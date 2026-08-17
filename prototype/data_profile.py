"""Mapping-independent reservoir profile of generated conceptual E/R tuples."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


def _stable_seed(seed: int, object_name: str) -> int:
    digest = hashlib.sha256(f"{seed}:{object_name.lower()}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


class Reservoir:
    def __init__(self, capacity: int, seed: int):
        if capacity < 1:
            raise ValueError("profile sample size must be positive")
        self.capacity = capacity
        self.seen = 0
        self.rows = []
        self.random = random.Random(seed)

    def observe(self, row: Mapping[str, Any]):
        self.seen += 1
        value = dict(row)
        if len(self.rows) < self.capacity:
            self.rows.append(value)
            return
        position = self.random.randrange(self.seen)
        if position < self.capacity:
            self.rows[position] = value


class ConceptualDataProfile:
    def __init__(self, sample_size=10_000, seed=1):
        self.sample_size = int(sample_size)
        self.seed = int(seed)
        self.reservoirs = {}

    def _reservoir(self, object_name):
        key = str(object_name).lower()
        if key not in self.reservoirs:
            self.reservoirs[key] = Reservoir(
                self.sample_size,
                _stable_seed(self.seed, key),
            )
        return self.reservoirs[key]

    def observe(self, node, row):
        """Observe a strict tuple and propagate subclass tuples to ancestors."""

        self._reservoir(node.unique_name).observe(row)
        if not (
            node.is_entity()
            and not getattr(node, "is_weak_entity", False)
            and getattr(node, "is_subclass", False)
        ):
            return
        parent = getattr(node, "parent_entity", None)
        while parent is not None:
            self._reservoir(parent.unique_name).observe(row)
            parent = (
                getattr(parent, "parent_entity", None)
                if getattr(parent, "is_subclass", False)
                else None
            )

    def write(self, path, *, schema_sha256, generation_seed):
        objects = {
            name: {
                "population_size": reservoir.seen,
                "sample_size": len(reservoir.rows),
                "rows": reservoir.rows,
            }
            for name, reservoir in sorted(self.reservoirs.items())
        }
        payload = {
            "format_version": 1,
            "profile_type": "conceptual_er_reservoir",
            "schema_sha256": schema_sha256,
            "generation_seed": generation_seed,
            "reservoir_seed": self.seed,
            "reservoir_capacity": self.sample_size,
            "objects": objects,
        }
        Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_profile(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def profile_values(profile, object_name, attribute_name):
    object_data = profile["objects"].get(str(object_name).lower())
    if object_data is None:
        raise KeyError(f"profile has no conceptual object {object_name!r}")
    requested = str(attribute_name).lower()
    result = []
    for row in object_data["rows"]:
        matches = [value for key, value in row.items() if str(key).lower() == requested]
        if len(matches) == 1 and not isinstance(matches[0], (list, dict)):
            result.append(matches[0])
    if not result:
        raise KeyError(f"profile has no scalar values for {object_name}.{attribute_name}")
    return result


def predicate_selectivity(values, operator, candidate):
    operator = operator.upper()
    if operator == "IS NULL":
        return sum(value is None for value in values) / len(values)
    if operator == "IS NOT NULL":
        return sum(value is not None for value in values) / len(values)
    if operator == "IN":
        candidates = set(candidate)
        return sum(value in candidates for value in values) / len(values)
    if operator == "NOT IN":
        candidates = set(candidate)
        return sum(value is not None and value not in candidates for value in values) / len(values)

    def matches(value):
        if value is None:
            return False
        if operator == "=":
            return value == candidate
        if operator in {"!=", "<>"}:
            return value != candidate
        if operator == "<":
            return value < candidate
        if operator == "<=":
            return value <= candidate
        if operator == ">":
            return value > candidate
        if operator == ">=":
            return value >= candidate
        raise ValueError(f"unsupported predicate operator {operator!r}")

    return sum(matches(value) for value in values) / len(values)


def choose_predicate(values, operator, target, *, in_value_count=None):
    """Return the observed literal whose sample selectivity is closest to target."""

    operator = operator.upper()
    non_null = [value for value in values if value is not None]
    if not non_null:
        raise ValueError("cannot calibrate from an all-NULL sample")
    frequencies = Counter(non_null)
    candidates = sorted(frequencies)

    if operator in {"IN", "NOT IN"}:
        count = max(1, int(in_value_count or 1))
        # Preserve the template's number of IN-list placeholders. For large
        # numeric domains, frequency-ranked observed values are the tractable
        # candidate pool; for small categorical domains, search all subsets.
        ranked = sorted(frequencies, key=lambda value: (-frequencies[value], repr(value)))
        if len(ranked) <= 16:
            from itertools import combinations

            choices = list(combinations(ranked, min(count, len(ranked))))
        else:
            pool = ranked[: max(32, count)]
            choices = [tuple(pool[offset:offset + count]) for offset in range(len(pool) - count + 1)]
    else:
        choices = candidates

    value = min(
        choices,
        key=lambda item: (
            abs(predicate_selectivity(values, operator, item) - target),
            repr(item),
        ),
    )
    achieved = predicate_selectivity(values, operator, value)
    return value, achieved

