#!/usr/bin/env python3
"""Generate distinct, selectivity-aligned E/R SPJG query workloads.

This is the missing stage in the original workload pipeline.  The older
``generate_selectivity_aligned_query_workloads.py`` accepts one fixed template
workload and changes only predicate literals.  Consequently, changing its seed
does not create new query shapes.

This program instead performs both stages:

1. Generate new valid query shapes from the E/R graph.
2. Calibrate each generated WHERE predicate with the conceptual data profile.

Every candidate is parsed and bound by ``prepare_er_query`` before it is
accepted.  Canonical template fingerprints are used to reject duplicate query
shapes, including duplicates that differ only in literal values.
"""

from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
from dataclasses import dataclass
import hashlib
import importlib
import importlib.util
from itertools import combinations
import json
import random
import re
from pathlib import Path
import sys
import time
from typing import Any, Iterable, Mapping, Sequence

from compiledb_query_adapter import prepare_er_query
from er_query_rewriter import template_fingerprint
from data_profile import load_profile
import generate_selectivity_aligned_query_workloads as calibration_module
from generate_selectivity_aligned_query_workloads import (
    calibrate_query,
    literal_arguments,
    target_schedule,
)


_ORIGINAL_PROFILE_VALUES = calibration_module.profile_values
_ORIGINAL_CHOOSE_PREDICATE = calibration_module.choose_predicate


DEFAULT_CATEGORY_WEIGHTS = {
    "selection_projection": 30,
    "weak_owner": 20,
    "relationship_join": 20,
    "aggregation": 15,
    "complex_multi_join": 15,
}

SUBCLASS_ONLY_CATEGORY_WEIGHTS = {
    "selection_projection": 1,
    "weak_owner": 0,
    "relationship_join": 0,
    "aggregation": 0,
    "complex_multi_join": 0,
}

SUBCLASS_ONLY_MIN_SELECTIVITY = 0.50
SUBCLASS_ONLY_MAX_SELECTIVITY = 0.99


@dataclass(frozen=True)
class AttributeSpec:
    name: str
    type_name: str
    values: tuple[Any, ...]


@dataclass(frozen=True)
class EntitySpec:
    name: str
    object_id: str
    is_weak: bool
    owner_id: str | None
    is_subclass: bool
    is_leaf_subclass: bool
    parent_id: str | None
    hierarchy_depth: int
    attributes: tuple[AttributeSpec, ...]

    @property
    def usable(self) -> bool:
        return bool(self.attributes)


@dataclass(frozen=True)
class EndpointSpec:
    entity_id: str
    token: str


@dataclass(frozen=True)
class RelationshipSpec:
    name: str
    object_id: str
    left: EndpointSpec
    right: EndpointSpec

    @property
    def endpoints(self) -> tuple[EndpointSpec, EndpointSpec]:
        return self.left, self.right


@dataclass(frozen=True)
class RelationshipPath:
    first: RelationshipSpec
    left: EndpointSpec
    first_common: EndpointSpec
    second: RelationshipSpec
    second_common: EndpointSpec
    right: EndpointSpec


@dataclass(frozen=True)
class ConceptualCatalog:
    entities: Mapping[str, EntitySpec]
    strong_entities: tuple[EntitySpec, ...]
    weak_entities: tuple[EntitySpec, ...]
    descendants: Mapping[str, tuple[EntitySpec, ...]]
    relationships: tuple[RelationshipSpec, ...]
    relationship_paths: tuple[RelationshipPath, ...]


def _candidate_module_paths(module_name: str, roots: Iterable[Path]):
    seen = set()
    for root in roots:
        for path in [root / f"{module_name}.py", *sorted(root.glob(f"{module_name}(*)*.py"))]:
            resolved = path.resolve()
            if resolved not in seen and path.is_file():
                seen.add(resolved)
                yield path


def _load_project_module(module_name: str, roots: Sequence[Path]):
    # Prefer a module that belongs to this prototype.  Calling
    # import_module() first is incorrect when the repository's parent
    # directory contains an older module with the same name: Python then
    # imports (for example) ../sql_analyzer.py instead of the prototype's
    # sql_analyzer(1).py compatibility file.
    for path in _candidate_module_paths(module_name, roots):
        loaded = sys.modules.get(module_name)
        loaded_path = getattr(loaded, "__file__", None)
        if loaded_path is not None:
            try:
                if Path(loaded_path).resolve() == path.resolve():
                    return loaded
            except OSError:
                pass
        specification = importlib.util.spec_from_file_location(module_name, path)
        if specification is None or specification.loader is None:
            continue
        module = importlib.util.module_from_spec(specification)
        sys.modules[module_name] = module
        specification.loader.exec_module(module)
        return module

    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        if error.name != module_name:
            raise
    raise ModuleNotFoundError(
        f"cannot locate {module_name}.py in: "
        + ", ".join(str(root) for root in roots)
    )


def load_er_graph(schema_path: Path):
    """Load the project's Graph without depending on a physical mapping."""

    schema_path = Path(schema_path).resolve()
    roots = tuple(dict.fromkeys((
        Path.cwd().resolve(),
        schema_path.parent,
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent,
        (Path.cwd() / "upload").resolve(),
    )))
    for root in reversed(roots):
        if root.is_dir() and str(root) not in sys.path:
            sys.path.insert(0, str(root))

    sql_analyzer = _load_project_module("sql_analyzer", roots)
    er_graph = _load_project_module("er_graph", roots)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    graph = er_graph.Graph()
    for statement in schema["create_entity_statements"]:
        graph.add_entity(_analyze_entity_ddl(sql_analyzer, statement))
    for statement in schema["create_relationship_statements"]:
        graph.add_relationship(_analyze_relationship_ddl(sql_analyzer, statement))
    return graph


def _parse_scalar(value, default=None):
    """Accept both old ParseResults fields and newer scalar result names."""

    if value is None or value == "":
        return default
    if isinstance(value, str):
        return value
    try:
        items = list(value)
    except TypeError:
        return value
    if not items:
        return default
    current = items[0]
    while not isinstance(current, str):
        try:
            nested = list(current)
        except TypeError:
            break
        if not nested:
            return default
        current = nested[0]
    return current


def _analyzed_attributes(sql_analyzer, parsed):
    attributes = getattr(parsed, "attributes", ())
    if attributes is None or attributes == "":
        return []
    return [sql_analyzer.analyze_attribute(attribute) for attribute in attributes]


def _analyze_entity_ddl(sql_analyzer, statement: str):
    """Convert CREATE ENTITY DDL without relying on fragile result indexing.

    Some project revisions return ``parent_entity`` as ``"Product"`` while
    others return ``ParseResults(["Product"])``.  The historical analyzer
    unconditionally used ``parent_entity[0]``, turning the scalar form into
    ``"P"`` and raising IndexError when the value was empty.  Entity kind and
    parent are unambiguous in the original DDL, so derive them there.
    """

    parsed = sql_analyzer.parse(statement)
    header = re.match(
        r"^\s*CREATE\s+(?:(WEAK)\s+)?ENTITY\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)",
        statement,
        re.IGNORECASE,
    )
    if header is None:
        raise ValueError(f"invalid CREATE ENTITY statement: {statement}")

    weak_marker, table_name = header.groups()
    subclass = re.search(
        r"\bSUBCLASS\s+OF\s+([A-Za-z_][A-Za-z0-9_]*)",
        statement,
        re.IGNORECASE,
    )
    weak_parent = re.search(
        r"\bDEPENDS\s+ON\s+([A-Za-z_][A-Za-z0-9_]*)",
        statement,
        re.IGNORECASE,
    )

    if weak_marker:
        entity_type = sql_analyzer.EntityType.WEAK
        if weak_parent is None:
            raise ValueError(f"weak entity has no DEPENDS ON parent: {statement}")
        parent_entity = weak_parent.group(1)
    elif subclass is not None:
        entity_type = sql_analyzer.EntityType.SUBCLASS
        parent_entity = subclass.group(1)
    else:
        entity_type = sql_analyzer.EntityType.REGULAR
        parent_entity = None

    result = {
        "entity_type": entity_type,
        "table_name": table_name,
        "attributes": _analyzed_attributes(sql_analyzer, parsed),
    }
    if parent_entity is not None:
        result["parent_entity"] = parent_entity
    if entity_type == sql_analyzer.EntityType.SUBCLASS:
        participation = re.search(
            r"\bSUBCLASS\s+OF\s+[A-Za-z_][A-Za-z0-9_]*\s*"
            r"(?:\(\s*(TOTAL|PARTIAL)\s*\))?",
            statement,
            re.IGNORECASE,
        )
        # Preserve the project's historical default: omitted means TOTAL.
        participation_value = (
            participation.group(1).upper()
            if participation is not None and participation.group(1)
            else "TOTAL"
        )
        result["total"] = participation_value == "TOTAL"
    return result


def _relationship_endpoint(modifier, entity_name: str):
    cardinality = str(
        _parse_scalar(modifier.get("cardinality", "ONE"), "ONE")
    ).upper()
    participation = str(
        _parse_scalar(modifier.get("participation", "TOTAL"), "TOTAL")
    ).upper()
    role = _parse_scalar(modifier.get("role", None), None)
    return {
        "name": entity_name,
        "one": cardinality == "ONE",
        "total": participation == "TOTAL",
        "role": role,
    }


def _analyze_relationship_ddl(sql_analyzer, statement: str):
    """Convert CREATE RELATIONSHIP across scalar/list parser revisions."""

    parsed = sql_analyzer.parse(statement)
    header = re.match(
        r"^\s*CREATE\s+RELATIONSHIP\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)",
        statement,
        re.IGNORECASE,
    )
    if header is None:
        raise ValueError(f"invalid CREATE RELATIONSHIP statement: {statement}")

    entity1_name = str(_parse_scalar(parsed.entity1))
    entity2_name = str(_parse_scalar(parsed.entity2))
    return {
        "table_name": header.group(1),
        "entity1": _relationship_endpoint(
            parsed.entity1_modifier,
            entity1_name,
        ),
        "entity2": _relationship_endpoint(
            parsed.entity2_modifier,
            entity2_name,
        ),
        "attributes": _analyzed_attributes(sql_analyzer, parsed),
    }


def _entity_attributes(entity_node) -> list[Any]:
    """Return attributes accessible through an entity binding.

    A strong subclass exposes inherited attributes.  A weak entity does not
    inherit its owner's attributes; those are accessed through an OWNER join.
    """

    result = []
    current = entity_node
    while current is not None:
        result.extend(getattr(current, "attributes", ()))
        if getattr(entity_node, "is_weak_entity", False):
            break
        if not getattr(current, "is_subclass", False):
            break
        current = getattr(current, "parent_entity", None)
    return result


def _profile_scalar_values(profile, object_id: str, attribute_name: str):
    object_profile = profile.get("objects", {}).get(object_id.lower())
    if object_profile is None:
        return ()
    wanted = attribute_name.lower()
    result = []
    for row in object_profile.get("rows", ()):
        for name, value in row.items():
            if str(name).lower() != wanted:
                continue
            if isinstance(value, (list, dict)):
                break
            result.append(value)
            break
    return tuple(result) if any(value is not None for value in result) else ()


def build_catalog(graph, profile) -> ConceptualCatalog:
    entities: dict[str, EntitySpec] = {}

    for node in graph.nodes:
        if not hasattr(node, "entity_dict"):
            continue
        object_id = str(node.unique_name).lower()
        attributes = []
        seen_names = set()
        for attribute in _entity_attributes(node):
            name = str(attribute.name)
            lowered = name.lower()
            if lowered in seen_names:
                continue
            seen_names.add(lowered)
            if getattr(attribute, "is_composite", False):
                continue
            if getattr(attribute, "is_multivalued", False):
                continue
            values = _profile_scalar_values(profile, object_id, name)
            if not values:
                continue
            attributes.append(AttributeSpec(
                name=name,
                type_name=str(getattr(attribute, "attr_type", "VARCHAR")),
                values=values,
            ))

        parent = getattr(node, "parent_entity", None)
        is_weak = bool(getattr(node, "is_weak_entity", False))
        is_subclass = bool(getattr(node, "is_subclass", False))
        is_leaf_subclass = is_subclass and not bool(
            getattr(node, "children", ())
        )
        hierarchy_depth = 0
        ancestor = node
        while getattr(ancestor, "is_subclass", False):
            hierarchy_depth += 1
            ancestor = getattr(ancestor, "parent_entity", None)
            if ancestor is None:
                break
        entities[object_id] = EntitySpec(
            name=str(node.name),
            object_id=object_id,
            is_weak=is_weak,
            owner_id=(
                str(parent.unique_name).lower()
                if parent is not None and is_weak
                else None
            ),
            is_subclass=is_subclass,
            is_leaf_subclass=is_leaf_subclass,
            parent_id=(
                str(parent.unique_name).lower()
                if parent is not None and is_subclass
                else None
            ),
            hierarchy_depth=hierarchy_depth,
            attributes=tuple(attributes),
        )

    relationships = []
    for node in graph.nodes:
        if not hasattr(node, "rel_dict"):
            continue
        relation = node.rel_dict
        left_data = relation["entity1"]
        right_data = relation["entity2"]
        left_id = str(left_data["name"]).lower()
        right_id = str(right_data["name"]).lower()
        if left_id not in entities or right_id not in entities:
            continue
        if not entities[left_id].usable or not entities[right_id].usable:
            continue
        relationships.append(RelationshipSpec(
            name=str(node.name),
            object_id=str(node.unique_name).lower(),
            left=EndpointSpec(left_id, str(left_data.get("role") or left_data["name"])),
            right=EndpointSpec(right_id, str(right_data.get("role") or right_data["name"])),
        ))

    paths = []
    for first in relationships:
        for second in relationships:
            if first.object_id == second.object_id:
                continue
            for first_index, first_common in enumerate(first.endpoints):
                for second_index, second_common in enumerate(second.endpoints):
                    if first_common.entity_id != second_common.entity_id:
                        continue
                    paths.append(RelationshipPath(
                        first=first,
                        left=first.endpoints[1 - first_index],
                        first_common=first_common,
                        second=second,
                        second_common=second_common,
                        right=second.endpoints[1 - second_index],
                    ))

    strong = tuple(
        entity for entity in entities.values()
        if not entity.is_weak and entity.usable
    )
    weak = tuple(
        entity for entity in entities.values()
        if entity.is_weak and entity.usable and entity.owner_id in entities
        and entities[entity.owner_id].usable
    )
    descendants: dict[str, list[EntitySpec]] = {
        entity_id: [] for entity_id in entities
    }
    for entity in strong:
        parent_id = entity.parent_id
        while parent_id is not None:
            descendants[parent_id].append(entity)
            parent_id = entities[parent_id].parent_id
    if not strong:
        raise ValueError("the profile has no usable strong-entity attributes")
    if not weak:
        raise ValueError("the profile has no usable weak-entity attributes")
    if not relationships:
        raise ValueError("the graph has no usable relationship paths")
    if not paths:
        raise ValueError("the graph has no connected two-relationship paths")

    return ConceptualCatalog(
        entities=entities,
        strong_entities=strong,
        weak_entities=weak,
        descendants={
            entity_id: tuple(values)
            for entity_id, values in descendants.items()
        },
        relationships=tuple(relationships),
        relationship_paths=tuple(paths),
    )


@dataclass
class _ValueStatistics:
    values: tuple[Any, ...]

    def __post_init__(self):
        self.non_null = tuple(value for value in self.values if value is not None)
        self.total = len(self.values)
        self.sorted_values = tuple(sorted(self.non_null))
        frequencies = {}
        for value in self.non_null:
            frequencies[value] = frequencies.get(value, 0) + 1
        self.frequencies = frequencies


class FastProfileIndex:
    """Cache profile columns and choose thresholds without quadratic scans."""

    def __init__(self, profile, catalog: ConceptualCatalog):
        self.profile = profile
        self.columns = {}
        self.statistics_by_identity = {}
        for entity in catalog.entities.values():
            for attribute in entity.attributes:
                key = (entity.object_id.lower(), attribute.name.lower())
                self.columns[key] = attribute.values

    def profile_values(self, _profile, object_name, attribute_name):
        key = (str(object_name).lower(), str(attribute_name).lower())
        values = self.columns.get(key)
        if values is None:
            values = tuple(
                _ORIGINAL_PROFILE_VALUES(
                    self.profile,
                    object_name,
                    attribute_name,
                )
            )
            self.columns[key] = values
        if not values:
            raise KeyError(
                f"profile has no scalar values for {object_name}.{attribute_name}"
            )
        return values

    def _statistics(self, values):
        identity = id(values)
        statistics = self.statistics_by_identity.get(identity)
        if statistics is None:
            statistics = _ValueStatistics(tuple(values))
            if not statistics.non_null:
                raise ValueError("cannot calibrate from an all-NULL sample")
            self.statistics_by_identity[identity] = statistics
        return statistics

    @staticmethod
    def _range_selectivity(statistics, operator, candidate):
        ordered = statistics.sorted_values
        if operator == "<":
            matches = bisect_left(ordered, candidate)
        elif operator == "<=":
            matches = bisect_right(ordered, candidate)
        elif operator == ">":
            matches = len(ordered) - bisect_right(ordered, candidate)
        elif operator == ">=":
            matches = len(ordered) - bisect_left(ordered, candidate)
        else:
            raise ValueError(f"not a range operator: {operator}")
        return matches / statistics.total

    def _range_candidates(self, statistics, operator, target):
        ordered = statistics.sorted_values
        non_null_count = len(ordered)
        wanted_matches = target * statistics.total
        pivot = (
            wanted_matches
            if operator in {"<", "<="}
            else non_null_count - wanted_matches
        )
        indexes = {0, non_null_count - 1}
        center = int(round(pivot))
        for offset in range(-3, 4):
            index = center + offset
            if 0 <= index < non_null_count:
                indexes.add(index)

        # Include the neighboring distinct values when the pivot falls inside
        # a large duplicate-value run.
        expanded = set(indexes)
        for index in tuple(indexes):
            value = ordered[index]
            left = bisect_left(ordered, value)
            right = bisect_right(ordered, value)
            for neighbor in (left - 1, left, right - 1, right):
                if 0 <= neighbor < non_null_count:
                    expanded.add(neighbor)
        return {ordered[index] for index in expanded}

    def choose_predicate(self, values, operator, target, *, in_value_count=None):
        operator = operator.upper()
        statistics = self._statistics(values)

        if operator in {"<", "<=", ">", ">="}:
            candidates = self._range_candidates(statistics, operator, target)
            selected = min(
                candidates,
                key=lambda candidate: (
                    abs(
                        self._range_selectivity(statistics, operator, candidate)
                        - target
                    ),
                    repr(candidate),
                ),
            )
            return selected, self._range_selectivity(
                statistics,
                operator,
                selected,
            )

        if operator in {"=", "!=", "<>"}:
            def equality_selectivity(candidate):
                equal = statistics.frequencies[candidate]
                matches = equal if operator == "=" else len(statistics.non_null) - equal
                return matches / statistics.total

            selected = min(
                statistics.frequencies,
                key=lambda candidate: (
                    abs(equality_selectivity(candidate) - target),
                    repr(candidate),
                ),
            )
            return selected, equality_selectivity(selected)

        if operator in {"IN", "NOT IN"}:
            count = max(1, int(in_value_count or 1))
            ranked = sorted(
                statistics.frequencies,
                key=lambda value: (-statistics.frequencies[value], repr(value)),
            )
            count = min(count, len(ranked))
            if len(ranked) <= 16:
                choices = combinations(ranked, count)
            else:
                pool = ranked[:max(32, count)]
                choices = (
                    tuple(pool[offset:offset + count])
                    for offset in range(len(pool) - count + 1)
                )

            def membership_selectivity(choice):
                selected_count = sum(
                    statistics.frequencies[value] for value in choice
                )
                matches = (
                    selected_count
                    if operator == "IN"
                    else len(statistics.non_null) - selected_count
                )
                return matches / statistics.total

            selected = min(
                choices,
                key=lambda choice: (
                    abs(membership_selectivity(choice) - target),
                    repr(choice),
                ),
            )
            return selected, membership_selectivity(selected)

        return _ORIGINAL_CHOOSE_PREDICATE(
            values,
            operator,
            target,
            in_value_count=in_value_count,
        )

    def install(self):
        # calibrate_query resolves these names in its defining module.  The
        # replacement remains process-local and leaves the source module
        # unchanged on disk.
        calibration_module.profile_values = self.profile_values
        calibration_module.choose_predicate = self.choose_predicate


def _qualified(alias: str, attribute: AttributeSpec) -> str:
    return f"{alias}.{attribute.name}"


def _choose_attributes(
    rng: random.Random,
    entity: EntitySpec,
    minimum: int = 1,
    maximum: int = 3,
) -> list[AttributeSpec]:
    count = rng.randint(minimum, min(maximum, len(entity.attributes)))
    return rng.sample(list(entity.attributes), count)


def _placeholder(attribute: AttributeSpec) -> str:
    example = next(value for value in attribute.values if value is not None)
    if isinstance(example, bool):
        return "1"
    if isinstance(example, (int, float)):
        return "0"
    return "''"


def _predicate(
    rng: random.Random,
    alias: str,
    entity: EntitySpec,
) -> str:
    attribute = rng.choice(entity.attributes)
    operator = rng.choice(("<", "<=", ">", ">="))
    return f"{_qualified(alias, attribute)} {operator} {_placeholder(attribute)}"


def _weighted_choice(
    rng: random.Random,
    values: Sequence[Any],
    weights: Sequence[float],
):
    if not values:
        raise ValueError("cannot choose from an empty sequence")
    return rng.choices(values, weights=weights, k=1)[0]


class ShapeGenerator:
    def __init__(
        self,
        catalog: ConceptualCatalog,
        *,
        subclass_weight: float = 1.0,
        leaf_subclass_weight: float | None = None,
        leaf_relationship_weight: float = 1.0,
        endpoint_subclass_probability: float = 0.0,
        hub_penalty: float = 0.0,
        subclass_only: bool = False,
    ):
        self.catalog = catalog
        self.subclass_weight = subclass_weight
        self.leaf_subclass_weight = (
            subclass_weight
            if leaf_subclass_weight is None
            else leaf_subclass_weight
        )
        self.leaf_relationship_weight = leaf_relationship_weight
        self.endpoint_subclass_probability = endpoint_subclass_probability
        self.hub_penalty = hub_penalty
        self.subclass_only = subclass_only

        self._selection_entities = tuple(
            entity
            for entity in catalog.strong_entities
            if not subclass_only or entity.is_subclass
        )
        if not self._selection_entities:
            raise ValueError(
                "subclass-only mode requires at least one usable strong subclass"
            )

        self._strong_weights = tuple(
            (
                self.leaf_subclass_weight
                if entity.is_leaf_subclass
                else subclass_weight if entity.is_subclass else 1.0
            )
            for entity in self._selection_entities
        )
        endpoint_degrees = {entity_id: 0 for entity_id in catalog.entities}
        for relationship in catalog.relationships:
            endpoint_degrees[relationship.left.entity_id] += 1
            endpoint_degrees[relationship.right.entity_id] += 1
        self._endpoint_degrees = endpoint_degrees
        def relationship_leaf_multiplier(relationship: RelationshipSpec) -> float:
            has_leaf_endpoint = any(
                catalog.entities[endpoint.entity_id].is_leaf_subclass
                for endpoint in relationship.endpoints
            )
            return leaf_relationship_weight if has_leaf_endpoint else 1.0

        self._relationship_leaf_multiplier = {
            relationship.object_id: relationship_leaf_multiplier(relationship)
            for relationship in catalog.relationships
        }
        self._relationship_weights = tuple(
            (
                endpoint_degrees[relationship.left.entity_id]
                * endpoint_degrees[relationship.right.entity_id]
            ) ** (-0.5 * hub_penalty)
            * self._relationship_leaf_multiplier[relationship.object_id]
            for relationship in catalog.relationships
        )
        self._path_weights = tuple(
            max(
                endpoint_degrees[path.first_common.entity_id]
                * (endpoint_degrees[path.first_common.entity_id] - 1),
                1,
            ) ** (-hub_penalty)
            * self._relationship_leaf_multiplier[path.first.object_id]
            * self._relationship_leaf_multiplier[path.second.object_id]
            for path in catalog.relationship_paths
        )

    def _choose_strong_entity(self, rng: random.Random) -> EntitySpec:
        if all(weight == 1.0 for weight in self._strong_weights):
            return rng.choice(self._selection_entities)
        return _weighted_choice(
            rng,
            self._selection_entities,
            self._strong_weights,
        )

    def _choose_relationship(self, rng: random.Random) -> RelationshipSpec:
        if self.hub_penalty == 0.0 and self.leaf_relationship_weight == 1.0:
            return rng.choice(self.catalog.relationships)
        return _weighted_choice(
            rng,
            self.catalog.relationships,
            self._relationship_weights,
        )

    def _choose_relationship_path(self, rng: random.Random) -> RelationshipPath:
        if self.hub_penalty == 0.0 and self.leaf_relationship_weight == 1.0:
            return rng.choice(self.catalog.relationship_paths)
        return _weighted_choice(
            rng,
            self.catalog.relationship_paths,
            self._path_weights,
        )

    def _specialize_entity(
        self,
        entity: EntitySpec,
        rng: random.Random,
    ) -> EntitySpec:
        """Optionally bind a root-typed reference to one usable descendant.

        ENDPOINT tokens continue to name the relationship's declared endpoint.
        Only the joined entity changes.  For example, a Product endpoint may
        be joined to Phone because REF(Phone) has Product's root identity type.
        """

        candidates = self.catalog.descendants.get(entity.object_id, ())
        if not candidates or self.endpoint_subclass_probability <= 0.0:
            return entity
        if (
            self.endpoint_subclass_probability < 1.0
            and rng.random() >= self.endpoint_subclass_probability
        ):
            return entity
        weights = tuple(
            self.leaf_subclass_weight
            if candidate.is_leaf_subclass
            else self.subclass_weight
            for candidate in candidates
        )
        if all(weight == 1.0 for weight in weights):
            return rng.choice(candidates)
        return _weighted_choice(rng, candidates, weights)

    def selection_projection(self, rng: random.Random) -> str:
        entity = self._choose_strong_entity(rng)
        projected = _choose_attributes(rng, entity, 1, 4)
        select = ", ".join(_qualified("e", attribute) for attribute in projected)
        distinct = "DISTINCT " if rng.random() < 0.15 else ""
        return (
            f"SELECT {distinct}{select} FROM {entity.name} e "
            f"WHERE {_predicate(rng, 'e', entity)};"
        )

    def weak_owner(self, rng: random.Random) -> str:
        weak = rng.choice(self.catalog.weak_entities)
        owner = self.catalog.entities[weak.owner_id]
        weak_attributes = _choose_attributes(rng, weak, 1, 3)
        join_owner = rng.random() < 0.75
        if join_owner:
            owner = self._specialize_entity(owner, rng)
        projected = [_qualified("w", attribute) for attribute in weak_attributes]
        if join_owner:
            projected.extend(
                _qualified("o", attribute)
                for attribute in _choose_attributes(rng, owner, 1, 2)
            )
        predicate_entity, predicate_alias = (
            (owner, "o")
            if join_owner and rng.random() < 0.5
            else (weak, "w")
        )
        from_sql = f"FROM {weak.name} w"
        if join_owner:
            from_sql += f" JOIN {owner.name} o ON OWNER(w) = REF(o)"
        return (
            f"SELECT {', '.join(projected)} {from_sql} "
            f"WHERE {_predicate(rng, predicate_alias, predicate_entity)};"
        )

    def _relationship_from(
        self,
        relationship: RelationshipSpec,
        rng: random.Random,
    ):
        left = self._specialize_entity(
            self.catalog.entities[relationship.left.entity_id],
            rng,
        )
        right = self._specialize_entity(
            self.catalog.entities[relationship.right.entity_id],
            rng,
        )
        return (
            f"FROM {relationship.name} r "
            f"JOIN {left.name} e1 ON ENDPOINT(r, {relationship.left.token}) = REF(e1) "
            f"JOIN {right.name} e2 ON ENDPOINT(r, {relationship.right.token}) = REF(e2)",
            left,
            right,
        )

    def relationship_join(self, rng: random.Random) -> str:
        relationship = self._choose_relationship(rng)
        from_sql, left, right = self._relationship_from(relationship, rng)
        projected = [
            *(_qualified("e1", attribute) for attribute in _choose_attributes(rng, left, 1, 2)),
            *(_qualified("e2", attribute) for attribute in _choose_attributes(rng, right, 1, 2)),
        ]
        predicate_entity, predicate_alias = rng.choice(((left, "e1"), (right, "e2")))
        return (
            f"SELECT {', '.join(projected)} {from_sql} "
            f"WHERE {_predicate(rng, predicate_alias, predicate_entity)};"
        )

    def aggregation(self, rng: random.Random) -> str:
        relationship = self._choose_relationship(rng)
        from_sql, left, right = self._relationship_from(relationship, rng)
        if rng.random() < 0.5:
            group_entity, group_alias = left, "e1"
            counted_alias = "e2"
        else:
            group_entity, group_alias = right, "e2"
            counted_alias = "e1"
        group_attribute = rng.choice(group_entity.attributes)
        predicate_entity, predicate_alias = rng.choice(((left, "e1"), (right, "e2")))
        threshold = rng.randint(1, 5)
        return (
            f"SELECT {_qualified(group_alias, group_attribute)}, "
            f"COUNT(DISTINCT REF({counted_alias})) AS related_count "
            f"{from_sql} WHERE {_predicate(rng, predicate_alias, predicate_entity)} "
            f"GROUP BY REF({group_alias}), {_qualified(group_alias, group_attribute)} "
            f"HAVING COUNT(DISTINCT REF({counted_alias})) >= {threshold};"
        )

    def complex_multi_join(self, rng: random.Random) -> str:
        path = self._choose_relationship_path(rng)
        left = self._specialize_entity(
            self.catalog.entities[path.left.entity_id],
            rng,
        )
        # Both relationships must use the same specialized common binding.
        common = self._specialize_entity(
            self.catalog.entities[path.first_common.entity_id],
            rng,
        )
        right = self._specialize_entity(
            self.catalog.entities[path.right.entity_id],
            rng,
        )
        from_sql = (
            f"FROM {path.first.name} r1 "
            f"JOIN {left.name} e1 ON ENDPOINT(r1, {path.left.token}) = REF(e1) "
            f"JOIN {common.name} e2 ON ENDPOINT(r1, {path.first_common.token}) = REF(e2) "
            f"JOIN {path.second.name} r2 "
            f"ON ENDPOINT(r2, {path.second_common.token}) = REF(e2) "
            f"JOIN {right.name} e3 ON ENDPOINT(r2, {path.right.token}) = REF(e3)"
        )
        predicate_entity, predicate_alias = rng.choice(
            ((left, "e1"), (common, "e2"), (right, "e3"))
        )
        where_sql = _predicate(rng, predicate_alias, predicate_entity)

        if rng.random() < 0.30:
            group_attribute = rng.choice(common.attributes)
            return (
                f"SELECT {_qualified('e2', group_attribute)}, "
                f"COUNT(DISTINCT REF(e3)) AS related_count {from_sql} "
                f"WHERE {where_sql} "
                f"GROUP BY REF(e2), {_qualified('e2', group_attribute)} "
                f"HAVING COUNT(DISTINCT REF(e3)) >= {rng.randint(1, 5)};"
            )

        projected = [
            _qualified("e1", rng.choice(left.attributes)),
            _qualified("e2", rng.choice(common.attributes)),
            _qualified("e3", rng.choice(right.attributes)),
        ]
        return f"SELECT {', '.join(projected)} {from_sql} WHERE {where_sql};"

    def generate(self, category: str, rng: random.Random) -> str:
        method = getattr(self, category, None)
        if method is None:
            raise ValueError(f"unsupported category {category!r}")
        return method(rng)


def _apportion(query_count: int, weights: Mapping[str, float]) -> dict[str, int]:
    total = sum(weights.values())
    if query_count < 1 or total <= 0:
        raise ValueError("query count and category weights must be positive")
    exact = {name: query_count * weight / total for name, weight in weights.items()}
    counts = {name: int(value) for name, value in exact.items()}
    remaining = query_count - sum(counts.values())
    order = sorted(weights, key=lambda name: (exact[name] - counts[name], name), reverse=True)
    for name in order[:remaining]:
        counts[name] += 1
    return counts


def _category_schedule(query_count: int, weights: Mapping[str, float], seed: int):
    counts = _apportion(query_count, weights)
    schedule = [category for category, count in counts.items() for _ in range(count)]
    random.Random(seed).shuffle(schedule)
    return schedule, counts


def parse_category_weights(text: str) -> dict[str, float]:
    result = {}
    for item in text.split(","):
        name, separator, value = item.strip().partition("=")
        if not separator or not name:
            raise ValueError(
                "category mix must use category=weight comma-separated entries"
            )
        result[name] = float(value)
    unknown = set(result) - set(DEFAULT_CATEGORY_WEIGHTS)
    if unknown:
        raise ValueError(f"unsupported categories: {sorted(unknown)}")
    if set(result) != set(DEFAULT_CATEGORY_WEIGHTS):
        missing = set(DEFAULT_CATEGORY_WEIGHTS) - set(result)
        raise ValueError(f"category mix is missing: {sorted(missing)}")
    return result


def generate_schema_driven_workloads(
    schema_path: Path,
    profile_path: Path,
    output_directory: Path,
    *,
    workload_count: int = 10,
    queries_per_workload: int = 100,
    targets: Sequence[float] = (0.01, 0.05, 0.10, 0.25, 0.50),
    seed: int = 1,
    category_weights: Mapping[str, float] = DEFAULT_CATEGORY_WEIGHTS,
    subclass_weight: float = 1.0,
    leaf_subclass_weight: float | None = None,
    leaf_relationship_weight: float = 1.0,
    endpoint_subclass_probability: float = 0.0,
    hub_penalty: float = 0.0,
    subclass_only: bool = False,
    reject_cross_workload_duplicates: bool = True,
    max_attempts_per_query: int = 2_000,
    progress_every: int = 0,
):
    started_at = time.perf_counter()
    schema_path = Path(schema_path)
    profile_path = Path(profile_path)
    output_directory = Path(output_directory)
    if workload_count < 1:
        raise ValueError("workload count must be positive")
    if queries_per_workload < 1:
        raise ValueError("queries per workload must be positive")
    if not targets or any(not 0.0 <= value <= 1.0 for value in targets):
        raise ValueError("every selectivity target must be between 0 and 1")
    if progress_every < 0:
        raise ValueError("progress interval cannot be negative")
    if subclass_weight <= 0:
        raise ValueError("subclass weight must be greater than zero")
    if leaf_subclass_weight is not None and leaf_subclass_weight <= 0:
        raise ValueError("leaf subclass weight must be greater than zero")
    if leaf_relationship_weight <= 0:
        raise ValueError("leaf relationship weight must be greater than zero")
    if not 0.0 <= endpoint_subclass_probability <= 1.0:
        raise ValueError(
            "endpoint subclass probability must be between zero and one"
        )
    if hub_penalty < 0:
        raise ValueError("hub penalty cannot be negative")
    if subclass_only:
        invalid_targets = [
            value
            for value in targets
            if not (
                SUBCLASS_ONLY_MIN_SELECTIVITY
                <= value
                <= SUBCLASS_ONLY_MAX_SELECTIVITY
            )
        ]
        if invalid_targets:
            raise ValueError(
                "subclass-only selectivity targets must be between "
                f"{SUBCLASS_ONLY_MIN_SELECTIVITY:.2f} and "
                f"{SUBCLASS_ONLY_MAX_SELECTIVITY:.2f}; got "
                f"{invalid_targets}"
            )
        category_weights = SUBCLASS_ONLY_CATEGORY_WEIGHTS

    schema_bytes = schema_path.read_bytes()
    schema_hash = hashlib.sha256(schema_bytes).hexdigest()
    profile_bytes = profile_path.read_bytes()
    profile_hash = hashlib.sha256(profile_bytes).hexdigest()
    if progress_every:
        print(f"Reading {profile_path}...", flush=True)
    profile = load_profile(profile_path)
    if profile.get("schema_sha256") != schema_hash:
        raise ValueError(
            "schema/profile hash mismatch; regenerate conceptual_data_profile.json "
            "from this exact schema file"
        )

    if progress_every:
        print(
            f"Loaded profile; constructing the E/R graph from {schema_path.name}...",
            flush=True,
        )
    graph = load_er_graph(schema_path)
    catalog = build_catalog(graph, profile)
    leaf_subclass_ids = {
        entity.object_id
        for entity in catalog.strong_entities
        if entity.is_leaf_subclass
    }
    leaf_relationship_ids = {
        relationship.object_id
        for relationship in catalog.relationships
        if any(
            catalog.entities[endpoint.entity_id].is_leaf_subclass
            for endpoint in relationship.endpoints
        )
    }
    fast_profile_index = FastProfileIndex(profile, catalog)
    fast_profile_index.install()
    shape_generator = ShapeGenerator(
        catalog,
        subclass_weight=subclass_weight,
        leaf_subclass_weight=leaf_subclass_weight,
        leaf_relationship_weight=leaf_relationship_weight,
        endpoint_subclass_probability=endpoint_subclass_probability,
        hub_penalty=hub_penalty,
        subclass_only=subclass_only,
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    if progress_every:
        print(
            "Graph ready: "
            f"{len(catalog.strong_entities)} strong entities, "
            f"{len(catalog.weak_entities)} weak entities, "
            f"{len(catalog.relationships)} relationships. ",
            "Generating workloads...",
            sep="",
            flush=True,
        )

    global_fingerprints: set[str] = set()
    output_paths = []
    for workload_number in range(1, workload_count + 1):
        workload_started_at = time.perf_counter()
        workload_seed = seed + workload_number - 1
        rng = random.Random(workload_seed)
        categories, category_counts = _category_schedule(
            queries_per_workload,
            category_weights,
            workload_seed * 104_729 + 11,
        )
        targets_for_queries = target_schedule(
            queries_per_workload,
            list(targets),
            workload_seed * 130_363 + 17,
        )
        local_fingerprints: set[str] = set()
        queries = []
        errors = []
        structural_access_counts = Counter()

        for index, (category, target) in enumerate(
            zip(categories, targets_for_queries), 1
        ):
            last_error = None
            for _attempt in range(max_attempts_per_query):
                candidate = shape_generator.generate(category, rng)
                try:
                    calibrated_sql, selectivity = calibrate_query(
                        candidate,
                        profile,
                        target,
                    )
                    prepared = prepare_er_query(calibrated_sql, graph)
                    fingerprint = template_fingerprint(prepared.template)
                except (KeyError, TypeError, ValueError) as error:
                    last_error = error
                    continue

                if subclass_only:
                    estimated = selectivity.get("estimated_selectivity")
                    if (
                        estimated is None
                        or not (
                            SUBCLASS_ONLY_MIN_SELECTIVITY
                            <= float(estimated)
                            <= SUBCLASS_ONLY_MAX_SELECTIVITY
                        )
                    ):
                        last_error = ValueError(
                            "calibrated selectivity is outside the required "
                            f"[{SUBCLASS_ONLY_MIN_SELECTIVITY:.2f}, "
                            f"{SUBCLASS_ONLY_MAX_SELECTIVITY:.2f}] range: "
                            f"{estimated!r}"
                        )
                        continue
                    bindings = prepared.template.bindings
                    if len(bindings) != 1:
                        last_error = ValueError(
                            "subclass-only query has more than one conceptual binding"
                        )
                        continue
                    entity = catalog.entities.get(bindings[0].object_id)
                    if (
                        bindings[0].kind != "entity"
                        or entity is None
                        or not entity.is_subclass
                    ):
                        last_error = ValueError(
                            "subclass-only query did not bind one strong subclass"
                        )
                        continue

                if fingerprint in local_fingerprints:
                    continue
                if reject_cross_workload_duplicates and fingerprint in global_fingerprints:
                    continue

                local_fingerprints.add(fingerprint)
                global_fingerprints.add(fingerprint)
                bound_object_ids = [
                    binding.object_id
                    for binding in prepared.template.bindings
                ]
                leaf_entity_bindings = sum(
                    object_id in leaf_subclass_ids
                    for object_id in bound_object_ids
                )
                leaf_relationship_bindings = sum(
                    object_id in leaf_relationship_ids
                    for object_id in bound_object_ids
                )
                structural_access_counts["leaf_entity_bindings"] += (
                    leaf_entity_bindings
                )
                structural_access_counts["leaf_relationship_bindings"] += (
                    leaf_relationship_bindings
                )
                if leaf_entity_bindings:
                    structural_access_counts["queries_with_leaf_entity"] += 1
                if leaf_relationship_bindings:
                    structural_access_counts[
                        "queries_with_leaf_endpoint_relationship"
                    ] += 1
                if selectivity.get("absolute_error") is not None:
                    errors.append(selectivity["absolute_error"])
                queries.append({
                    "id": f"Q{index:03d}",
                    "category": category,
                    "frequency": 1,
                    "sql": calibrated_sql,
                    "canonical_template_hash": fingerprint,
                    "literal_arguments": literal_arguments(calibrated_sql),
                    "selectivity": selectivity,
                })
                if progress_every and (
                    index % progress_every == 0
                    or index == queries_per_workload
                ):
                    print(
                        f"[workload {workload_number:02d}/{workload_count:02d}] "
                        f"accepted {index:03d}/{queries_per_workload:03d} queries",
                        flush=True,
                    )
                break
            else:
                detail = f": {last_error}" if last_error is not None else ""
                raise RuntimeError(
                    f"could not generate a new valid {category} shape for "
                    f"workload {workload_number}, query {index} after "
                    f"{max_attempts_per_query} attempts{detail}"
                )

        workload = {
            "format_version": 3,
            "workload_name": f"example2_schema_driven_selectivity_100_w{workload_number:02d}",
            "query_language": "CompileDB E/R SPJG SQL",
            "schema_source": schema_path.name,
            "schema_sha256": schema_hash,
            "data_profile_source": profile_path.name,
            "data_profile_sha256": profile_hash,
            "shape_generation_method": "schema_graph_random_validated_unique",
            "shape_seed": workload_seed,
            "workload_mode": (
                "strong_subclass_selection_projection_only"
                if subclass_only
                else "mixed_schema_graph"
            ),
            "sampling_policy": {
                "subclass_weight": subclass_weight,
                "leaf_subclass_weight": (
                    subclass_weight
                    if leaf_subclass_weight is None
                    else leaf_subclass_weight
                ),
                "leaf_relationship_weight": leaf_relationship_weight,
                "endpoint_subclass_probability": endpoint_subclass_probability,
                "hub_penalty": hub_penalty,
                "subclass_only": subclass_only,
                "inferred_leaf_subclasses": sorted(leaf_subclass_ids),
                "inferred_leaf_endpoint_relationships": sorted(
                    leaf_relationship_ids
                ),
            },
            "structural_access_summary": {
                key: int(structural_access_counts.get(key, 0))
                for key in (
                    "queries_with_leaf_entity",
                    "leaf_entity_bindings",
                    "queries_with_leaf_endpoint_relationship",
                    "leaf_relationship_bindings",
                )
            },
            "cross_workload_shape_reuse_allowed": not reject_cross_workload_duplicates,
            "selectivity_method": "initialization_time_conceptual_reservoir",
            "selectivity_targets": list(targets),
            "enforced_estimated_selectivity_range": (
                [
                    SUBCLASS_ONLY_MIN_SELECTIVITY,
                    SUBCLASS_ONLY_MAX_SELECTIVITY,
                ]
                if subclass_only
                else None
            ),
            "selectivity_scope": "where_filter_over_join_input",
            "category_counts": dict(sorted(category_counts.items())),
            "query_count": len(queries),
            "total_frequency": sum(query["frequency"] for query in queries),
            "unique_canonical_shape_count": len(local_fingerprints),
            "mean_absolute_where_selectivity_error": (
                sum(errors) / len(errors) if errors else None
            ),
            "contains_select_star": False,
            "queries": queries,
        }
        output_path = output_directory / f"er_query_workload_100_{workload_number:02d}.json"
        output_path.write_text(
            json.dumps(workload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        output_paths.append(output_path)
        if progress_every:
            print(
                f"[workload {workload_number:02d}/{workload_count:02d}] "
                f"wrote {output_path} in "
                f"{time.perf_counter() - workload_started_at:.2f}s",
                flush=True,
            )

    if progress_every:
        print(
            f"Completed {workload_count * queries_per_workload} queries in "
            f"{time.perf_counter() - started_at:.2f}s",
            flush=True,
        )

    return output_paths


def main():
    parser = argparse.ArgumentParser(
        description="Generate distinct schema-driven, selectivity-aligned E/R workloads"
    )
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("er_query_workloads"))
    parser.add_argument("--workload-count", type=int, default=10)
    parser.add_argument("--queries-per-workload", type=int, default=100)
    parser.add_argument(
        "--targets",
        default=None,
        help=(
            "comma-separated target selectivities; defaults to "
            "0.50,0.60,0.70,0.80,0.90,0.99 with --subclass-only and "
            "0.01,0.05,0.10,0.25,0.50 otherwise"
        ),
    )
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--subclass-only",
        action="store_true",
        help=(
            "generate only single-entity selection/projection queries over "
            "strong subclasses; excludes roots, weak entities, and all "
            "relationships, and enforces estimated selectivity in [0.50,0.99]"
        ),
    )
    parser.add_argument(
        "--subclass-weight",
        type=float,
        default=1.0,
        help=(
            "relative weight of every strong subclass versus a hierarchy root "
            "in selection/projection queries (default: 1, uniform)"
        ),
    )
    parser.add_argument(
        "--leaf-subclass-weight",
        type=float,
        default=None,
        help=(
            "relative weight of leaf subclasses in direct entity queries and "
            "endpoint specialization; defaults to --subclass-weight"
        ),
    )
    parser.add_argument(
        "--leaf-relationship-weight",
        type=float,
        default=1.0,
        help=(
            "relative weight of relationships declaring at least one leaf-"
            "subclass endpoint, including paths containing those relationships"
        ),
    )
    parser.add_argument(
        "--endpoint-subclass-probability",
        type=float,
        default=0.0,
        help=(
            "probability in [0,1] of joining a root-typed relationship/owner "
            "endpoint to a usable descendant (default: 0)"
        ),
    )
    parser.add_argument(
        "--hub-penalty",
        type=float,
        default=0.0,
        help=(
            "inverse-degree sampling strength for relationships and connected "
            "paths; 0 is uniform and 1 neutralizes most hub amplification"
        ),
    )
    parser.add_argument(
        "--category-mix",
        default=",".join(
            f"{name}={weight}" for name, weight in DEFAULT_CATEGORY_WEIGHTS.items()
        ),
        help="comma-separated category=weight entries",
    )
    parser.add_argument(
        "--allow-cross-workload-shape-reuse",
        action="store_true",
        help="allow the same canonical query shape in more than one workload",
    )
    parser.add_argument("--max-attempts-per-query", type=int, default=2_000)
    parser.add_argument(
        "--progress-every",
        type=int,
        default=25,
        help="print progress after this many accepted queries; use 0 to disable",
    )
    arguments = parser.parse_args()

    targets_text = arguments.targets
    if targets_text is None:
        targets_text = (
            "0.50,0.60,0.70,0.80,0.90,0.99"
            if arguments.subclass_only
            else "0.01,0.05,0.10,0.25,0.50"
        )
    targets = tuple(float(value) for value in targets_text.split(","))
    paths = generate_schema_driven_workloads(
        arguments.schema,
        arguments.profile,
        arguments.output_dir,
        workload_count=arguments.workload_count,
        queries_per_workload=arguments.queries_per_workload,
        targets=targets,
        seed=arguments.seed,
        category_weights=parse_category_weights(arguments.category_mix),
        subclass_weight=arguments.subclass_weight,
        leaf_subclass_weight=arguments.leaf_subclass_weight,
        leaf_relationship_weight=arguments.leaf_relationship_weight,
        endpoint_subclass_probability=(
            arguments.endpoint_subclass_probability
        ),
        hub_penalty=arguments.hub_penalty,
        subclass_only=arguments.subclass_only,
        reject_cross_workload_duplicates=(
            not arguments.allow_cross_workload_shape_reuse
        ),
        max_attempts_per_query=arguments.max_attempts_per_query,
        progress_every=arguments.progress_every,
    )
    print(
        f"Generated {len(paths)} workloads with "
        f"{arguments.queries_per_workload} distinct E/R query shapes each"
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
