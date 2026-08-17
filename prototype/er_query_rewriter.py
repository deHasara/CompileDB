"""Mapping-independent E/R SPJG query compiler.

This module provides the complete middle and back end of an E/R-to-relational
query rewriter:

* a typed, serializable E/R query-template IR;
* validation and parameterized-template fingerprinting;
* required-slot (demand) analysis;
* a declarative physical access-plan catalog;
* exact-column relational access-plan generation (never SELECT *);
* PostgreSQL SQL generation for selection, projection, joins, grouping,
  aggregates, and HAVING;
* utilities for normalizing the physical schemas and Key objects produced by
  the existing er_graph/construct_create_statements implementation; and
* an optional SQLite template/compiled-query cache.

The only project-specific front-end step is translating the application's
existing parsed E/R plan into QueryTemplate.  The compiler deliberately does
not parse a textual E/R language because that grammar is not part of the
attached implementation.

Run ``python er_query_rewriter.py --self-test`` for executable examples.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, fields, is_dataclass, replace
import argparse
import hashlib
import json
import math
import re
import sqlite3
from typing import Any, Iterable, Mapping, MutableMapping, Protocol, Sequence


# ---------------------------------------------------------------------------
# Conceptual query IR
# ---------------------------------------------------------------------------


@dataclass(frozen=True, order=True)
class TypeInfo:
    name: str
    nullable: bool = False


BOOLEAN = TypeInfo("BOOLEAN")
INTEGER = TypeInfo("INT")
BIGINT = TypeInfo("BIGINT")
TEXT = TypeInfo("TEXT", nullable=True)


@dataclass(frozen=True)
class ParameterDefinition:
    id: str
    type: TypeInfo
    original_name: str | None = None


@dataclass(frozen=True)
class Binding:
    """One occurrence of a conceptual object in a query.

    Two appearances of Phone must have two bindings even though object_id is
    identical.  Supported kinds are entity, weak_entity, and relationship.
    """

    id: str
    kind: str
    object_id: str
    original_alias: str | None = None
    polymorphic: bool = True


@dataclass(frozen=True)
class Attribute:
    binding: str
    attribute_id: str
    type: TypeInfo
    accessed_through: str | None = None


@dataclass(frozen=True)
class Reference:
    binding: str
    reference_type: str


@dataclass(frozen=True)
class OwnerReference:
    binding: str
    reference_type: str


@dataclass(frozen=True)
class EndpointReference:
    binding: str
    role_id: str
    reference_type: str


@dataclass(frozen=True)
class ParameterReference:
    parameter_id: str
    type: TypeInfo


@dataclass(frozen=True)
class Literal:
    value: Any
    type: TypeInfo


@dataclass(frozen=True)
class Apply:
    """A scalar, Boolean, function, or aggregate expression.

    Common op values are eq, ne, lt, lte, gt, gte, and, or, not, is_null,
    is_not_null, add, sub, mul, div, in, function, and aggregate.
    """

    op: str
    arguments: tuple[Expression, ...]
    type: TypeInfo
    function: str | None = None
    distinct: bool = False


Expression = (
    Attribute
    | Reference
    | OwnerReference
    | EndpointReference
    | ParameterReference
    | Literal
    | Apply
)


@dataclass(frozen=True)
class ScanSource:
    binding: str


@dataclass(frozen=True)
class JoinSource:
    left: FromExpression
    right: FromExpression
    join_type: str
    condition: Expression | None


FromExpression = ScanSource | JoinSource


@dataclass(frozen=True)
class SelectItem:
    output_id: str
    alias: str
    expression: Expression


@dataclass(frozen=True)
class QueryTemplate:
    format_version: int
    schema_fingerprint: str
    bindings: tuple[Binding, ...]
    parameters: tuple[ParameterDefinition, ...]
    from_expression: FromExpression
    select: tuple[SelectItem, ...]
    where: Expression | None = None
    group_by: tuple[Expression, ...] = ()
    having: Expression | None = None
    distinct: bool = False
    row_semantics: str = "bag"
    null_semantics: str = "sql"


# Small expression constructors.  They keep front-end adapters readable.


def binary(op: str, left: Expression, right: Expression, result: TypeInfo) -> Apply:
    return Apply(op=op, arguments=(left, right), type=result)


def eq(left: Expression, right: Expression) -> Apply:
    return binary("eq", left, right, BOOLEAN)


def ne(left: Expression, right: Expression) -> Apply:
    return binary("ne", left, right, BOOLEAN)


def gt(left: Expression, right: Expression) -> Apply:
    return binary("gt", left, right, BOOLEAN)


def gte(left: Expression, right: Expression) -> Apply:
    return binary("gte", left, right, BOOLEAN)


def lt(left: Expression, right: Expression) -> Apply:
    return binary("lt", left, right, BOOLEAN)


def lte(left: Expression, right: Expression) -> Apply:
    return binary("lte", left, right, BOOLEAN)


def and_(*arguments: Expression) -> Apply:
    return Apply("and", tuple(arguments), BOOLEAN)


def or_(*arguments: Expression) -> Apply:
    return Apply("or", tuple(arguments), BOOLEAN)


def not_(argument: Expression) -> Apply:
    return Apply("not", (argument,), BOOLEAN)


def aggregate(
    function: str,
    argument: Expression | None,
    result_type: TypeInfo,
    *,
    distinct: bool = False,
) -> Apply:
    arguments: tuple[Expression, ...] = () if argument is None else (argument,)
    return Apply(
        op="aggregate",
        arguments=arguments,
        type=result_type,
        function=function,
        distinct=distinct,
    )


# ---------------------------------------------------------------------------
# Query traversal and validation
# ---------------------------------------------------------------------------


class QueryValidationError(ValueError):
    pass


def walk_expression(expression: Expression | None) -> Iterable[Expression]:
    if expression is None:
        return
    yield expression
    if isinstance(expression, Apply):
        for argument in expression.arguments:
            yield from walk_expression(argument)


def walk_from_expression(
    source: FromExpression,
) -> Iterable[tuple[str, Expression | None]]:
    if isinstance(source, ScanSource):
        yield source.binding, None
        return
    yield from walk_from_expression(source.left)
    yield from walk_from_expression(source.right)
    yield "", source.condition


def query_expression_roots(template: QueryTemplate) -> Iterable[Expression]:
    for _, condition in walk_from_expression(template.from_expression):
        if condition is not None:
            yield condition
    if template.where is not None:
        yield template.where
    yield from template.group_by
    if template.having is not None:
        yield template.having
    for item in template.select:
        yield item.expression


def contains_aggregate(expression: Expression) -> bool:
    return any(
        isinstance(node, Apply) and node.op == "aggregate"
        for node in walk_expression(expression)
    )


def expression_bindings(expression: Expression) -> frozenset[str]:
    result: set[str] = set()
    for node in walk_expression(expression):
        if isinstance(
            node,
            (Attribute, Reference, OwnerReference, EndpointReference),
        ):
            result.add(node.binding)
    return frozenset(result)


def _validate_no_aggregate(expression: Expression | None, location: str) -> None:
    if expression is not None and contains_aggregate(expression):
        raise QueryValidationError(f"Aggregate is not legal in {location}")


def _validate_from_scopes(
    source: FromExpression,
    known_bindings: Mapping[str, Binding],
) -> frozenset[str]:
    """Validate SQL visibility rules for every JOIN condition."""

    if isinstance(source, ScanSource):
        if source.binding not in known_bindings:
            raise QueryValidationError(
                f"FROM references unknown binding {source.binding!r}"
            )
        return frozenset((source.binding,))

    left_scope = _validate_from_scopes(source.left, known_bindings)
    right_scope = _validate_from_scopes(source.right, known_bindings)
    scope = left_scope | right_scope
    join_type = source.join_type.lower()
    if join_type not in {"inner", "left", "right", "full", "cross"}:
        raise QueryValidationError(f"Unsupported join type {source.join_type!r}")
    if join_type == "cross":
        if source.condition is not None:
            raise QueryValidationError("CROSS JOIN cannot have an ON condition")
    else:
        if source.condition is None:
            raise QueryValidationError(f"{join_type.upper()} JOIN requires ON")
        dependencies = expression_bindings(source.condition)
        if not dependencies.issubset(scope):
            raise QueryValidationError(
                "JOIN condition references a binding outside its left/right scope: "
                f"{sorted(dependencies - scope)}"
            )
    return scope


def validate_template(template: QueryTemplate) -> None:
    if template.format_version != 1:
        raise QueryValidationError(
            f"Unsupported query-template version {template.format_version}"
        )
    if template.row_semantics not in {"bag", "set"}:
        raise QueryValidationError("row_semantics must be 'bag' or 'set'")
    if template.null_semantics != "sql":
        raise QueryValidationError("Only SQL null semantics are supported")

    bindings = {binding.id: binding for binding in template.bindings}
    parameters = {parameter.id: parameter for parameter in template.parameters}
    if len(bindings) != len(template.bindings):
        raise QueryValidationError("Duplicate binding IDs")
    if len(parameters) != len(template.parameters):
        raise QueryValidationError("Duplicate parameter IDs")
    if not template.select:
        raise QueryValidationError("Projection must contain at least one item")

    _validate_from_scopes(template.from_expression, bindings)

    scan_ids = [
        binding_id
        for binding_id, condition in walk_from_expression(template.from_expression)
        if condition is None and binding_id
    ]
    if len(scan_ids) != len(set(scan_ids)):
        raise QueryValidationError("A binding appears more than once in FROM")
    if set(scan_ids) != set(bindings):
        missing = set(bindings) - set(scan_ids)
        extra = set(scan_ids) - set(bindings)
        raise QueryValidationError(
            f"FROM/binding mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )

    output_ids = [item.output_id for item in template.select]
    if len(output_ids) != len(set(output_ids)):
        raise QueryValidationError("Duplicate output IDs")

    for expression in query_expression_roots(template):
        for node in walk_expression(expression):
            if isinstance(
                node,
                (Attribute, Reference, OwnerReference, EndpointReference),
            ):
                if node.binding not in bindings:
                    raise QueryValidationError(
                        f"Expression references unknown binding {node.binding!r}"
                    )
            if isinstance(node, OwnerReference):
                if bindings[node.binding].kind != "weak_entity":
                    raise QueryValidationError(
                        f"OWNER applied to non-weak binding {node.binding!r}"
                    )
            if isinstance(node, EndpointReference):
                if bindings[node.binding].kind != "relationship":
                    raise QueryValidationError(
                        f"ENDPOINT applied to non-relationship binding "
                        f"{node.binding!r}"
                    )
            if isinstance(node, ParameterReference):
                if node.parameter_id not in parameters:
                    raise QueryValidationError(
                        f"Unknown parameter {node.parameter_id!r}"
                    )
            if isinstance(node, Apply) and node.op == "aggregate":
                for argument in node.arguments:
                    if contains_aggregate(argument):
                        raise QueryValidationError("Nested aggregates are not supported")

    for _, condition in walk_from_expression(template.from_expression):
        _validate_no_aggregate(condition, "JOIN ON")
    _validate_no_aggregate(template.where, "WHERE")
    for expression in template.group_by:
        _validate_no_aggregate(expression, "GROUP BY")

    grouped_reference_bindings = {
        expression.binding
        for expression in template.group_by
        if isinstance(expression, Reference)
    }
    grouping_present = bool(template.group_by) or any(
        contains_aggregate(item.expression) for item in template.select
    ) or (template.having is not None and contains_aggregate(template.having))

    if grouping_present:
        group_set = set(template.group_by)
        for item in template.select:
            expression = item.expression
            if contains_aggregate(expression):
                continue
            if expression in group_set:
                continue
            dependencies = expression_bindings(expression)
            if dependencies and not dependencies.issubset(grouped_reference_bindings):
                raise QueryValidationError(
                    f"Nonaggregate projection {item.alias!r} is neither grouped nor "
                    "functionally dependent on a grouped entity reference"
                )


# ---------------------------------------------------------------------------
# Canonical JSON, fingerprints, and persistent cache
# ---------------------------------------------------------------------------


_SERIALIZABLE_TYPES = (
    TypeInfo,
    ParameterDefinition,
    Binding,
    Attribute,
    Reference,
    OwnerReference,
    EndpointReference,
    ParameterReference,
    Literal,
    Apply,
    ScanSource,
    JoinSource,
    SelectItem,
    QueryTemplate,
)
_TYPE_REGISTRY = {cls.__name__: cls for cls in _SERIALIZABLE_TYPES}


def encode_ir(value: Any) -> Any:
    if is_dataclass(value):
        result = {"$type": type(value).__name__}
        for field in fields(value):
            result[field.name] = encode_ir(getattr(value, field.name))
        return result
    if isinstance(value, tuple):
        return [encode_ir(element) for element in value]
    if isinstance(value, list):
        return [encode_ir(element) for element in value]
    if isinstance(value, dict):
        return {str(key): encode_ir(element) for key, element in value.items()}
    return value


def decode_ir(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(decode_ir(element) for element in value)
    if not isinstance(value, dict):
        return value
    if "$type" not in value:
        return {key: decode_ir(element) for key, element in value.items()}
    type_name = value["$type"]
    try:
        cls = _TYPE_REGISTRY[type_name]
    except KeyError as error:
        raise QueryValidationError(f"Unknown serialized IR type {type_name!r}") from error
    arguments = {
        key: decode_ir(element)
        for key, element in value.items()
        if key != "$type"
    }
    return cls(**arguments)


def template_to_json(template: QueryTemplate, *, indent: int | None = None) -> str:
    validate_template(template)
    return json.dumps(
        encode_ir(template),
        sort_keys=True,
        separators=(",", ":") if indent is None else None,
        ensure_ascii=False,
        indent=indent,
    )


def template_from_json(payload: str) -> QueryTemplate:
    result = decode_ir(json.loads(payload))
    if not isinstance(result, QueryTemplate):
        raise QueryValidationError("JSON payload is not a QueryTemplate")
    validate_template(result)
    return result


def semantic_template(template: QueryTemplate) -> QueryTemplate:
    """Remove debug-only source aliases/names before structural hashing."""

    return replace(
        template,
        bindings=tuple(
            replace(binding, original_alias=None) for binding in template.bindings
        ),
        parameters=tuple(
            replace(parameter, original_name=None)
            for parameter in template.parameters
        ),
    )


def template_fingerprint(template: QueryTemplate) -> str:
    payload = template_to_json(semantic_template(template)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class TemplateStore:
    """SQLite persistence for deduplicated templates and compiled SQL."""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS er_query_templates (
                template_hash TEXT PRIMARY KEY,
                schema_fingerprint TEXT NOT NULL,
                template_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS er_query_instances (
                query_id TEXT PRIMARY KEY,
                template_hash TEXT NOT NULL,
                parameter_json TEXT NOT NULL,
                frequency REAL NOT NULL,
                FOREIGN KEY (template_hash)
                    REFERENCES er_query_templates(template_hash)
            );
            CREATE TABLE IF NOT EXISTS compiled_query_cache (
                template_hash TEXT NOT NULL,
                mapping_hash TEXT NOT NULL,
                sql_template TEXT NOT NULL,
                PRIMARY KEY (template_hash, mapping_hash)
            );
            """
        )

    def put_template(self, template: QueryTemplate) -> str:
        fingerprint = template_fingerprint(template)
        self.connection.execute(
            """
            INSERT OR IGNORE INTO er_query_templates
                (template_hash, schema_fingerprint, template_json)
            VALUES (?, ?, ?)
            """,
            (
                fingerprint,
                template.schema_fingerprint,
                template_to_json(template),
            ),
        )
        return fingerprint

    def get_template(self, fingerprint: str) -> QueryTemplate | None:
        row = self.connection.execute(
            "SELECT template_json FROM er_query_templates WHERE template_hash = ?",
            (fingerprint,),
        ).fetchone()
        return None if row is None else template_from_json(row[0])

    def put_instance(
        self,
        query_id: str,
        template_hash: str,
        parameters: Mapping[str, Any],
        frequency: float,
    ) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO er_query_instances
                (query_id, template_hash, parameter_json, frequency)
            VALUES (?, ?, ?, ?)
            """,
            (
                query_id,
                template_hash,
                json.dumps(parameters, sort_keys=True, separators=(",", ":")),
                float(frequency),
            ),
        )

    def put_compiled_sql(
        self,
        template_hash: str,
        mapping_hash: str,
        sql: str,
    ) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO compiled_query_cache
                (template_hash, mapping_hash, sql_template)
            VALUES (?, ?, ?)
            """,
            (template_hash, mapping_hash, sql),
        )

    def get_compiled_sql(
        self,
        template_hash: str,
        mapping_hash: str,
    ) -> str | None:
        row = self.connection.execute(
            """
            SELECT sql_template
            FROM compiled_query_cache
            WHERE template_hash = ? AND mapping_hash = ?
            """,
            (template_hash, mapping_hash),
        ).fetchone()
        return None if row is None else row[0]


# ---------------------------------------------------------------------------
# Demand analysis
# ---------------------------------------------------------------------------


@dataclass(frozen=True, order=True)
class RequiredSlot:
    kind: str
    id: str = ""


def slot_for_expression(expression: Expression) -> RequiredSlot | None:
    if isinstance(expression, Attribute):
        return RequiredSlot("attribute", expression.attribute_id)
    if isinstance(expression, Reference):
        return RequiredSlot("reference", expression.reference_type)
    if isinstance(expression, OwnerReference):
        return RequiredSlot("owner_reference", expression.reference_type)
    if isinstance(expression, EndpointReference):
        return RequiredSlot("endpoint", expression.role_id)
    return None


def collect_required_slots(
    template: QueryTemplate,
) -> dict[str, frozenset[RequiredSlot]]:
    validate_template(template)
    result: MutableMapping[str, set[RequiredSlot]] = defaultdict(set)
    for binding in template.bindings:
        result[binding.id]
    for root in query_expression_roots(template):
        for expression in walk_expression(root):
            slot = slot_for_expression(expression)
            if slot is not None:
                result[expression.binding].add(slot)  # type: ignore[attr-defined]
    return {
        binding: frozenset(slots)
        for binding, slots in result.items()
    }


# ---------------------------------------------------------------------------
# Declarative physical mapping catalog
# ---------------------------------------------------------------------------


class MappingError(ValueError):
    pass


@dataclass(frozen=True)
class OutputExpression:
    name: str
    sql: str


@dataclass(frozen=True)
class SlotProvider:
    outputs: tuple[OutputExpression, ...]
    required_fragments: tuple[str, ...] = ()


@dataclass(frozen=True)
class StructuralFragment:
    id: str
    sql: str
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class AccessBranch:
    """One physical branch of a conceptual object extent.

    from_sql may contain a table scan, a derived table, or a LATERAL unnest.
    Providers use trusted mapping SQL expressions and canonical output names.
    """

    from_sql: str
    providers: Mapping[RequiredSlot, SlotProvider]
    fragments: Mapping[str, StructuralFragment]
    predicates: tuple[str, ...] = ()


@dataclass(frozen=True)
class ObjectMappingSpec:
    kind: str
    object_id: str
    branches: tuple[AccessBranch, ...]
    output_unit: str
    duplicate_free: bool = True


@dataclass(frozen=True)
class AccessPlan:
    sql: str
    resolved_slots: Mapping[RequiredSlot, tuple[str, ...]]
    output_unit: str
    duplicate_free: bool


class MappingCatalog(Protocol):
    mapping_id: str

    def resolve_access(
        self,
        binding: Binding,
        required_slots: frozenset[RequiredSlot],
    ) -> AccessPlan:
        ...


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _fragment_order(
    fragments: Mapping[str, StructuralFragment],
    requested: Iterable[str],
) -> list[str]:
    ordered: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(fragment_id: str) -> None:
        if fragment_id in visited:
            return
        if fragment_id in visiting:
            raise MappingError(f"Fragment dependency cycle at {fragment_id!r}")
        try:
            fragment = fragments[fragment_id]
        except KeyError as error:
            raise MappingError(f"Unknown fragment {fragment_id!r}") from error
        visiting.add(fragment_id)
        for dependency in fragment.dependencies:
            visit(dependency)
        visiting.remove(fragment_id)
        visited.add(fragment_id)
        ordered.append(fragment_id)

    for requested_id in requested:
        visit(requested_id)
    return ordered


class StaticMappingCatalog:
    """Mapping catalog backed by declarative ObjectMappingSpec objects."""

    def __init__(self, mapping_id: str, specifications: Sequence[ObjectMappingSpec]):
        self.mapping_id = mapping_id
        self._specifications = {
            (specification.kind, specification.object_id): specification
            for specification in specifications
        }
        if len(self._specifications) != len(specifications):
            raise MappingError("Duplicate object mapping specification")

    def resolve_access(
        self,
        binding: Binding,
        required_slots: frozenset[RequiredSlot],
    ) -> AccessPlan:
        try:
            specification = self._specifications[(binding.kind, binding.object_id)]
        except KeyError as error:
            raise MappingError(
                f"No mapping for {binding.kind} {binding.object_id!r}"
            ) from error
        if not specification.branches:
            raise MappingError(f"{binding.object_id!r} has no extent branches")

        branch_queries: list[str] = []
        canonical_slot_outputs: dict[RequiredSlot, tuple[str, ...]] = {}

        for branch_number, branch in enumerate(specification.branches):
            missing = required_slots - set(branch.providers)
            if missing:
                raise MappingError(
                    f"Mapping branch {branch_number} for {binding.object_id!r} "
                    f"cannot provide slots {sorted(missing)}"
                )

            requested_fragments: list[str] = []
            output_by_name: dict[str, str] = {}

            for slot in sorted(required_slots):
                provider = branch.providers[slot]
                requested_fragments.extend(provider.required_fragments)
                names = tuple(output.name for output in provider.outputs)
                previous_names = canonical_slot_outputs.setdefault(slot, names)
                if previous_names != names:
                    raise MappingError(
                        f"Branches disagree on canonical outputs for slot {slot}"
                    )
                for output in provider.outputs:
                    existing = output_by_name.get(output.name)
                    if existing is not None and existing != output.sql:
                        raise MappingError(
                            f"Output {output.name!r} has conflicting expressions"
                        )
                    output_by_name[output.name] = output.sql

            if not output_by_name:
                output_by_name["__present"] = "1"

            select_sql = ",\n    ".join(
                f"{expression} AS {quote_identifier(name)}"
                for name, expression in output_by_name.items()
            )
            parts = [f"SELECT\n    {select_sql}", f"FROM {branch.from_sql}"]
            for fragment_id in _fragment_order(
                branch.fragments,
                requested_fragments,
            ):
                parts.append(branch.fragments[fragment_id].sql)
            if branch.predicates:
                parts.append("WHERE " + " AND ".join(
                    f"({predicate})" for predicate in branch.predicates
                ))
            branch_queries.append("\n".join(parts))

        return AccessPlan(
            sql="\nUNION ALL\n".join(branch_queries),
            resolved_slots=canonical_slot_outputs,
            output_unit=specification.output_unit,
            duplicate_free=specification.duplicate_free,
        )


# ---------------------------------------------------------------------------
# PostgreSQL query lowering
# ---------------------------------------------------------------------------


_SAFE_FUNCTION = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class CompiledQuery:
    sql: str
    template_hash: str
    mapping_id: str
    output_columns: tuple[str, ...]
    parameters: tuple[ParameterDefinition, ...]


class PostgreSQLCompiler:
    def __init__(self, catalog: MappingCatalog):
        self.catalog = catalog
        self._bindings: dict[str, Binding] = {}
        self._access: dict[str, AccessPlan] = {}

    def compile(self, template: QueryTemplate) -> CompiledQuery:
        validate_template(template)
        requirements = collect_required_slots(template)
        self._bindings = {binding.id: binding for binding in template.bindings}
        self._access = {
            binding.id: self.catalog.resolve_access(
                binding,
                requirements[binding.id],
            )
            for binding in template.bindings
        }

        ctes = []
        for binding in template.bindings:
            access = self._access[binding.id]
            ctes.append(
                f"{quote_identifier(binding.id)} AS (\n{_indent(access.sql, 4)}\n)"
            )

        select_parts: list[str] = []
        output_columns: list[str] = []
        for item in template.select:
            values = self._render_value(item.expression)
            if len(values) == 1:
                alias = item.alias
                select_parts.append(
                    f"{values[0]} AS {quote_identifier(alias)}"
                )
                output_columns.append(alias)
            else:
                for index, value in enumerate(values):
                    alias = f"{item.alias}__{index}"
                    select_parts.append(
                        f"{value} AS {quote_identifier(alias)}"
                    )
                    output_columns.append(alias)

        distinct = "DISTINCT " if template.distinct or template.row_semantics == "set" else ""
        parts = [
            "WITH",
            ",\n".join(ctes),
            f"SELECT {distinct}\n    " + ",\n    ".join(select_parts),
            "FROM " + self._render_from(template.from_expression),
        ]
        if template.where is not None:
            parts.append("WHERE " + self._scalar(template.where))

        group_parts: list[str] = []
        for expression in template.group_by:
            group_parts.extend(self._render_value(expression))

        # Conceptual grouping by an entity reference functionally determines
        # its attributes. PostgreSQL cannot infer that key through a CTE, so
        # add projected nonaggregate values to the physical GROUP BY.
        if group_parts:
            group_set = set(template.group_by)
            grouped_reference_bindings = {
                expression.binding
                for expression in template.group_by
                if isinstance(expression, Reference)
            }
            for item in template.select:
                expression = item.expression
                if contains_aggregate(expression) or expression in group_set:
                    continue
                dependencies = expression_bindings(expression)
                if dependencies.issubset(grouped_reference_bindings):
                    group_parts.extend(self._render_value(expression))
            group_parts = list(dict.fromkeys(group_parts))
            parts.append("GROUP BY\n    " + ",\n    ".join(group_parts))

        if template.having is not None:
            parts.append("HAVING " + self._scalar(template.having))

        sql = "\n".join(parts) + ";"
        return CompiledQuery(
            sql=sql,
            template_hash=template_fingerprint(template),
            mapping_id=self.catalog.mapping_id,
            output_columns=tuple(output_columns),
            parameters=template.parameters,
        )

    def _slot_columns(self, binding: str, slot: RequiredSlot) -> tuple[str, ...]:
        try:
            names = self._access[binding].resolved_slots[slot]
        except KeyError as error:
            raise MappingError(
                f"Access plan for {binding!r} does not expose {slot}"
            ) from error
        return tuple(
            f"{quote_identifier(binding)}.{quote_identifier(name)}"
            for name in names
        )

    def _render_value(self, expression: Expression) -> tuple[str, ...]:
        slot = slot_for_expression(expression)
        if slot is not None:
            return self._slot_columns(expression.binding, slot)  # type: ignore[attr-defined]
        if isinstance(expression, ParameterReference):
            if not _SAFE_FUNCTION.fullmatch(expression.parameter_id):
                raise QueryValidationError(
                    f"Unsafe parameter ID {expression.parameter_id!r}"
                )
            return (f"%({expression.parameter_id})s",)
        if isinstance(expression, Literal):
            return (_render_literal(expression.value),)
        if not isinstance(expression, Apply):
            raise TypeError(f"Unsupported expression {expression!r}")

        op = expression.op
        if op == "aggregate":
            return (self._render_aggregate(expression),)
        if op in {"eq", "ne"}:
            if len(expression.arguments) != 2:
                raise QueryValidationError(f"{op} expects two arguments")
            left = self._render_value(expression.arguments[0])
            right = self._render_value(expression.arguments[1])
            if len(left) != len(right):
                raise QueryValidationError(
                    f"Reference comparison arity mismatch: {len(left)} vs {len(right)}"
                )
            comparisons = [
                f"{left_part} {'=' if op == 'eq' else '<>'} {right_part}"
                for left_part, right_part in zip(left, right)
            ]
            connector = " AND " if op == "eq" else " OR "
            return ("(" + connector.join(comparisons) + ")",)
        if op in {"lt", "lte", "gt", "gte", "add", "sub", "mul", "div"}:
            if len(expression.arguments) != 2:
                raise QueryValidationError(f"{op} expects two arguments")
            token = {
                "lt": "<",
                "lte": "<=",
                "gt": ">",
                "gte": ">=",
                "add": "+",
                "sub": "-",
                "mul": "*",
                "div": "/",
            }[op]
            left = self._scalar(expression.arguments[0])
            right = self._scalar(expression.arguments[1])
            return (f"({left} {token} {right})",)
        if op in {"and", "or"}:
            if not expression.arguments:
                raise QueryValidationError(f"{op} expects at least one argument")
            connector = " AND " if op == "and" else " OR "
            return (
                "(" + connector.join(self._scalar(arg) for arg in expression.arguments) + ")",
            )
        if op == "not":
            if len(expression.arguments) != 1:
                raise QueryValidationError("not expects one argument")
            return (f"(NOT {self._scalar(expression.arguments[0])})",)
        if op in {"is_null", "is_not_null"}:
            if len(expression.arguments) != 1:
                raise QueryValidationError(f"{op} expects one argument")
            token = "IS NULL" if op == "is_null" else "IS NOT NULL"
            return (f"({self._scalar(expression.arguments[0])} {token})",)
        if op == "in":
            if len(expression.arguments) < 2:
                raise QueryValidationError("in expects a value and at least one candidate")
            value = self._scalar(expression.arguments[0])
            candidates = ", ".join(
                self._scalar(argument) for argument in expression.arguments[1:]
            )
            return (f"({value} IN ({candidates}))",)
        if op == "function":
            function = _safe_function_name(expression.function)
            arguments = ", ".join(
                self._scalar(argument) for argument in expression.arguments
            )
            return (f"{function}({arguments})",)
        raise QueryValidationError(f"Unsupported expression operator {op!r}")

    def _scalar(self, expression: Expression) -> str:
        values = self._render_value(expression)
        if len(values) != 1:
            raise QueryValidationError(
                f"Expected scalar expression; found {len(values)} reference components"
            )
        return values[0]

    def _render_aggregate(self, expression: Apply) -> str:
        function = _safe_function_name(expression.function)
        if not expression.arguments:
            if function.upper() != "COUNT":
                raise QueryValidationError(
                    f"Only COUNT may have an empty aggregate argument"
                )
            if expression.distinct:
                raise QueryValidationError("COUNT(DISTINCT *) is invalid")
            return "COUNT(*)"
        if len(expression.arguments) != 1:
            raise QueryValidationError("Aggregate expects zero or one argument")
        argument_parts = self._render_value(expression.arguments[0])
        if len(argument_parts) == 1:
            argument = argument_parts[0]
        else:
            argument = "ROW(" + ", ".join(argument_parts) + ")"
        distinct = "DISTINCT " if expression.distinct else ""
        return f"{function}({distinct}{argument})"

    def _render_from(self, source: FromExpression) -> str:
        if isinstance(source, ScanSource):
            return quote_identifier(source.binding)
        join_type = source.join_type.lower()
        if join_type not in {"inner", "left", "right", "full", "cross"}:
            raise QueryValidationError(f"Unsupported join type {source.join_type!r}")
        left = self._render_from(source.left)
        right = self._render_from(source.right)
        if join_type == "cross":
            if source.condition is not None:
                raise QueryValidationError("CROSS JOIN cannot have an ON condition")
            return f"({left} CROSS JOIN {right})"
        if source.condition is None:
            raise QueryValidationError(f"{join_type.upper()} JOIN requires a condition")
        return (
            f"({left} {join_type.upper()} JOIN {right} "
            f"ON {self._scalar(source.condition)})"
        )


def _safe_function_name(name: str | None) -> str:
    if name is None or not _SAFE_FUNCTION.fullmatch(name):
        raise QueryValidationError(f"Unsafe or missing function name {name!r}")
    return name.upper()


def _render_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise QueryValidationError("Non-finite numeric literal")
        return repr(value)
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    raise QueryValidationError(
        f"Unsupported literal type {type(value).__name__}; parameterize it instead"
    )


def _indent(value: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in value.splitlines())


# ---------------------------------------------------------------------------
# Adapters for construct_create_statements/er_graph outputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PhysicalColumn:
    table: str
    column: str
    physical_type: str
    conceptual_id: str
    source_node: str


class PhysicalSchemaIndex:
    """Indexes schemas_without_foreign_key_statements by conceptual lineage."""

    def __init__(self, physical_schemas: Sequence[Sequence[Any]]):
        by_conceptual: MutableMapping[str, list[PhysicalColumn]] = defaultdict(list)
        by_table: MutableMapping[str, list[PhysicalColumn]] = defaultdict(list)
        primary_keys: dict[str, tuple[str, ...]] = {}
        for schema in physical_schemas:
            if len(schema) < 4:
                raise MappingError(f"Malformed physical schema entry: {schema!r}")
            table_name = schema[0]
            table_attributes = schema[1]
            primary_keys[table_name] = tuple(schema[3])
            for attribute in table_attributes:
                if len(attribute) < 4:
                    raise MappingError(
                        f"Malformed physical column entry in {table_name}: {attribute!r}"
                    )
                column = PhysicalColumn(
                    table=table_name,
                    column=attribute[0],
                    physical_type=attribute[1],
                    conceptual_id=attribute[2],
                    source_node=attribute[3],
                )
                by_conceptual[column.conceptual_id].append(column)
                by_table[table_name].append(column)
        self.by_conceptual = {
            key: tuple(values) for key, values in by_conceptual.items()
        }
        self.by_table = {key: tuple(values) for key, values in by_table.items()}
        self.primary_keys = primary_keys

    def providers(self, conceptual_id: str) -> tuple[PhysicalColumn, ...]:
        return self.by_conceptual.get(conceptual_id, ())


@dataclass(frozen=True)
class KeyComponent:
    physical_column: str
    physical_type: str
    conceptual_component: str
    er_name: str


def normalize_key_group(group: Any) -> tuple[KeyComponent, ...]:
    """Normalize one Key.table_key group from er_graph.Key.

    A strong entity uses a flat list of tuples; weak entities and relationships
    use a list of groups.  Call this function on one flat group.
    """

    if group is None:
        return ()
    result: list[KeyComponent] = []
    for component in group:
        if len(component) < 4:
            raise MappingError(f"Malformed key component {component!r}")
        result.append(
            KeyComponent(
                physical_column=component[0],
                physical_type=component[1],
                conceptual_component=component[2],
                er_name=component[3],
            )
        )
    return tuple(result)


@dataclass(frozen=True)
class WeakIdentityLayout:
    owner: tuple[KeyComponent, ...]
    discriminator: tuple[KeyComponent, ...]


def weak_identity_layout(weak_entity: Any) -> WeakIdentityLayout:
    if not getattr(weak_entity, "is_weak_entity", False):
        raise MappingError(f"{getattr(weak_entity, 'unique_name', weak_entity)!r} is not weak")
    groups = weak_entity.key.table_key
    if len(groups) != 2:
        raise MappingError("Weak key must contain owner and discriminator groups")
    return WeakIdentityLayout(
        owner=normalize_key_group(groups[0]),
        discriminator=normalize_key_group(groups[1]),
    )


@dataclass(frozen=True)
class EndpointKeyLayout:
    endpoint_id: str
    target_entity: str
    components: tuple[KeyComponent, ...]
    reference_table: str | None


def relationship_endpoint_layouts(
    relationship: Any,
    *,
    recursive_group_roles: Sequence[str] | None = None,
) -> tuple[EndpointKeyLayout, ...]:
    """Normalize relationship endpoint groups.

    For nonrecursive relationships, Key.table_key_entities identifies the
    conceptual side even when 1:N key groups are reordered.  For recursive
    relationships that list is ambiguous; pass the role corresponding to each
    physical key group.  The best place to retain that ordering is inside
    define_node_keys_for_relationship while it is being constructed.
    """

    key = relationship.key
    groups = key.table_key
    entities = key.table_key_entities
    reference_tables = key.reference_table or [None] * len(groups)
    recursive = relationship.entity1 == relationship.entity2
    if recursive:
        if recursive_group_roles is None or len(recursive_group_roles) != len(groups):
            raise MappingError(
                "Recursive endpoint key-group order is ambiguous; provide "
                "recursive_group_roles captured during key construction"
            )
        endpoint_ids = list(recursive_group_roles)
        target_entities = [relationship.entity1.unique_name] * len(groups)
    else:
        endpoint_ids = [entity_group[0] for entity_group in entities]
        target_entities = endpoint_ids
    return tuple(
        EndpointKeyLayout(
            endpoint_id=endpoint_ids[index],
            target_entity=target_entities[index],
            components=normalize_key_group(groups[index]),
            reference_table=reference_tables[index],
        )
        for index in range(len(groups))
    )


# ---------------------------------------------------------------------------
# Executable reference mapping and tests
# ---------------------------------------------------------------------------


def reference_mapping() -> StaticMappingCatalog:
    """A small mapping used by the self-tests and as a construction example."""

    accessory_ref_product = RequiredSlot("reference", "entity:Product")
    accessory_ref = RequiredSlot("reference", "entity:Accessory")
    accessory_type = RequiredSlot(
        "attribute", "attribute:Accessory.accessory_type"
    )
    accessory_active = RequiredSlot("attribute", "attribute:Product.is_active")
    accessory_spec = ObjectMappingSpec(
        kind="entity",
        object_id="entity:Accessory",
        output_unit="one_row_per_entity",
        branches=(
            AccessBranch(
                from_sql="accessory AS ac",
                providers={
                    accessory_ref_product: SlotProvider(
                        (OutputExpression("__id", "ac.product_id"),)
                    ),
                    accessory_ref: SlotProvider(
                        (OutputExpression("__id", "ac.product_id"),)
                    ),
                    accessory_type: SlotProvider(
                        (OutputExpression("accessory_type", "ac.accessory_type"),)
                    ),
                    accessory_active: SlotProvider(
                        (OutputExpression("is_active", "p.is_active"),),
                        required_fragments=("product",),
                    ),
                },
                fragments={
                    "product": StructuralFragment(
                        id="product",
                        sql=(
                            "JOIN product AS p "
                            "ON p.product_id = ac.product_id"
                        ),
                    )
                },
            ),
        ),
    )

    ph_ref = RequiredSlot("reference", "weak-entity:PriceHistory")
    ph_owner = RequiredSlot("owner_reference", "entity:Product")
    ph_price = RequiredSlot("attribute", "attribute:PriceHistory.price")
    price_history_spec = ObjectMappingSpec(
        kind="weak_entity",
        object_id="weak-entity:PriceHistory",
        output_unit="one_row_per_weak_entity",
        branches=(
            AccessBranch(
                from_sql="price_history AS ph",
                providers={
                    ph_ref: SlotProvider(
                        (
                            OutputExpression("__owner_id", "ph.product_id"),
                            OutputExpression("__partial_key", "ph.price_id"),
                        )
                    ),
                    ph_owner: SlotProvider(
                        (OutputExpression("__owner_id", "ph.product_id"),)
                    ),
                    ph_price: SlotProvider(
                        (OutputExpression("price", "ph.price"),)
                    ),
                },
                fragments={},
            ),
        ),
    )

    phone_ref_product = RequiredSlot("reference", "entity:Product")
    phone_ref = RequiredSlot("reference", "entity:Phone")
    phone_spec = ObjectMappingSpec(
        kind="entity",
        object_id="entity:Phone",
        output_unit="one_row_per_entity",
        branches=(
            AccessBranch(
                from_sql="phone AS phone_row",
                providers={
                    phone_ref_product: SlotProvider(
                        (OutputExpression("__id", "phone_row.product_id"),)
                    ),
                    phone_ref: SlotProvider(
                        (OutputExpression("__id", "phone_row.product_id"),)
                    ),
                },
                fragments={},
            ),
        ),
    )

    role_phone = RequiredSlot("endpoint", "role:bundle_phones.phone_id")
    role_bundle = RequiredSlot(
        "endpoint", "role:bundle_phones.bundle_phone_id"
    )
    bundle_spec = ObjectMappingSpec(
        kind="relationship",
        object_id="relationship:bundle_phones",
        output_unit="one_row_per_relationship",
        branches=(
            AccessBranch(
                from_sql="bundle_phones AS bf",
                providers={
                    role_phone: SlotProvider(
                        (OutputExpression("__phone", "bf.phone_id"),)
                    ),
                    role_bundle: SlotProvider(
                        (OutputExpression("__bundle_phone", "bf.bundle_phone_id"),)
                    ),
                },
                fragments={},
            ),
        ),
    )
    return StaticMappingCatalog(
        "reference-mapping-v1",
        (accessory_spec, price_history_spec, phone_spec, bundle_spec),
    )


def reference_query() -> QueryTemplate:
    accessory_type = Attribute(
        "b0",
        "attribute:Accessory.accessory_type",
        TEXT,
        accessed_through="entity:Accessory",
    )
    active = Attribute(
        "b0",
        "attribute:Product.is_active",
        INTEGER,
        accessed_through="entity:Accessory",
    )
    price = Attribute("b1", "attribute:PriceHistory.price", INTEGER)
    ph_ref = Reference("b1", "weak-entity:PriceHistory")
    return QueryTemplate(
        format_version=1,
        schema_fingerprint="example2-v1",
        bindings=(
            Binding("b0", "entity", "entity:Accessory", "a"),
            Binding("b1", "weak_entity", "weak-entity:PriceHistory", "ph"),
        ),
        parameters=(
            ParameterDefinition("p0", INTEGER, "active"),
            ParameterDefinition("p1", INTEGER, "minimum_price"),
        ),
        from_expression=JoinSource(
            ScanSource("b0"),
            ScanSource("b1"),
            "inner",
            eq(
                OwnerReference("b1", "entity:Product"),
                Reference("b0", "entity:Product"),
            ),
        ),
        where=and_(
            eq(active, ParameterReference("p0", INTEGER)),
            gt(price, ParameterReference("p1", INTEGER)),
        ),
        group_by=(Reference("b0", "entity:Accessory"),),
        select=(
            SelectItem("o0", "accessory_type", accessory_type),
            SelectItem(
                "o1",
                "price_count",
                aggregate("count", ph_ref, BIGINT, distinct=True),
            ),
            SelectItem("o2", "minimum_price", aggregate("min", price, INTEGER)),
        ),
    )


def recursive_relationship_query() -> QueryTemplate:
    p_ref = Reference("b0", "entity:Phone")
    bp_ref = Reference("b2", "entity:Phone")
    return QueryTemplate(
        format_version=1,
        schema_fingerprint="example2-v1",
        bindings=(
            Binding("b0", "entity", "entity:Phone", "p"),
            Binding(
                "b1", "relationship", "relationship:bundle_phones", "bf"
            ),
            Binding("b2", "entity", "entity:Phone", "bp"),
        ),
        parameters=(),
        from_expression=JoinSource(
            JoinSource(
                ScanSource("b0"),
                ScanSource("b1"),
                "inner",
                eq(
                    EndpointReference(
                        "b1",
                        "role:bundle_phones.phone_id",
                        "entity:Phone",
                    ),
                    p_ref,
                ),
            ),
            ScanSource("b2"),
            "inner",
            eq(
                EndpointReference(
                    "b1",
                    "role:bundle_phones.bundle_phone_id",
                    "entity:Phone",
                ),
                bp_ref,
            ),
        ),
        group_by=(p_ref,),
        select=(
            SelectItem("o0", "phone", p_ref),
            SelectItem(
                "o1",
                "bundled_phone_count",
                aggregate("count", bp_ref, BIGINT, distinct=True),
            ),
        ),
    )


def run_self_tests() -> None:
    mapping = reference_mapping()
    query = reference_query()
    validate_template(query)

    encoded = template_to_json(query)
    decoded = template_from_json(encoded)
    assert decoded == query
    assert template_fingerprint(decoded) == template_fingerprint(query)

    requirements = collect_required_slots(query)
    assert RequiredSlot("attribute", "attribute:Product.is_active") in requirements["b0"]
    assert RequiredSlot("owner_reference", "entity:Product") in requirements["b1"]

    compiled = PostgreSQLCompiler(mapping).compile(query)
    assert "SELECT *" not in compiled.sql.upper()
    assert "JOIN product AS p ON p.product_id = ac.product_id" in compiled.sql
    assert '"b1"."__owner_id" = "b0"."__id"' in compiled.sql
    assert "COUNT(DISTINCT ROW(" in compiled.sql
    assert "GROUP BY" in compiled.sql
    assert "base_price" not in compiled.sql

    recursive = PostgreSQLCompiler(mapping).compile(recursive_relationship_query())
    assert '"b1"."__phone" = "b0"."__id"' in recursive.sql
    assert '"b1"."__bundle_phone" = "b2"."__id"' in recursive.sql
    assert recursive.sql.count("phone AS phone_row") == 2

    connection = sqlite3.connect(":memory:")
    store = TemplateStore(connection)
    fingerprint = store.put_template(query)
    store.put_instance("q1", fingerprint, {"p0": 1, "p1": 25}, 10.0)
    store.put_compiled_sql(fingerprint, mapping.mapping_id, compiled.sql)
    connection.commit()
    assert store.get_template(fingerprint) == query
    assert store.get_compiled_sql(fingerprint, mapping.mapping_id) == compiled.sql

    print("All E/R query rewriter self-tests passed.")
    print()
    print(compiled.sql)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the executable reference tests and print generated SQL",
    )
    arguments = parser.parse_args(argv)
    if arguments.self_test:
        run_self_tests()
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
