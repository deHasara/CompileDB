"""Sampling and validation for conceptual-schema attribute distributions.

The JSON schema stores a distribution specification in
``node_data.<entity>.attribute_domains.<attribute>``.  Legacy two-element
integer ranges and string lists remain supported.
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta
from typing import Any, Mapping


class DistributionError(ValueError):
    """Raised when an attribute distribution specification is invalid."""


def _clamp(value: int, spec: Mapping[str, Any]) -> int:
    return max(int(spec["min"]), min(int(spec["max"]), value))


def _weighted_index(weights: list[float], rng: random.Random | Any) -> int:
    if not weights or any(weight < 0 for weight in weights) or sum(weights) <= 0:
        raise DistributionError("weights must be non-negative and sum to more than zero")
    return rng.choices(range(len(weights)), weights=weights, k=1)[0]


def sample_distribution(
    spec: Any,
    attribute_type: str | None = None,
    *,
    rng: random.Random | Any = random,
    faker: Any = None,
) -> Any:
    """Draw one value from a JSON distribution specification.

    ``rng`` may be either the :mod:`random` module or a ``random.Random``
    instance.  Passing both an explicitly seeded RNG and Faker instance makes
    generation repeatable.
    """

    if spec is None:
        return None

    # Backwards-compatible schema formats used by the original generator.
    if isinstance(spec, list):
        if attribute_type in {"INT", "INTEGER"} and len(spec) == 2:
            return rng.randint(int(spec[0]), int(spec[1]))
        if not spec:
            raise DistributionError("a categorical value list cannot be empty")
        return rng.choice(spec)

    if not isinstance(spec, Mapping):
        raise DistributionError(f"distribution must be an object or list, got {type(spec).__name__}")

    null_probability = float(spec.get("null_probability", 0.0))
    if not 0.0 <= null_probability <= 1.0:
        raise DistributionError("null_probability must be between 0 and 1")
    if null_probability and rng.random() < null_probability:
        return None

    family = spec.get("distribution")

    if family == "constant":
        return spec.get("value")

    if family == "uniform_int":
        return rng.randint(int(spec["min"]), int(spec["max"]))

    if family == "categorical":
        values = list(spec["values"])
        if not values:
            raise DistributionError("categorical.values cannot be empty")
        weights = spec.get("weights")
        if weights is None:
            return rng.choice(values)
        weights = [float(weight) for weight in weights]
        if len(weights) != len(values):
            raise DistributionError("categorical weights and values must have equal length")
        return values[_weighted_index(weights, rng)]

    if family == "normal_int":
        value = round(rng.gauss(float(spec["mean"]), float(spec["stddev"])))
        return _clamp(value, spec)

    if family == "lognormal_int":
        median = float(spec["median"])
        if median <= 0:
            raise DistributionError("lognormal_int.median must be positive")
        value = round(rng.lognormvariate(math.log(median), float(spec["sigma"])))
        return _clamp(value, spec)

    if family == "uniform_date":
        start = date.fromisoformat(spec["start"])
        end = date.fromisoformat(spec["end"])
        if end < start:
            raise DistributionError("uniform_date.end must not precede start")
        return (start + timedelta(days=rng.randint(0, (end - start).days))).isoformat()

    if family == "faker":
        if faker is None:
            try:
                from faker import Faker
            except ImportError as exc:
                raise DistributionError(
                    "the 'faker' package is required when sampling a Faker distribution"
                ) from exc
            faker_instance = Faker()
        else:
            faker_instance = faker
        provider_name = spec["provider"]
        try:
            provider = getattr(faker_instance, provider_name)
        except AttributeError as exc:
            raise DistributionError(f"unknown Faker provider: {provider_name}") from exc
        kwargs = dict(spec.get("kwargs", {}))
        return provider(**kwargs)

    if family == "mixture":
        components = list(spec.get("components", []))
        if not components:
            raise DistributionError("mixture.components cannot be empty")
        index = _weighted_index([float(item["weight"]) for item in components], rng)
        component = components[index]
        nested_spec = component.get("spec", {"distribution": "constant", "value": component.get("value")})
        return sample_distribution(nested_spec, attribute_type, rng=rng, faker=faker)

    raise DistributionError(f"unsupported distribution family: {family!r}")


def resolve_attribute_distribution(
    schema_data: Mapping[str, Any],
    current_node_data: Mapping[str, Any] | None,
    attribute: Mapping[str, Any],
    attribute_name: str,
) -> Any:
    """Resolve a local or inherited attribute's declaring-node distribution."""

    local_domains = (current_node_data or {}).get("attribute_domains", {})
    if attribute_name in local_domains:
        return local_domains[attribute_name]

    node_data = schema_data.get("node_data", {})
    owner_candidates = (
        attribute.get("entity_unique_name"),
        attribute.get("pk_entity_name"),
    )
    for owner in owner_candidates:
        if not owner:
            continue
        owner_data = node_data.get(owner) or node_data.get(str(owner).lower())
        owner_domains = (owner_data or {}).get("attribute_domains", {})
        if attribute_name in owner_domains:
            return owner_domains[attribute_name]
    return None


def validate_distribution(spec: Any, attribute_type: str | None = None) -> None:
    """Validate a specification without depending on a particular random draw."""

    class _ValidationFaker:
        def __getattr__(self, _name):
            return lambda **_kwargs: "validation-value"

    # Sampling catches structural errors. Dedicated stand-ins prevent mutation
    # of the caller's data-generation streams and avoid requiring Faker merely
    # to validate a schema catalog.
    sample_distribution(spec, attribute_type, rng=random.Random(0), faker=_ValidationFaker())
