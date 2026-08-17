"""CompileDB front end for mapping-independent E/R SPJG queries.

This module connects the existing CompileDB graph and conceptual-extent
generator to :mod:`er_query_rewriter`.  It deliberately leaves the existing
DDL/INSERT parser untouched: an E/R query is parsed into a typed, serializable
``QueryTemplate`` and is then compiled for the selected physical mapping.

Supported query shape::

    SELECT a.accessory_type AS accessory_type,
           COUNT(DISTINCT REF(ph)) AS price_count,
           MIN(ph.price) AS minimum_price
    FROM Accessory AS a
    JOIN PriceHistory AS ph ON OWNER(ph) = REF(a)
    WHERE a.is_active = 1 AND ph.price > 100
    GROUP BY REF(a), a.accessory_type
    HAVING COUNT(DISTINCT REF(ph)) >= 2;

Conceptual identity operators are explicit:

``REF(e)``
    Identity of an entity or weak entity.  Strong subclasses use the identity
    of the root entity in their inheritance hierarchy.

``OWNER(w)``
    Identity of the immediate owner of weak-entity binding ``w``.

``ENDPOINT(r, role)``
    Identity of one endpoint of relationship binding ``r``.  For a recursive
    relationship, ``role`` is one of ``recursive_relationship_roles``.  For a
    non-recursive relationship it is the participating entity name.

Every non-NULL literal is converted to a named parameter.  Consequently one
million queries that differ only in literal values share one canonical
``QueryTemplate`` and one compiled SQL template per physical mapping.

The default runtime catalog derives direct physical access branches from the
selected CompileDB mapping.  It lowers only the slots demanded by the current
AST, projects them before ``UNION ALL``, and activates ancestor joins only for
providers that need them.  Existing full conceptual-extent SQL remains a lazy
compatibility fallback for an object/query combination whose required slots
cannot yet be represented directly.  The emitted outer query never contains
``SELECT *``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Sequence

from pyparsing import (
    CaselessKeyword,
    Forward,
    Group,
    Literal as PPLiteral,
    MatchFirst,
    Optional,
    ParseException,
    ParserElement,
    QuotedString,
    Suppress,
    Word,
    ZeroOrMore,
    alphanums,
    alphas,
    delimitedList,
    oneOf,
    pyparsing_common,
)

from er_query_rewriter import (
    Apply,
    Attribute,
    BIGINT,
    BOOLEAN,
    Binding,
    CompiledQuery,
    EndpointReference,
    Expression,
    FromExpression,
    INTEGER,
    JoinSource,
    Literal,
    MappingCatalog,
    MappingError,
    OutputExpression,
    OwnerReference,
    ParameterDefinition,
    ParameterReference,
    PostgreSQLCompiler,
    QueryTemplate,
    QueryValidationError,
    Reference,
    RequiredSlot,
    ScanSource,
    SelectItem,
    SlotProvider,
    StaticMappingCatalog,
    TEXT,
    TypeInfo,
    AccessPlan,
    quote_identifier,
    template_fingerprint,
    validate_template,
)


# ---------------------------------------------------------------------------
# Public result objects
# ---------------------------------------------------------------------------


class ERQuerySyntaxError(ValueError):
    """The textual E/R query is syntactically invalid."""


class ERQueryBindingError(ValueError):
    """The query cannot be bound against the conceptual graph."""


@dataclass(frozen=True)
class PreparedERQuery:
    template: QueryTemplate
    arguments: Mapping[str, Any]


@dataclass(frozen=True)
class CompiledERQuery:
    compiled: CompiledQuery
    arguments: Mapping[str, Any]

    @property
    def sql(self) -> str:
        return self.compiled.sql


# ---------------------------------------------------------------------------
# Unbound parse tree
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Name:
    qualifier: str | None
    name: str


@dataclass(frozen=True)
class _Parameter:
    name: str


@dataclass(frozen=True)
class _Value:
    value: Any


@dataclass(frozen=True)
class _Reference:
    alias: str
    target: str | None = None


@dataclass(frozen=True)
class _Owner:
    alias: str


@dataclass(frozen=True)
class _Endpoint:
    alias: str
    role: str


@dataclass(frozen=True)
class _Call:
    name: str
    arguments: tuple[_RawExpression, ...]
    distinct: bool = False
    star: bool = False


@dataclass(frozen=True)
class _Operation:
    op: str
    arguments: tuple[_RawExpression, ...]


_RawExpression = (
    _Name
    | _Parameter
    | _Value
    | _Reference
    | _Owner
    | _Endpoint
    | _Call
    | _Operation
)


@dataclass(frozen=True)
class _Select:
    expression: _RawExpression
    alias: str | None


@dataclass(frozen=True)
class _ObjectSource:
    object_name: str
    alias: str


@dataclass(frozen=True)
class _Join:
    join_type: str
    source: _ObjectSource
    condition: _RawExpression | None


@dataclass(frozen=True)
class _ParsedQuery:
    distinct: bool
    first_source: _ObjectSource
    joins: tuple[_Join, ...]
    select: tuple[_Select, ...]
    where: _RawExpression | None
    group_by: tuple[_RawExpression, ...]
    having: _RawExpression | None


# ---------------------------------------------------------------------------
# SQL-like E/R query grammar
# ---------------------------------------------------------------------------


ParserElement.enablePackrat()

_RESERVED = (
    "SELECT", "DISTINCT", "FROM", "AS", "JOIN", "INNER", "LEFT", "RIGHT",
    "FULL", "CROSS", "ON", "WHERE", "GROUP", "BY", "HAVING", "AND", "OR",
    "NOT", "IS", "NULL", "IN", "TRUE", "FALSE",
)
_RESERVED_MATCH = MatchFirst([CaselessKeyword(word) for word in _RESERVED])
_IDENTIFIER = (~_RESERVED_MATCH + Word(alphas + "_", alphanums + "_$")).setName(
    "identifier"
)


def _fold_binary(tokens: Any, operator_map: Mapping[str, str]) -> _RawExpression:
    values = list(tokens)
    result: _RawExpression = values[0]
    for index in range(1, len(values), 2):
        token = str(values[index]).lower()
        result = _Operation(operator_map[token], (result, values[index + 1]))
    return result


def _query_grammar() -> ParserElement:
    expression = Forward()

    qualified_name = (
        _IDENTIFIER.copy() + Suppress(".") + _IDENTIFIER.copy()
    ).setParseAction(lambda t: _Name(str(t[0]), str(t[1])))
    unqualified_name = _IDENTIFIER.copy().setParseAction(
        lambda t: _Name(None, str(t[0]))
    )

    parameter = (Suppress(":") + _IDENTIFIER.copy()).setParseAction(
        lambda t: _Parameter(str(t[0]))
    )
    string_value = QuotedString("'", escQuote="''", unquoteResults=True).setParseAction(
        lambda t: _Value(str(t[0]))
    )
    number_value = pyparsing_common.number().setParseAction(
        lambda t: _Value(t[0])
    )
    true_value = CaselessKeyword("TRUE").setParseAction(lambda: _Value(True))
    false_value = CaselessKeyword("FALSE").setParseAction(lambda: _Value(False))
    null_value = CaselessKeyword("NULL").setParseAction(lambda: _Value(None))

    ref_call = (
        CaselessKeyword("REF").suppress()
        + Suppress("(")
        + _IDENTIFIER.copy()
        + Optional(Suppress(",") + _IDENTIFIER.copy())
        + Suppress(")")
    ).setParseAction(
        lambda t: _Reference(str(t[0]), str(t[1]) if len(t) > 1 else None)
    )
    owner_call = (
        CaselessKeyword("OWNER").suppress()
        + Suppress("(")
        + _IDENTIFIER.copy()
        + Suppress(")")
    ).setParseAction(lambda t: _Owner(str(t[0])))
    endpoint_call = (
        CaselessKeyword("ENDPOINT").suppress()
        + Suppress("(")
        + _IDENTIFIER.copy()
        + Suppress(",")
        + _IDENTIFIER.copy()
        + Suppress(")")
    ).setParseAction(lambda t: _Endpoint(str(t[0]), str(t[1])))

    function_call = Forward()
    atom = Forward()
    function_call <<= (
        _IDENTIFIER.copy()
        + Suppress("(")
        + Optional(CaselessKeyword("DISTINCT")("distinct"))
        + (
            PPLiteral("*")("star")
            | Optional(Group(delimitedList(expression))("arguments"))
        )
        + Suppress(")")
    ).setParseAction(
        lambda t: _Call(
            name=str(t[0]),
            arguments=tuple(t.arguments) if "arguments" in t else (),
            distinct="distinct" in t,
            star="star" in t,
        )
    )

    parenthesized = Suppress("(") + expression + Suppress(")")
    atom <<= (
        ref_call
        | owner_call
        | endpoint_call
        | function_call
        | parameter
        | string_value
        | number_value
        | true_value
        | false_value
        | null_value
        | qualified_name
        | unqualified_name
        | parenthesized
    )

    unary = Forward()
    unary <<= (
        (PPLiteral("-").suppress() + unary).setParseAction(
            lambda t: _Operation("negate", (t[0],))
        )
        | atom
    )
    product = (unary + ZeroOrMore(oneOf("* /") + unary)).setParseAction(
        lambda t: _fold_binary(t, {"*": "mul", "/": "div"})
    )
    arithmetic = (product + ZeroOrMore(oneOf("+ -") + product)).setParseAction(
        lambda t: _fold_binary(t, {"+": "add", "-": "sub"})
    )

    comparison_operator = oneOf("= != <> < <= > >=")
    is_null_tail = Group(
        CaselessKeyword("IS") + Optional(CaselessKeyword("NOT")) + CaselessKeyword("NULL")
    )
    in_tail = Group(
        Optional(CaselessKeyword("NOT"))
        + CaselessKeyword("IN")
        + Suppress("(")
        + Group(delimitedList(expression))
        + Suppress(")")
    )

    def comparison_action(tokens: Any) -> _RawExpression:
        values = list(tokens)
        if len(values) == 1:
            return values[0]
        left = values[0]
        tail = values[1]
        if isinstance(tail, str):
            op = {
                "=": "eq", "!=": "ne", "<>": "ne", "<": "lt",
                "<=": "lte", ">": "gt", ">=": "gte",
            }[tail]
            return _Operation(op, (left, values[2]))
        tail_values = [str(value).upper() if isinstance(value, str) else value for value in tail]
        if tail_values[0] == "IS":
            return _Operation(
                "is_not_null" if "NOT" in tail_values else "is_null",
                (left,),
            )
        negated = tail_values[0] == "NOT"
        candidates = tail[-1]
        operation = _Operation("in", (left, *tuple(candidates)))
        return _Operation("not", (operation,)) if negated else operation

    comparison = (
        arithmetic
        + Optional(
            (comparison_operator + arithmetic)
            | is_null_tail
            | in_tail
        )
    ).setParseAction(comparison_action)

    negation = Forward()
    negation <<= (
        (CaselessKeyword("NOT").suppress() + negation).setParseAction(
            lambda t: _Operation("not", (t[0],))
        )
        | comparison
    )
    conjunction = (
        negation + ZeroOrMore(CaselessKeyword("AND").suppress() + negation)
    ).setParseAction(
        lambda t: t[0] if len(t) == 1 else _Operation("and", tuple(t))
    )
    disjunction = (
        conjunction + ZeroOrMore(CaselessKeyword("OR").suppress() + conjunction)
    ).setParseAction(
        lambda t: t[0] if len(t) == 1 else _Operation("or", tuple(t))
    )
    expression <<= disjunction

    select_item = (
        expression + Optional(CaselessKeyword("AS").suppress() + _IDENTIFIER.copy())
    ).setParseAction(
        lambda t: _Select(t[0], str(t[1]) if len(t) > 1 else None)
    )

    object_source = (
        _IDENTIFIER.copy()
        + Optional(
            (CaselessKeyword("AS").suppress() + _IDENTIFIER.copy())
            | _IDENTIFIER.copy()
        )
    ).setParseAction(
        lambda t: _ObjectSource(str(t[0]), str(t[1]) if len(t) > 1 else str(t[0]))
    )

    join_type = Optional(
        MatchFirst(
            [CaselessKeyword(value) for value in ("INNER", "LEFT", "RIGHT", "FULL", "CROSS")]
        ),
        default="INNER",
    )

    def join_action(tokens: Any) -> _Join:
        values = list(tokens)
        kind = str(values[0]).lower()
        source = values[1]
        condition = values[2] if len(values) > 2 else None
        if kind == "cross" and condition is not None:
            raise ERQuerySyntaxError("CROSS JOIN cannot have an ON condition")
        return _Join(kind, source, condition)

    join = (
        join_type
        + CaselessKeyword("JOIN").suppress()
        + object_source
        + Optional(CaselessKeyword("ON").suppress() + expression)
    ).setParseAction(join_action)

    statement = (
        CaselessKeyword("SELECT").suppress()
        + Optional(CaselessKeyword("DISTINCT")("distinct"))
        + Group(delimitedList(select_item))("select_items")
        + CaselessKeyword("FROM").suppress()
        + object_source("first_source")
        + Group(ZeroOrMore(join))("joins")
        + Optional(CaselessKeyword("WHERE").suppress() + expression("where"))
        + Optional(
            CaselessKeyword("GROUP").suppress()
            + CaselessKeyword("BY").suppress()
            + Group(delimitedList(expression))("group_by")
        )
        + Optional(CaselessKeyword("HAVING").suppress() + expression("having"))
        + Optional(Suppress(";"))
    )

    def statement_action(tokens: Any) -> _ParsedQuery:
        first = tokens.first_source
        if hasattr(first, "asList"):
            first = first[0]
        where = tokens.where if "where" in tokens else None
        if hasattr(where, "asList"):
            where = where[0]
        having = tokens.having if "having" in tokens else None
        if hasattr(having, "asList"):
            having = having[0]
        return _ParsedQuery(
            distinct="distinct" in tokens,
            first_source=first,
            joins=tuple(tokens.joins),
            select=tuple(tokens.select_items),
            where=where,
            group_by=tuple(tokens.group_by) if "group_by" in tokens else (),
            having=having,
        )

    return statement.setParseAction(statement_action)


_QUERY_GRAMMAR = _query_grammar()


def parse_er_query(text: str) -> _ParsedQuery:
    """Parse an E/R SPJG query without consulting a physical mapping."""

    try:
        result = _QUERY_GRAMMAR.parse_string(text, parse_all=True)
    except ParseException as error:
        raise ERQuerySyntaxError(
            f"E/R query syntax error at line {error.lineno}, column {error.col}: "
            f"{error.msg}"
        ) from error
    except ERQuerySyntaxError:
        raise
    parsed = result[0]
    if not isinstance(parsed, _ParsedQuery):
        raise ERQuerySyntaxError("Parser did not produce an E/R query")
    return parsed


# ---------------------------------------------------------------------------
# Conceptual graph binding and literal parameterization
# ---------------------------------------------------------------------------


def _node_index(graph: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for node in graph.nodes:
        if not (node.is_entity() or node.is_relationship()):
            continue
        for key in {str(node.name).lower(), str(node.unique_name).lower()}:
            previous = result.get(key)
            if previous is not None and previous is not node:
                raise ERQueryBindingError(f"Ambiguous conceptual object name {key!r}")
            result[key] = node
    return result


def _attribute_nodes(node: Any) -> tuple[Any, ...]:
    result: list[Any] = []
    if node.is_entity():
        parents: list[Any] = []
        current = node
        while current is not None:
            parents.append(current)
            current = (
                getattr(current, "parent_entity", None)
                if (
                    getattr(current, "is_subclass", False)
                    or getattr(current, "is_weak_entity", False)
                )
                else None
            )
        for parent in reversed(parents):
            result.extend(parent.attributes)
    else:
        result.extend(node.attributes)

    def add_children(attribute: Any) -> None:
        for child in getattr(attribute, "children", None) or ():
            result.append(child)
            add_children(child)

    for attribute in tuple(result):
        add_children(attribute)
    unique_result: list[Any] = []
    seen_ids: set[int] = set()
    for attribute in result:
        if id(attribute) not in seen_ids:
            seen_ids.add(id(attribute))
            unique_result.append(attribute)
    return tuple(unique_result)


def _attribute_index(node: Any) -> dict[str, Any]:
    result: MutableMapping[str, list[Any]] = {}
    for attribute in _attribute_nodes(node):
        keys = {
            str(attribute.name).lower(),
            str(attribute.unique_name).lower(),
            str(attribute.unique_name).split(".", 1)[-1].lower(),
        }
        for key in keys:
            result.setdefault(key, []).append(attribute)
    final: dict[str, Any] = {}
    for key, values in result.items():
        unique_values: list[Any] = []
        seen_ids: set[int] = set()
        for value in values:
            if id(value) not in seen_ids:
                seen_ids.add(id(value))
                unique_values.append(value)
        if len(unique_values) == 1:
            final[key] = unique_values[0]
    return final


def _type_info(type_name: str | None, *, nullable: bool = True) -> TypeInfo:
    normalized = (type_name or "TEXT").upper()
    if normalized in {"INT", "INTEGER"}:
        return TypeInfo("INT", nullable)
    if normalized in {"BIGINT"}:
        return TypeInfo("BIGINT", nullable)
    if normalized in {"BOOL", "BOOLEAN"}:
        return TypeInfo("BOOLEAN", nullable)
    if normalized in {"VARCHAR", "VARCHAR(255)", "TEXT"}:
        return TypeInfo("TEXT", nullable)
    if normalized.endswith("[]"):
        return TypeInfo(normalized, nullable)
    return TypeInfo(normalized, nullable)


def _root_strong_entity(node: Any) -> Any:
    current = node
    while getattr(current, "is_subclass", False):
        current = current.parent_entity
    return current


def conceptual_schema_fingerprint(graph: Any) -> str:
    nodes: list[dict[str, Any]] = []
    for node in graph.nodes:
        if node.is_entity():
            nodes.append(
                {
                    "kind": "weak_entity" if getattr(node, "is_weak_entity", False) else "entity",
                    "id": node.unique_name,
                    "parent": getattr(getattr(node, "parent_entity", None), "unique_name", None),
                    "attributes": [
                        {
                            "id": attribute.unique_name,
                            "type": attribute.attr_type,
                            "pk": attribute.is_primary_key,
                            "discriminator": attribute.is_discriminator,
                            "mvd": attribute.is_multivalued,
                        }
                        for attribute in node.attributes
                    ],
                }
            )
        elif node.is_relationship():
            nodes.append(
                {
                    "kind": "relationship",
                    "id": node.unique_name,
                    "entity1": node.entity1.unique_name,
                    "entity2": node.entity2.unique_name,
                    "roles": getattr(node, "recursive_relationship_roles", None),
                    "attributes": [
                        {"id": attribute.unique_name, "type": attribute.attr_type}
                        for attribute in node.attributes
                    ],
                }
            )
    payload = json.dumps(nodes, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _walk_raw(expression: _RawExpression | None) -> Iterable[_RawExpression]:
    if expression is None:
        return
    yield expression
    if isinstance(expression, (_Operation, _Call)):
        for argument in expression.arguments:
            yield from _walk_raw(argument)


class _Binder:
    def __init__(self, parsed: _ParsedQuery, graph: Any):
        self.parsed = parsed
        self.graph = graph
        self.nodes = _node_index(graph)
        self.aliases: dict[str, tuple[Binding, Any]] = {}
        self.parameters: dict[str, ParameterDefinition] = {}
        self.arguments: dict[str, Any] = {}
        self._literal_counter = 0
        roots: list[_RawExpression | None] = [
            *(join.condition for join in parsed.joins),
            *(item.expression for item in parsed.select),
            parsed.where,
            *parsed.group_by,
            parsed.having,
        ]
        self._reserved_parameter_names = {
            node.name
            for root in roots
            for node in _walk_raw(root)
            if isinstance(node, _Parameter)
        }

    def bind(self) -> PreparedERQuery:
        sources = (self.parsed.first_source,) + tuple(join.source for join in self.parsed.joins)
        bindings: list[Binding] = []
        for index, source in enumerate(sources):
            try:
                node = self.nodes[source.object_name.lower()]
            except KeyError as error:
                raise ERQueryBindingError(
                    f"Unknown conceptual object {source.object_name!r}"
                ) from error
            alias_key = source.alias.lower()
            if alias_key in self.aliases:
                raise ERQueryBindingError(f"Duplicate query alias {source.alias!r}")
            kind = (
                "relationship"
                if node.is_relationship()
                else "weak_entity"
                if getattr(node, "is_weak_entity", False)
                else "entity"
            )
            binding = Binding(
                id=f"b{index}",
                kind=kind,
                object_id=node.unique_name,
                original_alias=source.alias,
            )
            self.aliases[alias_key] = (binding, node)
            bindings.append(binding)

        from_expression: FromExpression = ScanSource(bindings[0].id)
        for join in self.parsed.joins:
            right_binding, _ = self.aliases[join.source.alias.lower()]
            condition = self._bind_expression(join.condition) if join.condition is not None else None
            if join.join_type != "cross" and condition is None:
                raise ERQueryBindingError(
                    f"{join.join_type.upper()} JOIN {join.source.alias!r} requires ON"
                )
            from_expression = JoinSource(
                left=from_expression,
                right=ScanSource(right_binding.id),
                join_type=join.join_type,
                condition=condition,
            )

        select_items: list[SelectItem] = []
        for index, item in enumerate(self.parsed.select):
            expression = self._bind_expression(item.expression)
            alias = item.alias or self._default_alias(item.expression, index)
            select_items.append(SelectItem(f"o{index}", alias, expression))

        where = (
            self._bind_expression(self.parsed.where)
            if self.parsed.where is not None
            else None
        )
        group_by = tuple(
            self._bind_expression(expression)
            for expression in self.parsed.group_by
        )
        having = (
            self._bind_expression(self.parsed.having)
            if self.parsed.having is not None
            else None
        )

        template = QueryTemplate(
            format_version=1,
            schema_fingerprint=conceptual_schema_fingerprint(self.graph),
            bindings=tuple(bindings),
            parameters=tuple(self.parameters.values()),
            from_expression=from_expression,
            select=tuple(select_items),
            where=where,
            group_by=group_by,
            having=having,
            distinct=self.parsed.distinct,
        )
        validate_template(template)
        return PreparedERQuery(template, dict(self.arguments))

    def _binding(self, alias: str) -> tuple[Binding, Any]:
        try:
            return self.aliases[alias.lower()]
        except KeyError as error:
            raise ERQueryBindingError(f"Unknown query alias {alias!r}") from error

    def _resolve_attribute(self, raw: _Name) -> tuple[Binding, Any, Any]:
        if raw.qualifier is not None:
            binding, node = self._binding(raw.qualifier)
            attribute = _attribute_index(node).get(raw.name.lower())
            if attribute is None:
                raise ERQueryBindingError(
                    f"{raw.name!r} is not an attribute of {node.name!r}"
                )
            return binding, node, attribute

        matches: list[tuple[Binding, Any, Any]] = []
        for binding, node in self.aliases.values():
            attribute = _attribute_index(node).get(raw.name.lower())
            if attribute is not None:
                matches.append((binding, node, attribute))
        if not matches:
            raise ERQueryBindingError(f"Unknown attribute {raw.name!r}")
        if len(matches) > 1:
            raise ERQueryBindingError(
                f"Ambiguous attribute {raw.name!r}; qualify it with a query alias"
            )
        return matches[0]

    def _new_parameter(self, value: Any, type_info: TypeInfo, original: str | None = None) -> ParameterReference:
        if original is None:
            while True:
                parameter_id = f"p{self._literal_counter}"
                self._literal_counter += 1
                if parameter_id not in self._reserved_parameter_names:
                    break
        else:
            parameter_id = original
        previous = self.parameters.get(parameter_id)
        definition = ParameterDefinition(parameter_id, type_info, original)
        if previous is not None and previous.type.name != type_info.name:
            raise ERQueryBindingError(
                f"Parameter {parameter_id!r} is used with incompatible types "
                f"{previous.type.name} and {type_info.name}"
            )
        self.parameters.setdefault(parameter_id, definition)
        if original is None:
            self.arguments[parameter_id] = value
        return ParameterReference(parameter_id, type_info)

    def _literal_type(self, value: Any, expected: TypeInfo | None) -> TypeInfo:
        if expected is not None:
            return expected
        if isinstance(value, bool):
            return BOOLEAN
        if isinstance(value, int):
            return INTEGER
        if isinstance(value, float):
            return TypeInfo("DOUBLE PRECISION")
        return TEXT

    def _bind_expression(
        self,
        raw: _RawExpression | None,
        expected: TypeInfo | None = None,
    ) -> Expression:
        if raw is None:
            raise ERQueryBindingError("Missing expression")
        if isinstance(raw, _Name):
            binding, node, attribute = self._resolve_attribute(raw)
            return Attribute(
                binding=binding.id,
                attribute_id=attribute.unique_name,
                type=_type_info(attribute.attr_type),
                accessed_through=node.unique_name,
            )
        if isinstance(raw, _Value):
            if raw.value is None:
                return Literal(None, expected or TEXT)
            type_info = self._literal_type(raw.value, expected)
            return self._new_parameter(raw.value, type_info)
        if isinstance(raw, _Parameter):
            return self._new_parameter(None, expected or TEXT, raw.name)
        if isinstance(raw, _Reference):
            binding, node = self._binding(raw.alias)
            if node.is_relationship():
                raise ERQueryBindingError("REF cannot be applied to a relationship")
            if getattr(node, "is_weak_entity", False):
                target = node.unique_name
            else:
                root = _root_strong_entity(node)
                target = root.unique_name
                if raw.target is not None:
                    requested = self.nodes.get(raw.target.lower())
                    if requested is None or requested.is_relationship():
                        raise ERQueryBindingError(
                            f"Unknown REF target entity {raw.target!r}"
                        )
                    if _root_strong_entity(requested) is not root:
                        raise ERQueryBindingError(
                            f"{raw.target!r} is not in the identity hierarchy of {node.name!r}"
                        )
                    target = _root_strong_entity(requested).unique_name
            return Reference(binding.id, target)
        if isinstance(raw, _Owner):
            binding, node = self._binding(raw.alias)
            if not (node.is_entity() and getattr(node, "is_weak_entity", False)):
                raise ERQueryBindingError("OWNER requires a weak-entity binding")
            owner = node.parent_entity
            reference_type = (
                owner.unique_name
                if getattr(owner, "is_weak_entity", False)
                else _root_strong_entity(owner).unique_name
            )
            return OwnerReference(binding.id, reference_type)
        if isinstance(raw, _Endpoint):
            binding, node = self._binding(raw.alias)
            if not node.is_relationship():
                raise ERQueryBindingError("ENDPOINT requires a relationship binding")
            return EndpointReference(
                binding.id,
                _canonical_endpoint_role(node, raw.role),
                _endpoint_reference_type(node, raw.role),
            )
        if isinstance(raw, _Call):
            name = raw.name.upper()
            aggregates = {"COUNT", "SUM", "MIN", "MAX", "AVG"}
            if name in aggregates:
                if raw.star:
                    if name != "COUNT" or raw.distinct:
                        raise ERQueryBindingError("Only COUNT(*) is valid")
                    arguments: tuple[Expression, ...] = ()
                else:
                    if len(raw.arguments) != 1:
                        raise ERQueryBindingError(f"{name} expects one argument")
                    arguments = (self._bind_expression(raw.arguments[0]),)
                result_type = BIGINT if name == "COUNT" else (
                    arguments[0].type if hasattr(arguments[0], "type") else TypeInfo("NUMERIC")
                )
                return Apply("aggregate", arguments, result_type, name, raw.distinct)
            if raw.star or raw.distinct:
                raise ERQueryBindingError(
                    "Star and DISTINCT are supported only for aggregate calls"
                )
            arguments = tuple(self._bind_expression(argument) for argument in raw.arguments)
            return Apply("function", arguments, expected or TEXT, raw.name)
        if not isinstance(raw, _Operation):
            raise ERQueryBindingError(f"Unsupported expression {raw!r}")

        op = raw.op
        if op in {"eq", "ne", "lt", "lte", "gt", "gte"}:
            left_raw, right_raw = raw.arguments
            if isinstance(left_raw, (_Value, _Parameter)) and not isinstance(right_raw, (_Value, _Parameter)):
                right = self._bind_expression(right_raw)
                left = self._bind_expression(left_raw, getattr(right, "type", None))
            else:
                left = self._bind_expression(left_raw)
                right = self._bind_expression(right_raw, getattr(left, "type", None))
            return Apply(op, (left, right), BOOLEAN)
        if op in {"and", "or"}:
            return Apply(op, tuple(self._bind_expression(arg, BOOLEAN) for arg in raw.arguments), BOOLEAN)
        if op == "not":
            return Apply("not", (self._bind_expression(raw.arguments[0], BOOLEAN),), BOOLEAN)
        if op in {"is_null", "is_not_null"}:
            return Apply(op, (self._bind_expression(raw.arguments[0]),), BOOLEAN)
        if op == "in":
            value = self._bind_expression(raw.arguments[0])
            candidates = tuple(
                self._bind_expression(argument, getattr(value, "type", None))
                for argument in raw.arguments[1:]
            )
            return Apply("in", (value, *candidates), BOOLEAN)
        if op == "negate":
            value = self._bind_expression(raw.arguments[0])
            zero = self._new_parameter(0, getattr(value, "type", INTEGER))
            return Apply("sub", (zero, value), getattr(value, "type", INTEGER))
        if op in {"add", "sub", "mul", "div"}:
            left = self._bind_expression(raw.arguments[0])
            right = self._bind_expression(raw.arguments[1], getattr(left, "type", None))
            return Apply(op, (left, right), getattr(left, "type", TypeInfo("NUMERIC")))
        raise ERQueryBindingError(f"Unsupported expression operation {op!r}")

    @staticmethod
    def _default_alias(expression: _RawExpression, index: int) -> str:
        if isinstance(expression, _Name):
            return expression.name
        if isinstance(expression, _Call):
            return expression.name.lower()
        if isinstance(expression, _Reference):
            return f"{expression.alias}_id"
        if isinstance(expression, _Owner):
            return f"{expression.alias}_owner_id"
        if isinstance(expression, _Endpoint):
            return f"{expression.alias}_{expression.role}_id"
        return f"column_{index + 1}"


def prepare_er_query(text: str, graph: Any) -> PreparedERQuery:
    """Parse, bind, type-check, parameterize, and canonicalize one E/R query."""

    return _Binder(parse_er_query(text), graph).bind()


# ---------------------------------------------------------------------------
# Adapter over the existing conceptual-extent SQL generator
# ---------------------------------------------------------------------------


def _flatten_key_groups(value: Any) -> tuple[tuple[Any, ...], ...]:
    if value is None:
        return ()
    if value and isinstance(value[0], tuple):
        return (tuple(value),)
    return tuple(tuple(group) for group in value)


def _canonical_endpoint_role(relationship: Any, requested_role: str) -> str:
    requested = requested_role.lower()
    if relationship.entity1 == relationship.entity2:
        roles = tuple(role.lower() for role in (relationship.recursive_relationship_roles or ()))
        for role in roles:
            if requested in {role, role.removesuffix("_id")}:
                return role
        raise ERQueryBindingError(
            f"Unknown role {requested_role!r} for recursive relationship "
            f"{relationship.name!r}; expected one of {roles}"
        )
    candidates = (
        (relationship.entity1, relationship.rel_dict["entity1"].get("role")),
        (relationship.entity2, relationship.rel_dict["entity2"].get("role")),
    )
    for entity, role in candidates:
        names = {entity.unique_name.lower(), entity.name.lower()}
        if role:
            names.update({role.lower(), role.lower().removesuffix("_id")})
        if requested in names:
            return entity.unique_name
    raise ERQueryBindingError(
        f"Unknown endpoint {requested_role!r} for relationship {relationship.name!r}"
    )


def _endpoint_index(relationship: Any, requested_role: str) -> int:
    canonical = _canonical_endpoint_role(relationship, requested_role)
    groups = _flatten_key_groups(relationship.key.table_key)
    if relationship.entity1 == relationship.entity2:
        role1, role2 = tuple(role.lower() for role in relationship.recursive_relationship_roles)
        # define_node_keys_for_relationship reverses the groups for ONE:MANY
        # when entity1 is the one side.  Preserve that physical ordering here.
        if relationship.rel_dict["entity1"]["one"] and not relationship.rel_dict["entity2"]["one"]:
            group_roles = (role2, role1)
        else:
            group_roles = (role1, role2)
        try:
            return group_roles.index(canonical)
        except ValueError as error:
            raise MappingError(
                f"Cannot map recursive role {canonical!r} to a key group"
            ) from error

    entity_groups = relationship.key.table_key_entities
    for index, entity_group in enumerate(entity_groups):
        entity_name = entity_group[0] if isinstance(entity_group, (list, tuple)) else entity_group
        if str(entity_name).lower() == canonical:
            return index
    # Older serialized graphs may omit table_key_entities.  The key builder's
    # nonrecursive order is still deterministic.
    if canonical == relationship.entity1.unique_name:
        if relationship.rel_dict["entity1"]["one"] and not relationship.rel_dict["entity2"]["one"]:
            return 1
        return 0
    return 0 if relationship.rel_dict["entity2"]["one"] and not relationship.rel_dict["entity1"]["one"] else 1


def _endpoint_reference_type(relationship: Any, requested_role: str) -> str:
    canonical = _canonical_endpoint_role(relationship, requested_role)
    if relationship.entity1 == relationship.entity2:
        entity = relationship.entity1
    elif canonical == relationship.entity1.unique_name:
        entity = relationship.entity1
    else:
        entity = relationship.entity2
    return (
        entity.unique_name
        if getattr(entity, "is_weak_entity", False)
        else _root_strong_entity(entity).unique_name
    )


def _safe_output_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_") or "slot"


def _extent_column_name(attribute: Any) -> str:
    return str(attribute.unique_name).split(".", 1)[-1].replace(".", "__")


def _attribute_expression(extent_alias: str, attribute: Any) -> tuple[OutputExpression, ...]:
    parents: list[Any] = []
    current = attribute
    while getattr(current, "parent_attribute", None) is not None:
        parents.append(current)
        current = current.parent_attribute
    top = current

    if parents and not getattr(top, "is_flattened", False):
        sql = f"{quote_identifier(extent_alias)}.{quote_identifier(_extent_column_name(top))}"
        for child in reversed(parents):
            sql = f"({sql}).{quote_identifier(child.name)}"
        return (OutputExpression(_extent_column_name(attribute), sql),)

    if getattr(attribute, "is_composite", False) and getattr(attribute, "is_flattened", False):
        outputs: list[OutputExpression] = []
        for child in attribute.children:
            outputs.extend(_attribute_expression(extent_alias, child))
        return tuple(outputs)

    name = _extent_column_name(attribute)
    return (
        OutputExpression(
            name,
            f"{quote_identifier(extent_alias)}.{quote_identifier(name)}",
        ),
    )


def _mapping_fingerprint(graph: Any, tables: Sequence[Sequence[Any]]) -> str:
    payload = {
        "config": getattr(graph, "config", None),
        "tables": tables,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class CompileDBExtentCatalog(MappingCatalog):
    """Direct-first adapter with a full conceptual-extent fallback.

    The class name is retained for compatibility with existing callers. For a
    strong entity it first asks the selected physical mapping for providers of
    the slots required by the current AST. Only an unsupported object/slot
    combination reaches the legacy full-information extent generator.
    """

    def __init__(
        self,
        graph: Any,
        tables: Sequence[Sequence[Any]],
        types: Any,
        *,
        extent_sql_factory: Callable[[Any], str] | None = None,
        mapping_id: str | None = None,
    ):
        self.graph = graph
        self.tables = tables
        self.types = types
        self.mapping_id = mapping_id or _mapping_fingerprint(graph, tables)
        self._nodes = {
            node.unique_name.lower(): node
            for node in graph.nodes
            if node.is_entity() or node.is_relationship()
        }
        self._extent_sql_cache: dict[str, str] = {}
        self._direct_access_cache: dict[
            str,
            tuple[StaticMappingCatalog, frozenset[RequiredSlot]] | None,
        ] = {}

        if extent_sql_factory is None:
            from map_select_queries_all_attributes_extended_for_strict_all_by_itself import (
                generate_select_query_for_single_entity_or_relationship,
                init_memoized_attributes_and_select_all_queries,
                initialize_select_tables_for_single_entity_or_relationship,
            )

            init_memoized_attributes_and_select_all_queries()
            initialize_select_tables_for_single_entity_or_relationship(graph)

            def default_factory(node: Any) -> str:
                return generate_select_query_for_single_entity_or_relationship(
                    node, tables, types, graph
                )

            self._extent_sql_factory = default_factory
        else:
            self._extent_sql_factory = extent_sql_factory

    def _extent_sql(self, node: Any) -> str:
        if node.unique_name not in self._extent_sql_cache:
            sql = self._extent_sql_factory(node).strip().removesuffix(";")
            if re.search(r"\bSELECT\s+\*", sql, re.IGNORECASE):
                raise MappingError(
                    f"Extent SQL for {node.unique_name!r} contains SELECT *"
                )
            self._extent_sql_cache[node.unique_name] = sql
        return self._extent_sql_cache[node.unique_name]

    def resolve_access(
        self,
        binding: Binding,
        required_slots: frozenset[RequiredSlot],
    ) -> AccessPlan:
        try:
            node = self._nodes[binding.object_id.lower()]
        except KeyError as error:
            raise MappingError(f"No conceptual object {binding.object_id!r}") from error

        direct = self._direct_access(node)
        if direct is not None:
            direct_catalog, supported_slots = direct
            if required_slots.issubset(supported_slots):
                return direct_catalog.resolve_access(binding, required_slots)

        extent_alias = "extent"
        select_outputs: dict[str, str] = {}
        resolved: dict[RequiredSlot, tuple[str, ...]] = {}
        for slot in sorted(required_slots):
            provider = self._provider(node, slot, extent_alias)
            names: list[str] = []
            for output in provider.outputs:
                previous = select_outputs.get(output.name)
                if previous is not None and previous != output.sql:
                    raise MappingError(
                        f"Conflicting access expressions for {output.name!r}"
                    )
                select_outputs[output.name] = output.sql
                names.append(output.name)
            resolved[slot] = tuple(names)

        if not select_outputs:
            select_outputs["__present"] = "1"
        projection = ",\n    ".join(
            f"{sql} AS {quote_identifier(name)}"
            for name, sql in select_outputs.items()
        )
        sql = (
            f"SELECT\n    {projection}\n"
            f"FROM (\n{_indent(self._extent_sql(node), 4)}\n) AS {quote_identifier(extent_alias)}"
        )
        return AccessPlan(
            sql=sql,
            resolved_slots=resolved,
            output_unit=(
                "one_row_per_relationship"
                if node.is_relationship()
                else "one_row_per_weak_entity"
                if getattr(node, "is_weak_entity", False)
                else "one_row_per_entity"
            ),
            duplicate_free=True,
        )

    def _direct_access(
        self,
        node: Any,
    ) -> tuple[StaticMappingCatalog, frozenset[RequiredSlot]] | None:
        """Build and cache a partial direct mapping for one conceptual object."""
        cache_key = node.unique_name.lower()
        if cache_key in self._direct_access_cache:
            return self._direct_access_cache[cache_key]

        if not (node.is_entity() or node.is_relationship()):
            self._direct_access_cache[cache_key] = None
            return None

        # Lazy import avoids the adapter/catalog module cycle. The helper uses
        # only the selected graph and generated physical table metadata.
        from compiledb_mapping_catalog import (
            _direct_object_mapping,
            _object_mapping_specification,
        )

        mapping = _direct_object_mapping(
            node,
            self.graph,
            self.tables,
            require_complete=False,
        )
        if mapping is None:
            self._direct_access_cache[cache_key] = None
            return None

        specification = _object_mapping_specification(mapping)
        supported = set(specification.branches[0].providers)
        for branch in specification.branches[1:]:
            supported.intersection_update(branch.providers)
        if not supported:
            self._direct_access_cache[cache_key] = None
            return None

        result = (
            StaticMappingCatalog(self.mapping_id, (specification,)),
            frozenset(supported),
        )
        self._direct_access_cache[cache_key] = result
        return result

    def _provider(self, node: Any, slot: RequiredSlot, extent_alias: str) -> SlotProvider:
        if slot.kind == "attribute":
            attribute = next(
                (
                    candidate
                    for candidate in _attribute_nodes(node)
                    if candidate.unique_name.lower() == slot.id.lower()
                ),
                None,
            )
            if attribute is None:
                raise MappingError(
                    f"{node.unique_name!r} cannot provide attribute {slot.id!r}"
                )
            # CompileDB renames the physical key at some inheritance levels
            # (for example Product.product_id may be accessory_id in an
            # Accessory concrete table).  The conceptual primary-key attribute
            # still denotes that same identity component.
            if getattr(attribute, "is_primary_key", False) and node.is_entity():
                groups = _flatten_key_groups(node.key.table_key)
                if not groups or not groups[0]:
                    raise MappingError(
                        f"{node.unique_name!r} has no key component for {slot.id!r}"
                    )
                source_name = groups[0][0][0]
                return SlotProvider(
                    (
                        OutputExpression(
                            _extent_column_name(attribute),
                            f"{quote_identifier(extent_alias)}."
                            f"{quote_identifier(source_name)}",
                        ),
                    )
                )
            return SlotProvider(_attribute_expression(extent_alias, attribute))

        groups = _flatten_key_groups(node.key.table_key)
        if slot.kind == "reference":
            if node.is_relationship():
                raise MappingError("A relationship has no REF slot")
            components = tuple(component for group in groups for component in group)
            prefix = "reference"
        elif slot.kind == "owner_reference":
            if not getattr(node, "is_weak_entity", False) or len(groups) < 2:
                raise MappingError(f"{node.unique_name!r} has no weak owner")
            components = groups[0]
            prefix = "owner"
        elif slot.kind == "endpoint":
            if not node.is_relationship():
                raise MappingError(f"{node.unique_name!r} has no relationship endpoints")
            index = _endpoint_index(node, slot.id)
            try:
                components = groups[index]
            except IndexError as error:
                raise MappingError(
                    f"Endpoint {slot.id!r} has no physical key group"
                ) from error
            prefix = f"endpoint_{_safe_output_part(slot.id)}"
        else:
            raise MappingError(f"Unsupported required slot {slot}")

        outputs = tuple(
            OutputExpression(
                f"__{prefix}_{index}",
                f"{quote_identifier(extent_alias)}.{quote_identifier(component[0])}",
            )
            for index, component in enumerate(components)
        )
        if not outputs:
            raise MappingError(f"Empty identity layout for {node.unique_name!r}")
        return SlotProvider(outputs)


def _indent(value: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in value.splitlines())


def _default_mapping_catalog(
    graph: Any,
    tables: Sequence[Sequence[Any]],
    types: Any,
) -> MappingCatalog:
    """Build direct physical branches with legacy extents as safe fallbacks."""
    # Lazy import avoids a module cycle: catalog extraction reuses the binding
    # and provider helpers defined in this adapter.
    from compiledb_mapping_catalog import build_mapping_catalog

    return build_mapping_catalog(graph, tables, types)


def compile_compiledb_query(
    text: str,
    graph: Any,
    tables: Sequence[Sequence[Any]],
    types: Any,
    *,
    catalog: MappingCatalog | None = None,
) -> CompiledERQuery:
    """Compile one textual E/R query for one selected CompileDB mapping."""

    prepared = prepare_er_query(text, graph)
    effective_catalog = (
        catalog
        if catalog is not None
        else _default_mapping_catalog(graph, tables, types)
    )
    compiled = PostgreSQLCompiler(effective_catalog).compile(prepared.template)
    if re.search(r"\bSELECT\s+\*", compiled.sql, re.IGNORECASE):
        raise MappingError("Compiler invariant violated: emitted SQL contains SELECT *")
    return CompiledERQuery(compiled, prepared.arguments)


class CompileDBQueryEngine:
    """Reusable parse/bind/compile cache for one selected physical mapping.

    Literal values are not part of the template fingerprint.  Therefore the
    second and subsequent instances of the same query shape reuse the same
    compiled SQL while retaining their own execution arguments.
    """

    def __init__(
        self,
        graph: Any,
        tables: Sequence[Sequence[Any]],
        types: Any,
        *,
        catalog: MappingCatalog | None = None,
    ):
        self.graph = graph
        self.tables = tables
        self.types = types
        self.catalog = (
            catalog
            if catalog is not None
            else _default_mapping_catalog(graph, tables, types)
        )
        self._compiled: dict[str, CompiledQuery] = {}

    def prepare(self, text: str) -> PreparedERQuery:
        return prepare_er_query(text, self.graph)

    def compile(
        self,
        text: str,
        arguments: Mapping[str, Any] | None = None,
    ) -> CompiledERQuery:
        prepared = self.prepare(text)
        return self.compile_prepared(prepared, arguments)

    def compile_template(self, template: QueryTemplate) -> CompiledQuery:
        """Compile an already saved canonical template for this mapping."""

        expected_schema = conceptual_schema_fingerprint(self.graph)
        if template.schema_fingerprint != expected_schema:
            raise ERQueryBindingError(
                "Query template belongs to a different conceptual schema"
            )
        fingerprint = template_fingerprint(template)
        compiled = self._compiled.get(fingerprint)
        if compiled is None:
            compiled = PostgreSQLCompiler(self.catalog).compile(template)
            if re.search(r"\bSELECT\s+\*", compiled.sql, re.IGNORECASE):
                raise MappingError(
                    "Compiler invariant violated: emitted SQL contains SELECT *"
                )
            self._compiled[fingerprint] = compiled
        return compiled

    def compile_prepared(
        self,
        prepared: PreparedERQuery,
        arguments: Mapping[str, Any] | None = None,
    ) -> CompiledERQuery:
        """Compile a parse-once template and attach this instance's values."""

        compiled = self.compile_template(prepared.template)

        effective_arguments = dict(prepared.arguments)
        if arguments:
            effective_arguments.update(arguments)
        expected = {parameter.id for parameter in compiled.parameters}
        unexpected = set(effective_arguments) - expected
        if unexpected:
            raise ERQueryBindingError(
                f"Values supplied for unknown parameters {sorted(unexpected)}"
            )
        return CompiledERQuery(compiled, effective_arguments)

    @property
    def compiled_template_count(self) -> int:
        return len(self._compiled)


__all__ = [
    "CompiledERQuery",
    "CompileDBQueryEngine",
    "CompileDBExtentCatalog",
    "ERQueryBindingError",
    "ERQuerySyntaxError",
    "PreparedERQuery",
    "compile_compiledb_query",
    "conceptual_schema_fingerprint",
    "parse_er_query",
    "prepare_er_query",
]
