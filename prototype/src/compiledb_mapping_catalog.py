"""Extract, validate, serialize, and load a CompileDB mapping catalog.

The extractor runs *after* a physical mapping has been selected and after
``create_table_statements``/``generate_attribute_list`` have populated the
mapped graph.  Its output is the mapping-specific JSON input consumed by the
arbitrary E/R query compiler.

Typical use inside CompileDB::

    from compiledb_mapping_catalog import write_mapping_catalog

    write_mapping_catalog(
        "mapping_catalog.json",
        graph=graph,
        tables=tables,
        types=types,
    )

Load the saved catalog for query compilation::

    from compiledb_mapping_catalog import load_mapping_catalog
    from compiledb_query_adapter import CompileDBQueryEngine

    catalog = load_mapping_catalog("mapping_catalog.json")
    engine = CompileDBQueryEngine(graph, tables, types, catalog=catalog)

The exporter derives direct physical branches from ``mapped_table``, the
effective mapped-table collection (``mapped_tables_list`` in the current
CompileDB graph), and hierarchy ``node_cover`` metadata. Each branch
records providers for conceptual attributes, entity/weak identities, owners,
and relationship endpoints, together with only the structural fragments those
providers require. The compiler can therefore project required columns before
``UNION ALL`` and omit unused joins. Folded weak entities are unnested directly
from their mapped JSONB column, and folded 1:N relationships use the many-side
mapped table. Mapping shapes that cannot yet be proven safe retain the complete
conceptual extent as an explicit ``compatibility_extent`` fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Sequence

from compiledb_query_adapter import (
    CompileDBExtentCatalog,
    _attribute_expression,
    _attribute_nodes,
    _canonical_endpoint_role,
    _endpoint_index,
    _endpoint_reference_type,
    _flatten_key_groups,
    _mapping_fingerprint,
    _root_strong_entity,
    conceptual_schema_fingerprint,
)
from er_query_rewriter import (
    AccessBranch,
    AccessPlan,
    Binding,
    MappingCatalog,
    MappingError,
    ObjectMappingSpec,
    OutputExpression,
    RequiredSlot,
    SlotProvider,
    StaticMappingCatalog,
    StructuralFragment,
    quote_identifier,
)


CATALOG_FORMAT_VERSION = 1
DEFAULT_SCHEMA_FILE = Path(__file__).with_name(
    "compiledb_mapping_catalog.schema.json"
)


class CatalogValidationError(ValueError):
    """The serialized mapping catalog violates the compiler contract."""


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {
            str(key): _jsonable(element)
            for key, element in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        elements = [_jsonable(element) for element in value]
        if isinstance(value, (set, frozenset)):
            elements.sort(key=lambda element: json.dumps(element, sort_keys=True))
        return elements
    return str(value)


def _mapped_table(value: Any) -> list[Any] | None:
    if value is None:
        return None
    return list(value)


def _key_layout(node: Any) -> dict[str, Any] | None:
    key = getattr(node, "key", None)
    if key is None:
        return None
    return {
        "table_key": _jsonable(getattr(key, "table_key", None)),
        "reference_key": _jsonable(getattr(key, "reference_key", None)),
        "reference_table": _jsonable(getattr(key, "reference_table", None)),
        "reference_node_unique_name": _jsonable(
            getattr(key, "reference_node_unique_name", None)
        ),
        "table_key_entities": _jsonable(
            getattr(key, "table_key_entities", None)
        ),
    }


def _physical_type(type_name: Any) -> str:
    return str(type_name or "TEXT")


def _conceptual_attribute(attribute: Any) -> dict[str, Any]:
    return {
        "attribute_id": attribute.unique_name,
        "name": attribute.name,
        "type": _physical_type(getattr(attribute, "attr_type", "TEXT")),
        "nullable": None,
        "primary_key": bool(getattr(attribute, "is_primary_key", False)),
        "discriminator": bool(getattr(attribute, "is_discriminator", False)),
        "multivalued": bool(getattr(attribute, "is_multivalued", False)),
        "composite": bool(getattr(attribute, "is_composite", False)),
        "flattened": (
            bool(getattr(attribute, "is_flattened", False))
            if getattr(attribute, "is_composite", False)
            else None
        ),
        "separate_table": (
            bool(getattr(attribute, "is_in_separate_table", False))
            if getattr(attribute, "is_multivalued", False)
            else None
        ),
        "parent_attribute_id": getattr(
            getattr(attribute, "parent_attribute", None), "unique_name", None
        ),
        "declaring_object_id": getattr(
            getattr(attribute, "entity", None), "unique_name", None
        ),
        "mapped_table": _mapped_table(getattr(attribute, "mapped_table", None)),
        "children": [
            child.unique_name
            for child in (getattr(attribute, "children", None) or ())
        ],
    }


def _identity_components(node: Any) -> list[dict[str, Any]]:
    key = getattr(node, "key", None)
    if key is None:
        return []
    result: list[dict[str, Any]] = []
    groups = _flatten_key_groups(key.table_key)
    for group_index, group in enumerate(groups):
        for component_index, component in enumerate(group):
            result.append(
                {
                    "group": group_index,
                    "position": component_index,
                    "physical_column": component[0],
                    "physical_type": _physical_type(component[1]),
                    "conceptual_component": component[2],
                    "er_name": component[3],
                }
            )
    return result


def _mapping_state(node: Any, graph: Any) -> dict[str, Any]:
    effective_mapped_tables = [
        list(table)
        for table in _mapped_table_values(node)
    ]
    state = {
        "configuration_option": (
            graph.config.get(node.unique_name)
            if isinstance(getattr(graph, "config", None), Mapping)
            else None
        ),
        "mapped_table": _mapped_table(getattr(node, "mapped_table", None)),
        "mapped_tables_list": [
            _mapped_table(table)
            for table in (getattr(node, "mapped_tables_list", None) or ())
        ],
        # This is the normalized set the compiler actually branches over.
        # ``mapped_tables_list`` is the field produced by the current graph
        # implementation; the aliases handled by _mapped_table_values keep
        # the extractor compatible with callers that name it mapped_table_set.
        "mapped_table_set": effective_mapped_tables,
        "node_cover": list(getattr(node, "node_cover", None) or ()),
        "select_all_tables": [
            _mapped_table(table)
            for table in sorted(
                getattr(node, "select_all_tables", None) or (),
                key=lambda table: tuple(table),
            )
        ],
        "select_all_nodes": list(getattr(node, "select_all_nodes", None) or ()),
    }
    for name in (
        "is_no_table",
        "is_parent_in_table",
        "is_immediate_parent_in_a_different_table",
        "is_contained_in_parent",
        "is_partially_by_itself",
        "is_all_by_itself",
        "is_contained_all_descendants",
    ):
        if hasattr(node, name):
            state[name] = bool(getattr(node, name))
    return state


def _relationship_endpoints(node: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if node.entity1 == node.entity2:
        requested_roles = tuple(node.recursive_relationship_roles or ())
        if len(requested_roles) != 2:
            raise MappingError(
                f"Recursive relationship {node.unique_name!r} lacks two roles"
            )
        endpoints = (
            (requested_roles[0], node.entity1, node.rel_dict["entity1"]),
            (requested_roles[1], node.entity2, node.rel_dict["entity2"]),
        )
    else:
        endpoints = (
            (node.entity1.unique_name, node.entity1, node.rel_dict["entity1"]),
            (node.entity2.unique_name, node.entity2, node.rel_dict["entity2"]),
        )

    for position, (requested, entity, declaration) in enumerate(endpoints):
        role_id = _canonical_endpoint_role(node, requested)
        result.append(
            {
                "role_id": role_id,
                "declaration_position": position,
                "physical_key_group": _endpoint_index(node, role_id),
                "target_object_id": entity.unique_name,
                "target_reference_type": _endpoint_reference_type(node, role_id),
                "cardinality": "one" if declaration.get("one") else "many",
                "total_participation": bool(declaration.get("total")),
            }
        )
    return result


def _conceptual_object(node: Any, graph: Any) -> dict[str, Any]:
    if node.is_relationship():
        kind = "relationship"
    elif getattr(node, "is_weak_entity", False):
        kind = "weak_entity"
    else:
        kind = "entity"

    if node.is_entity() and not getattr(node, "is_weak_entity", False):
        reference_type = _root_strong_entity(node).unique_name
    elif node.is_entity():
        reference_type = node.unique_name
    else:
        reference_type = None

    result = {
        "object_id": node.unique_name,
        "name": node.name,
        "kind": kind,
        "parent_object_id": getattr(
            getattr(node, "parent_entity", None), "unique_name", None
        ),
        "owner_object_id": (
            getattr(getattr(node, "parent_entity", None), "unique_name", None)
            if kind == "weak_entity"
            else None
        ),
        "reference_type": reference_type,
        "polymorphic": kind == "entity",
        "declared_attributes": [attribute.unique_name for attribute in node.attributes],
        "queryable_attributes": [
            _conceptual_attribute(attribute)
            for attribute in _attribute_nodes(node)
        ],
        "identity_components": _identity_components(node),
        "key_layout": _key_layout(node),
        "relationship_endpoints": (
            _relationship_endpoints(node) if kind == "relationship" else []
        ),
        "mapping_state": _mapping_state(node, graph),
    }
    if kind == "weak_entity":
        owner = node.parent_entity
        result["owner_reference_type"] = (
            owner.unique_name
            if getattr(owner, "is_weak_entity", False)
            else _root_strong_entity(owner).unique_name
        )
    else:
        result["owner_reference_type"] = None
    return result


def _physical_schema(
    tables: Sequence[Sequence[Any]],
    types: Any,
    foreign_key_statements: Sequence[str] | None,
) -> dict[str, Any]:
    physical_tables: list[dict[str, Any]] = []
    for schema in tables:
        if len(schema) < 4:
            raise MappingError(f"Malformed physical schema {schema!r}")
        table_name, attributes, folded, primary_keys = schema[:4]
        columns = []
        for position, attribute in enumerate(attributes):
            if len(attribute) < 4:
                raise MappingError(
                    f"Malformed physical column in {table_name!r}: {attribute!r}"
                )
            columns.append(
                {
                    "position": position,
                    "name": attribute[0],
                    "physical_type": _physical_type(attribute[1]),
                    "nullable": None,
                    "conceptual_id": attribute[2],
                    "source_object_id": attribute[3],
                }
            )
        physical_tables.append(
            {
                "table_name": table_name,
                "columns": columns,
                "primary_key": list(primary_keys),
                "contains_entity_and_relationship": bool(folded),
            }
        )
    return {
        "tables": physical_tables,
        "composite_types": _jsonable(types),
        "foreign_key_statements": list(foreign_key_statements or ()),
        "foreign_keys_complete": foreign_key_statements is not None,
    }


def _all_slots(node: Any) -> tuple[RequiredSlot, ...]:
    result: list[RequiredSlot] = []
    if node.is_relationship():
        result.extend(
            RequiredSlot("endpoint", endpoint["role_id"])
            for endpoint in _relationship_endpoints(node)
        )
    else:
        reference_type = (
            node.unique_name
            if getattr(node, "is_weak_entity", False)
            else _root_strong_entity(node).unique_name
        )
        result.append(RequiredSlot("reference", reference_type))
        if getattr(node, "is_weak_entity", False):
            owner = node.parent_entity
            owner_reference_type = (
                owner.unique_name
                if getattr(owner, "is_weak_entity", False)
                else _root_strong_entity(owner).unique_name
            )
            result.append(RequiredSlot("owner_reference", owner_reference_type))
    result.extend(
        RequiredSlot("attribute", attribute.unique_name)
        for attribute in _attribute_nodes(node)
    )
    return tuple(sorted(set(result)))


def _slot_physical_types(node: Any, slot: RequiredSlot) -> tuple[str | None, ...]:
    groups = _flatten_key_groups(node.key.table_key) if getattr(node, "key", None) else ()
    if slot.kind == "reference":
        return tuple(_physical_type(component[1]) for group in groups for component in group)
    if slot.kind == "owner_reference":
        return tuple(_physical_type(component[1]) for component in groups[0])
    if slot.kind == "endpoint":
        index = _endpoint_index(node, slot.id)
        return tuple(_physical_type(component[1]) for component in groups[index])
    attribute = next(
        candidate
        for candidate in _attribute_nodes(node)
        if candidate.unique_name.lower() == slot.id.lower()
    )
    if getattr(attribute, "is_composite", False) and getattr(attribute, "is_flattened", False):
        return tuple(
            _physical_type(child.attr_type)
            for child in attribute.children
        )
    return (_physical_type(attribute.attr_type),)


def _provider_json(
    node: Any,
    slot: RequiredSlot,
    provider: SlotProvider,
) -> dict[str, Any]:
    types = _slot_physical_types(node, slot)
    return {
        "slot": {"kind": slot.kind, "id": slot.id},
        "outputs": [
            {
                "name": output.name,
                "sql": output.sql,
                "physical_type": types[index] if index < len(types) else None,
                "nullable": None,
            }
            for index, output in enumerate(provider.outputs)
        ],
        "required_fragments": list(provider.required_fragments),
    }


@dataclass(frozen=True)
class _PhysicalTableInfo:
    name: str
    columns: tuple[tuple[Any, ...], ...]
    primary_key: tuple[str, ...]

    @property
    def column_names(self) -> frozenset[str]:
        return frozenset(str(column[0]) for column in self.columns)


@dataclass(frozen=True)
class _DirectSource:
    table: _PhysicalTableInfo
    alias: str
    required_fragment: str | None = None


def _table_index(
    tables: Sequence[Sequence[Any]],
) -> dict[str, _PhysicalTableInfo]:
    result: dict[str, _PhysicalTableInfo] = {}
    for schema in tables:
        if len(schema) < 4:
            continue
        name, columns, _, primary_key = schema[:4]
        result[str(name)] = _PhysicalTableInfo(
            str(name),
            tuple(tuple(column) for column in columns),
            tuple(str(column) for column in primary_key),
        )
    return result


def _mapped_table_name(node: Any) -> str | None:
    mapped = getattr(node, "mapped_table", None)
    if isinstance(mapped, (list, tuple)) and len(mapped) >= 2:
        return str(mapped[1])
    return None


def _mapped_table_values(node: Any) -> tuple[tuple[Any, ...], ...]:
    """Normalize every physical table recorded for one conceptual object."""
    values: list[Any] = []
    mapped = getattr(node, "mapped_table", None)
    if mapped is not None:
        values.append(mapped)

    for field in (
        "mapped_tables_list",
        "mapped_table_set",
        "mapped_tables_set",
    ):
        collection = getattr(node, field, None) or ()
        if isinstance(collection, (set, frozenset)):
            collection = sorted(collection, key=lambda value: tuple(value))
        values.extend(collection)

    result: list[tuple[Any, ...]] = []
    seen_names: set[str] = set()
    for value in values:
        if not isinstance(value, (list, tuple)) or len(value) < 2:
            continue
        name = str(value[1])
        if name in seen_names:
            continue
        seen_names.add(name)
        result.append(tuple(value))
    return tuple(result)


def _mapped_table_names(node: Any) -> tuple[str, ...]:
    """Return physical branches recorded on the selected mapping.

    A folded weak entity or folded 1:N relationship normally has
    ``mapped_table`` set to its owner's/many-side table. When that object is
    distributed over a hierarchy node cover, CompileDB additionally records
    every physical branch in its mapped-table collection.
    """
    return tuple(str(value[1]) for value in _mapped_table_values(node))


def _component_records(value: Any) -> tuple[tuple[Any, ...], ...]:
    """Flatten a key layout while treating one column tuple as atomic."""
    if not isinstance(value, (list, tuple)):
        return ()
    if value and isinstance(value[0], str):
        return (tuple(value),)
    result: list[tuple[Any, ...]] = []
    for element in value:
        result.extend(_component_records(element))
    return tuple(result)


def _string_values(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, (list, tuple)):
        return ()
    result: list[str] = []
    for element in value:
        result.extend(_string_values(element))
    return tuple(result)


def _identity_columns(node: Any) -> tuple[str, ...]:
    key = getattr(node, "key", None)
    if key is None:
        return ()
    return tuple(str(component[0]) for component in _component_records(key.table_key))


def _branch_nodes(node: Any, graph: Any) -> tuple[Any, ...] | None:
    if not node.is_entity() or getattr(node, "is_weak_entity", False):
        return None

    nodes_by_name = {
        candidate.unique_name.lower(): candidate
        for candidate in graph.nodes
        if candidate.is_entity() or candidate.is_relationship()
    }
    cover = tuple(getattr(node, "node_cover", None) or ())
    if cover:
        try:
            branches = tuple(nodes_by_name[str(name).lower()] for name in cover)
        except KeyError:
            return None
    elif _mapped_table_name(node) is not None:
        branches = (node,)
    else:
        return None

    seen_tables: set[str] = set()
    for branch in branches:
        table_name = _mapped_table_name(branch)
        if table_name is None or table_name in seen_tables:
            return None
        seen_tables.add(table_name)

        if branch is not node and not (
            getattr(branch, "is_all_by_itself", False)
            or getattr(branch, "is_contained_all_descendants", False)
        ):
            return None
        if branch is not node and getattr(branch, "is_contained_in_parent", False):
            return None
    return branches


def _descendant_object_names(node: Any) -> tuple[str, ...]:
    """Return deterministic role values for node and all hierarchy children."""
    result: list[str] = []
    pending = [node]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        result.append(str(current.unique_name))
        children = sorted(
            getattr(current, "children", None) or (),
            key=lambda child: str(child.unique_name),
            reverse=True,
        )
        pending.extend(children)
    return tuple(result)


def _hierarchy_branch_predicates(
    branch_node: Any,
    base_table: _PhysicalTableInfo,
) -> tuple[str, ...] | None:
    """Restrict a CIP branch to the queried subtype's role domain."""
    if not getattr(branch_node, "is_contained_in_parent", False):
        return ()

    role_columns = [
        column
        for column in base_table.column_names
        if column.lower() == "role"
    ]
    if len(role_columns) != 1:
        return None
    role_values = ", ".join(
        "'" + value.replace("'", "''") + "'"
        for value in _descendant_object_names(branch_node)
    )
    return (
        f"{quote_identifier('source')}.{quote_identifier(role_columns[0])} "
        f"IN ({role_values})",
    )


def _own_branch_needs_ancestor_chain(node: Any, branch_node: Any) -> bool:
    """Only a vertically split own arm can require ancestor-table joins.

    ABI/CAD descendants in a node cover already contain every inherited
    attribute needed to represent the queried ancestor. Their branch must
    therefore remain a one-table scan.
    """
    return branch_node is node and bool(
        getattr(branch_node, "is_partially_by_itself", False)
        or getattr(branch_node, "is_contained_in_parent", False)
    )


def _ancestor_sources(
    branch_node: Any,
    base_table: _PhysicalTableInfo,
    tables: Mapping[str, _PhysicalTableInfo],
    graph: Any,
) -> tuple[tuple[_DirectSource, ...], tuple[StructuralFragment, ...]]:
    """Build a conditional chain of strong-entity ancestor joins."""
    sources: list[_DirectSource] = [_DirectSource(base_table, "source")]
    fragments: list[StructuralFragment] = []
    nodes_by_name = {
        candidate.unique_name.lower(): candidate
        for candidate in graph.nodes
        if candidate.is_entity() or candidate.is_relationship()
    }
    current = branch_node
    current_source = sources[0]
    visited: set[int] = set()

    while getattr(current, "parent_entity", None) is not None:
        if id(current) in visited:
            break
        visited.add(id(current))
        parent = current.parent_entity
        parent_table_name = _mapped_table_name(parent)
        if parent_table_name == current_source.table.name:
            current = parent
            continue

        key = getattr(current, "key", None)
        reference_tables = tuple(dict.fromkeys(
            _string_values(getattr(key, "reference_table", None))
        ))
        if len(reference_tables) != 1:
            break
        reference_table_name = reference_tables[0]
        reference_table = tables.get(reference_table_name)
        if reference_table is None:
            break

        local_components = _component_records(getattr(key, "table_key", None))
        reference_components = _component_records(
            getattr(key, "reference_key", None)
        )
        if not local_components or len(local_components) != len(reference_components):
            break
        local_columns = tuple(str(component[0]) for component in local_components)
        reference_columns = tuple(
            str(component[0]) for component in reference_components
        )
        if not set(local_columns).issubset(current_source.table.column_names):
            break
        if not set(reference_columns).issubset(reference_table.column_names):
            break

        fragment_id = f"join_ancestor_{len(fragments)}"
        alias = f"ancestor_{len(fragments)}"
        predicates = " AND ".join(
            f"{quote_identifier(current_source.alias)}.{quote_identifier(local)} = "
            f"{quote_identifier(alias)}.{quote_identifier(reference)}"
            for local, reference in zip(local_columns, reference_columns)
        )
        dependencies = (
            (current_source.required_fragment,)
            if current_source.required_fragment is not None
            else ()
        )
        fragments.append(
            StructuralFragment(
                fragment_id,
                f"INNER JOIN {quote_identifier(reference_table_name)} "
                f"AS {quote_identifier(alias)} ON ({predicates})",
                dependencies,
            )
        )
        current_source = _DirectSource(reference_table, alias, fragment_id)
        sources.append(current_source)

        target = None
        for name in _string_values(
            getattr(key, "reference_node_unique_name", None)
        ):
            target = nodes_by_name.get(name.lower())
            if target is not None:
                break
        if target is None:
            candidate = parent
            while candidate is not None:
                if _mapped_table_name(candidate) == reference_table_name:
                    target = candidate
                    break
                candidate = getattr(candidate, "parent_entity", None)
        if target is None:
            break
        current = target

    return tuple(sources), tuple(fragments)


def _source_columns(
    outputs: Sequence[OutputExpression], alias: str
) -> frozenset[str]:
    pattern = re.compile(
        re.escape(quote_identifier(alias)) + r'\."((?:[^"]|"")+)"'
    )
    return frozenset(
        match.replace('""', '"')
        for output in outputs
        for match in pattern.findall(output.sql)
    )


def _attribute_provider(
    attribute: Any,
    sources: Sequence[_DirectSource],
) -> SlotProvider | None:
    # Prefer the catalog's exact conceptual-id annotation.  This also permits
    # a physical column name that differs from the conceptual attribute name.
    directly_annotated = (
        getattr(attribute, "parent_attribute", None) is None
        and not (
            getattr(attribute, "is_composite", False)
            and getattr(attribute, "is_flattened", False)
        )
    )
    if directly_annotated:
        for source in sources:
            matches = [
                str(column[0])
                for column in source.table.columns
                if len(column) >= 3
                and str(column[2]).lower() == attribute.unique_name.lower()
            ]
            if len(matches) == 1:
                required = (
                    (source.required_fragment,)
                    if source.required_fragment is not None
                    else ()
                )
                return SlotProvider(
                    (
                        OutputExpression(
                            attribute.unique_name.split(".", 1)[-1].replace(".", "__"),
                            f"{quote_identifier(source.alias)}."
                            f"{quote_identifier(matches[0])}",
                        ),
                    ),
                    required,
                )
        # The physical schema has a conceptual-id annotation for ordinary
        # columns.  Do not guess by name when that annotation is absent: a
        # folded object may legitimately contain an unrelated same-name
        # column.
        return None

    for source in sources:
        outputs = _attribute_expression(source.alias, attribute)
        columns = _source_columns(outputs, source.alias)
        if columns and columns.issubset(source.table.column_names):
            required = (
                (source.required_fragment,)
                if source.required_fragment is not None
                else ()
            )
            return SlotProvider(outputs, required)
    return None


def _primary_attribute_position(node: Any, attribute: Any) -> int | None:
    primary_attributes = [
        candidate
        for candidate in _attribute_nodes(node)
        if getattr(candidate, "is_primary_key", False)
    ]
    for index, candidate in enumerate(primary_attributes):
        if candidate.unique_name.lower() == attribute.unique_name.lower():
            return index
    return None


def _direct_entity_provider(
    node: Any,
    branch_node: Any,
    slot: RequiredSlot,
    sources: Sequence[_DirectSource],
) -> SlotProvider | None:
    base = sources[0]
    branch_identity = _identity_columns(branch_node)
    conceptual_identity = _identity_columns(node)
    if (
        getattr(branch_node, "is_contained_in_parent", False)
        and not set(branch_identity).issubset(base.table.column_names)
        and len(base.table.primary_key) == len(conceptual_identity)
    ):
        # A CIP subclass shares its parent's table and therefore uses that
        # physical row identity; its conceptual subclass key name need not be
        # materialized as a second column.
        branch_identity = base.table.primary_key

    if slot.kind == "reference":
        if (
            not branch_identity
            or len(branch_identity) != len(conceptual_identity)
            or not set(branch_identity).issubset(base.table.column_names)
        ):
            return None
        return SlotProvider(
            tuple(
                OutputExpression(
                    f"__reference_{index}",
                    f"{quote_identifier(base.alias)}.{quote_identifier(column)}",
                )
                for index, column in enumerate(branch_identity)
            )
        )
    if slot.kind != "attribute":
        return None

    attribute = next(
        (
            candidate
            for candidate in _attribute_nodes(node)
            if candidate.unique_name.lower() == slot.id.lower()
        ),
        None,
    )
    if attribute is None:
        return None
    if getattr(attribute, "is_primary_key", False):
        if (
            not branch_identity
            or len(branch_identity) != len(conceptual_identity)
            or not set(branch_identity).issubset(base.table.column_names)
        ):
            return None
        position = _primary_attribute_position(node, attribute)
        if position is None or position >= len(branch_identity):
            return None
        output_name = attribute.unique_name.split(".", 1)[-1].replace(".", "__")
        return SlotProvider(
            (
                OutputExpression(
                    output_name,
                    f"{quote_identifier(base.alias)}."
                    f"{quote_identifier(branch_identity[position])}",
                ),
            )
        )
    return _attribute_provider(attribute, sources)


def _direct_entity_mapping(
    node: Any,
    graph: Any,
    tables: Sequence[Sequence[Any]],
    *,
    require_complete: bool = True,
) -> dict[str, Any] | None:
    branch_nodes = _branch_nodes(node, graph)
    if branch_nodes is None:
        return None
    table_by_name = _table_index(tables)
    slots = _all_slots(node)
    branches: list[dict[str, Any]] = []

    for branch_node in branch_nodes:
        table_name = _mapped_table_name(branch_node)
        base_table = table_by_name.get(table_name or "")
        if base_table is None:
            return None
        if _own_branch_needs_ancestor_chain(node, branch_node):
            sources, fragments = _ancestor_sources(
                branch_node, base_table, table_by_name, graph
            )
        else:
            # ABI/CAD cover descendants are complete physical records. Do not
            # even expose ancestor sources to their providers: this enforces
            # the one-table branch invariant rather than relying on pruning.
            sources = (_DirectSource(base_table, "source"),)
            fragments = ()
        predicates = _hierarchy_branch_predicates(branch_node, base_table)
        if predicates is None:
            return None
        providers: list[dict[str, Any]] = []
        for slot in slots:
            provider = _direct_entity_provider(
                node, branch_node, slot, sources
            )
            if provider is None:
                if require_complete:
                    return None
                continue
            providers.append(_provider_json(node, slot, provider))

        if not providers:
            return None

        branches.append(
            {
                "branch_id": (
                    f"{node.unique_name}-{branch_node.unique_name}-{table_name}"
                ),
                "from_sql": (
                    f"{quote_identifier(table_name)} AS "
                    f"{quote_identifier(sources[0].alias)}"
                ),
                "providers": providers,
                "fragments": [
                    {
                        "id": fragment.id,
                        "sql": fragment.sql,
                        "dependencies": list(fragment.dependencies),
                    }
                    for fragment in fragments
                ],
                "predicates": list(predicates),
            }
        )

    return {
        "kind": "entity",
        "object_id": node.unique_name,
        "output_unit": "one_row_per_entity",
        "duplicate_free": True,
        "branches_disjoint": True,
        "source_mode": "direct_physical",
        "branches": branches,
    }


def _folded_weak_entity(node: Any) -> bool:
    return bool(
        node.is_entity()
        and getattr(node, "is_weak_entity", False)
        and getattr(node, "is_contained_in_parent", False)
    )


def _folded_relationship(node: Any, graph: Any) -> bool:
    return bool(
        node.is_relationship()
        and isinstance(getattr(graph, "config", None), Mapping)
        and graph.config.get(node.unique_name) == "folded_to_many_side"
    )


def _json_scalar_expression(alias: str, attribute: Any) -> str | None:
    if getattr(attribute, "is_composite", False) or getattr(
        attribute, "is_multivalued", False
    ):
        return None
    name = attribute.unique_name.split(".", 1)[-1].replace(".", "__")
    expression = (
        f"{quote_identifier(alias)}.{quote_identifier('value')} ->> "
        f"'{name.replace("'", "''")}'"
    )
    physical_type = _physical_type(getattr(attribute, "attr_type", "TEXT"))
    if physical_type.upper() not in {
        "TEXT",
        "VARCHAR",
        "VARCHAR(255)",
        "CHAR",
        "CHARACTER VARYING",
    }:
        expression = f"CAST(({expression}) AS {physical_type})"
    return expression


def _record_key_columns(
    node: Any,
    slot: RequiredSlot,
    table: _PhysicalTableInfo,
    *,
    folded_weak: bool,
    folded_relationship: bool,
) -> tuple[str, ...] | None:
    groups = _flatten_key_groups(node.key.table_key)
    if slot.kind == "owner_reference":
        if not groups:
            return None
        if folded_weak:
            return table.primary_key if len(table.primary_key) == len(groups[0]) else None
        columns = tuple(str(component[0]) for component in groups[0])
    elif slot.kind == "endpoint":
        index = _endpoint_index(node, slot.id)
        if index >= len(groups):
            return None
        columns = tuple(str(component[0]) for component in groups[index])
        # CompileDB does not duplicate the many-side identity when a 1:N
        # relationship is folded. It is the primary key of mapped_table.
        if (
            folded_relationship
            and index == 0
            and not set(columns).issubset(table.column_names)
            and len(table.primary_key) == len(groups[index])
        ):
            return table.primary_key
    else:
        return None
    return columns if set(columns).issubset(table.column_names) else None


def _direct_record_provider(
    node: Any,
    slot: RequiredSlot,
    source: _DirectSource,
    *,
    folded_weak: bool,
    folded_relationship: bool,
) -> SlotProvider | None:
    groups = _flatten_key_groups(node.key.table_key)
    base_alias = source.alias

    if slot.kind == "owner_reference":
        columns = _record_key_columns(
            node,
            slot,
            source.table,
            folded_weak=folded_weak,
            folded_relationship=folded_relationship,
        )
        if columns is None:
            return None
        return SlotProvider(
            tuple(
                OutputExpression(
                    f"__owner_{index}",
                    f"{quote_identifier(base_alias)}.{quote_identifier(column)}",
                )
                for index, column in enumerate(columns)
            )
        )

    if slot.kind == "endpoint":
        columns = _record_key_columns(
            node,
            slot,
            source.table,
            folded_weak=folded_weak,
            folded_relationship=folded_relationship,
        )
        if columns is None:
            return None
        safe_role = re.sub(r"[^A-Za-z0-9_]+", "_", slot.id).strip("_")
        return SlotProvider(
            tuple(
                OutputExpression(
                    f"__endpoint_{safe_role}_{index}",
                    f"{quote_identifier(base_alias)}.{quote_identifier(column)}",
                )
                for index, column in enumerate(columns)
            )
        )

    if slot.kind == "reference":
        if not getattr(node, "is_weak_entity", False):
            return None
        owner_columns = _record_key_columns(
            node,
            RequiredSlot("owner_reference", slot.id),
            source.table,
            folded_weak=folded_weak,
            folded_relationship=folded_relationship,
        )
        if owner_columns is None:
            return None
        expressions = [
            f"{quote_identifier(base_alias)}.{quote_identifier(column)}"
            for column in owner_columns
        ]
        if folded_weak:
            discriminator_attributes = [
                attribute
                for attribute in _attribute_nodes(node)
                if getattr(attribute, "is_discriminator", False)
                and str(attribute.unique_name).lower().startswith(
                    node.unique_name.lower() + "."
                )
            ]
            for attribute in discriminator_attributes:
                expression = _json_scalar_expression("folded", attribute)
                if expression is None:
                    return None
                expressions.append(expression)
        else:
            remaining = tuple(
                str(component[0])
                for group in groups[1:]
                for component in group
            )
            if not set(remaining).issubset(source.table.column_names):
                return None
            expressions.extend(
                f"{quote_identifier(base_alias)}.{quote_identifier(column)}"
                for column in remaining
            )
        return SlotProvider(
            tuple(
                OutputExpression(f"__reference_{index}", expression)
                for index, expression in enumerate(expressions)
            )
        )

    if slot.kind != "attribute":
        return None
    attribute = next(
        (
            candidate
            for candidate in _attribute_nodes(node)
            if candidate.unique_name.lower() == slot.id.lower()
        ),
        None,
    )
    if attribute is None:
        return None

    if folded_weak and str(attribute.unique_name).lower().startswith(
        node.unique_name.lower() + "."
    ):
        expression = _json_scalar_expression("folded", attribute)
        if expression is None:
            return None
        name = attribute.unique_name.split(".", 1)[-1].replace(".", "__")
        return SlotProvider((OutputExpression(name, expression),))

    if getattr(node, "is_weak_entity", False) and getattr(
        attribute, "is_primary_key", False
    ):
        owner_columns = _record_key_columns(
            node,
            RequiredSlot("owner_reference", slot.id),
            source.table,
            folded_weak=folded_weak,
            folded_relationship=folded_relationship,
        )
        owner = node.parent_entity
        position = _primary_attribute_position(owner, attribute)
        if (
            owner_columns is None
            or position is None
            or position >= len(owner_columns)
        ):
            return None
        name = attribute.unique_name.split(".", 1)[-1].replace(".", "__")
        return SlotProvider(
            (
                OutputExpression(
                    name,
                    f"{quote_identifier(base_alias)}."
                    f"{quote_identifier(owner_columns[position])}",
                ),
            )
        )

    return _attribute_provider(attribute, (source,))


def _direct_record_mapping(
    node: Any,
    graph: Any,
    tables: Sequence[Sequence[Any]],
    *,
    require_complete: bool,
) -> dict[str, Any] | None:
    table_names = _mapped_table_names(node)
    if not table_names:
        return None
    table_by_name = _table_index(tables)
    slots = _all_slots(node)
    folded_weak = _folded_weak_entity(node)
    folded_relationship = _folded_relationship(node, graph)
    branches: list[dict[str, Any]] = []

    for table_name in table_names:
        table = table_by_name.get(table_name)
        if table is None:
            return None
        source = _DirectSource(table, "source")
        from_sql = f"{quote_identifier(table_name)} AS {quote_identifier('source')}"
        if folded_weak:
            json_columns = [
                str(column[0])
                for column in table.columns
                if len(column) >= 3
                and str(column[2]).lower() == node.unique_name.lower()
            ]
            if not json_columns and node.unique_name in table.column_names:
                json_columns = [node.unique_name]
            if len(json_columns) != 1:
                return None
            from_sql += (
                " CROSS JOIN LATERAL jsonb_array_elements("
                f"{quote_identifier('source')}.{quote_identifier(json_columns[0])}"
                f") AS {quote_identifier('folded')}({quote_identifier('value')})"
            )

        providers: list[dict[str, Any]] = []
        for slot in slots:
            provider = _direct_record_provider(
                node,
                slot,
                source,
                folded_weak=folded_weak,
                folded_relationship=folded_relationship,
            )
            if provider is None:
                if require_complete:
                    return None
                continue
            providers.append(_provider_json(node, slot, provider))
        if not providers:
            return None

        predicates: list[str] = []
        if folded_relationship:
            groups = _flatten_key_groups(node.key.table_key)
            if len(groups) < 2:
                return None
            one_side_columns = tuple(str(component[0]) for component in groups[1])
            if not set(one_side_columns).issubset(table.column_names):
                return None
            predicates.extend(
                f"{quote_identifier('source')}.{quote_identifier(column)} IS NOT NULL"
                for column in one_side_columns
            )

        branches.append(
            {
                "branch_id": f"{node.unique_name}-{table_name}",
                "from_sql": from_sql,
                "providers": providers,
                "fragments": [],
                "predicates": predicates,
            }
        )

    kind = "relationship" if node.is_relationship() else "weak_entity"
    return {
        "kind": kind,
        "object_id": node.unique_name,
        "output_unit": (
            "one_row_per_relationship"
            if kind == "relationship"
            else "one_row_per_weak_entity"
        ),
        "duplicate_free": True,
        "branches_disjoint": True,
        "source_mode": "direct_physical",
        "branches": branches,
    }


def _direct_object_mapping(
    node: Any,
    graph: Any,
    tables: Sequence[Sequence[Any]],
    *,
    require_complete: bool = True,
) -> dict[str, Any] | None:
    if node.is_entity() and not getattr(node, "is_weak_entity", False):
        return _direct_entity_mapping(
            node,
            graph,
            tables,
            require_complete=require_complete,
        )
    if node.is_relationship() or getattr(node, "is_weak_entity", False):
        return _direct_record_mapping(
            node,
            graph,
            tables,
            require_complete=require_complete,
        )
    return None


def _compatibility_mapping_specification(
    node: Any,
    extent_catalog: CompileDBExtentCatalog,
) -> dict[str, Any]:
    """Serialize the legacy full-information extent as a safe fallback."""
    extent_alias = "extent"
    providers = [
        _provider_json(
            node,
            slot,
            extent_catalog._provider(node, slot, extent_alias),
        )
        for slot in _all_slots(node)
    ]
    extent_sql = extent_catalog._extent_sql(node)
    from_sql = (
        "(\n"
        + "\n".join("    " + line for line in extent_sql.splitlines())
        + f"\n) AS {quote_identifier(extent_alias)}"
    )
    kind = (
        "relationship"
        if node.is_relationship()
        else "weak_entity"
        if getattr(node, "is_weak_entity", False)
        else "entity"
    )
    return {
        "kind": kind,
        "object_id": node.unique_name,
        "output_unit": (
            "one_row_per_relationship"
            if kind == "relationship"
            else "one_row_per_weak_entity"
            if kind == "weak_entity"
            else "one_row_per_entity"
        ),
        "duplicate_free": True,
        "branches_disjoint": True,
        "source_mode": "compatibility_extent",
        "branches": [
            {
                "branch_id": f"{node.unique_name}-extent",
                "from_sql": from_sql,
                "providers": providers,
                "fragments": [],
                "predicates": [],
            }
        ],
    }


def _mapping_specification(
    node: Any,
    graph: Any,
    tables: Sequence[Sequence[Any]],
    extent_catalog_factory: Callable[[], CompileDBExtentCatalog],
) -> dict[str, Any]:
    direct = _direct_object_mapping(node, graph, tables)
    if direct is not None:
        return direct
    return _compatibility_mapping_specification(
        node, extent_catalog_factory()
    )


def extract_mapping_catalog(
    graph: Any,
    tables: Sequence[Sequence[Any]],
    types: Any,
    *,
    foreign_key_statements: Sequence[str] | None = None,
    extent_sql_factory: Callable[[Any], str] | None = None,
    mapping_id: str | None = None,
) -> dict[str, Any]:
    """Extract a complete, self-contained compiler mapping catalog."""

    effective_mapping_id = mapping_id or _mapping_fingerprint(graph, tables)
    extent_catalog: CompileDBExtentCatalog | None = None

    def compatibility_catalog() -> CompileDBExtentCatalog:
        nonlocal extent_catalog
        if extent_catalog is None:
            extent_catalog = CompileDBExtentCatalog(
                graph,
                tables,
                types,
                extent_sql_factory=extent_sql_factory,
                mapping_id=effective_mapping_id,
            )
        return extent_catalog

    objects = [
        node
        for node in graph.nodes
        if node.is_entity() or node.is_relationship()
    ]
    result = {
        "$schema": "./compiledb_mapping_catalog.schema.json",
        "format_version": CATALOG_FORMAT_VERSION,
        "mapping_id": effective_mapping_id,
        "conceptual_schema_fingerprint": conceptual_schema_fingerprint(graph),
        "dialect": "postgresql",
        "conceptual_objects": [
            _conceptual_object(node, graph) for node in objects
        ],
        "physical_schema": _physical_schema(
            tables, types, foreign_key_statements
        ),
        "object_mappings": [
            _mapping_specification(node, graph, tables, compatibility_catalog)
            for node in objects
        ],
    }
    validate_mapping_catalog(result)
    return result


def build_mapping_catalog(
    graph: Any,
    tables: Sequence[Sequence[Any]],
    types: Any,
    *,
    foreign_key_statements: Sequence[str] | None = None,
    extent_sql_factory: Callable[[Any], str] | None = None,
    mapping_id: str | None = None,
) -> MappingCatalog:
    """Build a per-query direct/fallback catalog for one physical mapping."""
    # Retained in the public signature because callers use the same arguments
    # for runtime construction and self-contained JSON export. Runtime
    # compilation derives joins from the selected graph/table mapping instead.
    _ = foreign_key_statements
    return CompileDBHybridMappingCatalog(
        graph,
        tables,
        types,
        extent_sql_factory=extent_sql_factory,
        mapping_id=mapping_id,
    )


def _expect(condition: bool, path: str, message: str) -> None:
    if not condition:
        raise CatalogValidationError(f"{path}: {message}")


def _expect_type(value: Any, expected: type, path: str) -> None:
    _expect(isinstance(value, expected), path, f"expected {expected.__name__}")


def _required(mapping: Mapping[str, Any], key: str, path: str) -> Any:
    _expect(key in mapping, path, f"missing required property {key!r}")
    return mapping[key]


def validate_mapping_catalog(catalog: Mapping[str, Any]) -> None:
    """Dependency-free validation of the compiler-critical catalog rules."""

    _expect_type(catalog, Mapping, "$" )
    _expect(
        _required(catalog, "format_version", "$") == CATALOG_FORMAT_VERSION,
        "$.format_version",
        f"expected {CATALOG_FORMAT_VERSION}",
    )
    for key in ("mapping_id", "conceptual_schema_fingerprint", "dialect"):
        _expect_type(_required(catalog, key, "$"), str, f"$.{key}")
    objects = _required(catalog, "conceptual_objects", "$")
    mappings = _required(catalog, "object_mappings", "$")
    _expect_type(objects, list, "$.conceptual_objects")
    _expect_type(mappings, list, "$.object_mappings")
    _expect_type(_required(catalog, "physical_schema", "$"), Mapping, "$.physical_schema")

    object_keys: set[tuple[str, str]] = set()
    for index, obj in enumerate(objects):
        path = f"$.conceptual_objects[{index}]"
        _expect_type(obj, Mapping, path)
        object_id = _required(obj, "object_id", path)
        kind = _required(obj, "kind", path)
        _expect_type(object_id, str, f"{path}.object_id")
        _expect(kind in {"entity", "weak_entity", "relationship"}, f"{path}.kind", "invalid object kind")
        key = (kind, object_id)
        _expect(key not in object_keys, path, f"duplicate conceptual object {key}")
        object_keys.add(key)

    mapping_keys: set[tuple[str, str]] = set()
    for mapping_index, mapping in enumerate(mappings):
        path = f"$.object_mappings[{mapping_index}]"
        _expect_type(mapping, Mapping, path)
        kind = _required(mapping, "kind", path)
        object_id = _required(mapping, "object_id", path)
        key = (kind, object_id)
        _expect(key in object_keys, path, f"mapping has no conceptual object {key}")
        _expect(key not in mapping_keys, path, f"duplicate object mapping {key}")
        mapping_keys.add(key)
        branches = _required(mapping, "branches", path)
        _expect_type(branches, list, f"{path}.branches")
        _expect(bool(branches), f"{path}.branches", "must contain at least one branch")

        canonical_outputs: dict[tuple[str, str], tuple[str, ...]] = {}
        for branch_index, branch in enumerate(branches):
            branch_path = f"{path}.branches[{branch_index}]"
            _expect_type(branch, Mapping, branch_path)
            from_sql = _required(branch, "from_sql", branch_path)
            _expect_type(from_sql, str, f"{branch_path}.from_sql")
            _expect(
                re.search(r"\bSELECT\s+\*", from_sql, re.IGNORECASE) is None,
                f"{branch_path}.from_sql",
                "SELECT * is forbidden",
            )
            providers = _required(branch, "providers", branch_path)
            fragments = _required(branch, "fragments", branch_path)
            predicates = _required(branch, "predicates", branch_path)
            _expect_type(providers, list, f"{branch_path}.providers")
            _expect_type(fragments, list, f"{branch_path}.fragments")
            _expect_type(predicates, list, f"{branch_path}.predicates")

            fragment_ids: set[str] = set()
            fragment_dependencies: dict[str, tuple[str, ...]] = {}
            for fragment_index, fragment in enumerate(fragments):
                fragment_path = f"{branch_path}.fragments[{fragment_index}]"
                fragment_id = _required(fragment, "id", fragment_path)
                _expect_type(fragment_id, str, f"{fragment_path}.id")
                _expect(fragment_id not in fragment_ids, fragment_path, "duplicate fragment ID")
                fragment_ids.add(fragment_id)
                dependencies = tuple(_required(fragment, "dependencies", fragment_path))
                fragment_dependencies[fragment_id] = dependencies
            for fragment_id, dependencies in fragment_dependencies.items():
                for dependency in dependencies:
                    _expect(dependency in fragment_ids, branch_path, f"unknown fragment dependency {dependency!r}")

            provider_keys: set[tuple[str, str]] = set()
            for provider_index, provider in enumerate(providers):
                provider_path = f"{branch_path}.providers[{provider_index}]"
                slot = _required(provider, "slot", provider_path)
                slot_kind = _required(slot, "kind", f"{provider_path}.slot")
                slot_id = _required(slot, "id", f"{provider_path}.slot")
                provider_key = (slot_kind, slot_id)
                _expect(slot_kind in {"attribute", "reference", "owner_reference", "endpoint"}, f"{provider_path}.slot.kind", "invalid slot kind")
                _expect(provider_key not in provider_keys, provider_path, "duplicate provider slot")
                provider_keys.add(provider_key)
                outputs = _required(provider, "outputs", provider_path)
                _expect_type(outputs, list, f"{provider_path}.outputs")
                _expect(bool(outputs), f"{provider_path}.outputs", "must not be empty")
                names: list[str] = []
                for output_index, output in enumerate(outputs):
                    output_path = f"{provider_path}.outputs[{output_index}]"
                    name = _required(output, "name", output_path)
                    sql = _required(output, "sql", output_path)
                    _expect_type(name, str, f"{output_path}.name")
                    _expect_type(sql, str, f"{output_path}.sql")
                    names.append(name)
                previous = canonical_outputs.setdefault(provider_key, tuple(names))
                _expect(previous == tuple(names), provider_path, "branches disagree on output names/order")
                for required_fragment in _required(provider, "required_fragments", provider_path):
                    _expect(required_fragment in fragment_ids, provider_path, f"unknown required fragment {required_fragment!r}")

    _expect(mapping_keys == object_keys, "$.object_mappings", "every conceptual object must have exactly one mapping")


def _object_mapping_specification(
    mapping: Mapping[str, Any],
) -> ObjectMappingSpec:
    branches: list[AccessBranch] = []
    for branch_data in mapping["branches"]:
        providers: dict[RequiredSlot, SlotProvider] = {}
        for provider_data in branch_data["providers"]:
            slot_data = provider_data["slot"]
            slot = RequiredSlot(slot_data["kind"], slot_data["id"])
            providers[slot] = SlotProvider(
                outputs=tuple(
                    OutputExpression(output["name"], output["sql"])
                    for output in provider_data["outputs"]
                ),
                required_fragments=tuple(
                    provider_data["required_fragments"]
                ),
            )
        fragments = {
            fragment_data["id"]: StructuralFragment(
                id=fragment_data["id"],
                sql=fragment_data["sql"],
                dependencies=tuple(fragment_data["dependencies"]),
            )
            for fragment_data in branch_data["fragments"]
        }
        branches.append(
            AccessBranch(
                from_sql=branch_data["from_sql"],
                providers=providers,
                fragments=fragments,
                predicates=tuple(branch_data["predicates"]),
            )
        )
    return ObjectMappingSpec(
        kind=mapping["kind"],
        object_id=mapping["object_id"],
        branches=tuple(branches),
        output_unit=mapping["output_unit"],
        duplicate_free=bool(mapping["duplicate_free"]),
    )


class CompileDBHybridMappingCatalog:
    """Choose direct branches or a legacy extent for each query binding.

    Direct support is tested against the slots required by the current AST,
    rather than against every attribute the conceptual object could ever
    expose.  Thus an unrelated complex attribute cannot force a simple query
    back to a full-information extent.
    """

    def __init__(
        self,
        graph: Any,
        tables: Sequence[Sequence[Any]],
        types: Any,
        *,
        extent_sql_factory: Callable[[Any], str] | None = None,
        mapping_id: str | None = None,
    ) -> None:
        self.mapping_id = mapping_id or _mapping_fingerprint(graph, tables)
        self._graph = graph
        self._tables = tables
        self._types = types
        self._extent_sql_factory = extent_sql_factory
        self._fallback: CompileDBExtentCatalog | None = None

        specifications: list[ObjectMappingSpec] = []
        self._direct_slots: dict[
            tuple[str, str], frozenset[RequiredSlot]
        ] = {}
        for node in graph.nodes:
            if not (node.is_entity() or node.is_relationship()):
                continue
            mapping = _direct_object_mapping(
                node,
                graph,
                tables,
                require_complete=False,
            )
            if mapping is None:
                continue
            specification = _object_mapping_specification(mapping)
            supported = set(specification.branches[0].providers)
            for branch in specification.branches[1:]:
                supported.intersection_update(branch.providers)
            if not supported:
                continue
            specifications.append(specification)
            self._direct_slots[(specification.kind, specification.object_id)] = (
                frozenset(supported)
            )

        self._direct = (
            StaticMappingCatalog(self.mapping_id, specifications)
            if specifications
            else None
        )

    @property
    def direct_slot_support(
        self,
    ) -> Mapping[tuple[str, str], frozenset[RequiredSlot]]:
        return dict(self._direct_slots)

    def _fallback_catalog(self) -> CompileDBExtentCatalog:
        if self._fallback is None:
            self._fallback = CompileDBExtentCatalog(
                self._graph,
                self._tables,
                self._types,
                extent_sql_factory=self._extent_sql_factory,
                mapping_id=self.mapping_id,
            )
        return self._fallback

    def resolution_mode(
        self,
        binding: Binding,
        required_slots: frozenset[RequiredSlot],
    ) -> str:
        """Report which access path would be selected without building SQL."""
        key = (binding.kind, binding.object_id)
        if required_slots.issubset(
            self._direct_slots.get(key, frozenset())
        ):
            return "direct_physical"
        return "compatibility_extent"

    def resolve_access(
        self,
        binding: Binding,
        required_slots: frozenset[RequiredSlot],
    ) -> AccessPlan:
        if (
            self._direct is not None
            and self.resolution_mode(binding, required_slots) == "direct_physical"
        ):
            return self._direct.resolve_access(binding, required_slots)
        return self._fallback_catalog().resolve_access(binding, required_slots)


def mapping_catalog_from_dict(
    catalog: Mapping[str, Any],
) -> StaticMappingCatalog:
    """Load validated JSON metadata into the compiler's mapping objects."""

    validate_mapping_catalog(catalog)
    specifications = [
        _object_mapping_specification(mapping)
        for mapping in catalog["object_mappings"]
    ]
    return StaticMappingCatalog(catalog["mapping_id"], specifications)


def mapping_catalog_to_json(
    catalog: Mapping[str, Any],
    *,
    indent: int | None = 2,
) -> str:
    validate_mapping_catalog(catalog)
    return json.dumps(
        catalog,
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":") if indent is None else None,
    )


def mapping_catalog_from_json(payload: str) -> StaticMappingCatalog:
    parsed = json.loads(payload)
    if not isinstance(parsed, Mapping):
        raise CatalogValidationError("$: catalog must be a JSON object")
    return mapping_catalog_from_dict(parsed)


def write_mapping_catalog(
    path: str | Path,
    *,
    graph: Any,
    tables: Sequence[Sequence[Any]],
    types: Any,
    foreign_key_statements: Sequence[str] | None = None,
    extent_sql_factory: Callable[[Any], str] | None = None,
    mapping_id: str | None = None,
) -> dict[str, Any]:
    catalog = extract_mapping_catalog(
        graph,
        tables,
        types,
        foreign_key_statements=foreign_key_statements,
        extent_sql_factory=extent_sql_factory,
        mapping_id=mapping_id,
    )
    Path(path).write_text(mapping_catalog_to_json(catalog) + "\n", encoding="utf-8")
    return catalog


def load_mapping_catalog(path: str | Path) -> StaticMappingCatalog:
    return mapping_catalog_from_json(Path(path).read_text(encoding="utf-8"))


def _main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export the selected CompileDB physical mapping as query-compiler JSON"
        )
    )
    parser.add_argument("database", help="CompileDB PostgreSQL database name")
    parser.add_argument("output", help="Output mapping-catalog JSON file")
    args = parser.parse_args()

    # Lazy import keeps extraction/validation usable without PostgreSQL client
    # dependencies in unit tests and offline compiler tools.
    from helper_functions import load_data

    _, tables, types, graph = load_data(args.database)
    write_mapping_catalog(
        args.output,
        graph=graph,
        tables=tables,
        types=types,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "CATALOG_FORMAT_VERSION",
    "CatalogValidationError",
    "CompileDBHybridMappingCatalog",
    "DEFAULT_SCHEMA_FILE",
    "build_mapping_catalog",
    "extract_mapping_catalog",
    "load_mapping_catalog",
    "mapping_catalog_from_dict",
    "mapping_catalog_from_json",
    "mapping_catalog_to_json",
    "validate_mapping_catalog",
    "write_mapping_catalog",
]
