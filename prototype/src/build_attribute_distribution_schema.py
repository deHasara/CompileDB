"""Add fixed, predicate-independent attribute distributions to the E/R schema.

Usage:
    python3 build_attribute_distribution_schema.py INPUT.json OUTPUT.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from attribute_distributions import validate_distribution


def categorical(values, weights=None, *, null_probability=None):
    spec = {"distribution": "categorical", "values": values}
    if weights is not None:
        spec["weights"] = weights
    if null_probability is not None:
        spec["null_probability"] = null_probability
    return spec


def faker(provider, **kwargs):
    spec = {"distribution": "faker", "provider": provider}
    if kwargs:
        spec["kwargs"] = kwargs
    return spec


def uniform_int(minimum, maximum, *, null_probability=None):
    spec = {"distribution": "uniform_int", "min": minimum, "max": maximum}
    if null_probability is not None:
        spec["null_probability"] = null_probability
    return spec


def normal_int(mean, stddev, minimum, maximum, *, null_probability=None):
    spec = {
        "distribution": "normal_int",
        "mean": mean,
        "stddev": stddev,
        "min": minimum,
        "max": maximum,
    }
    if null_probability is not None:
        spec["null_probability"] = null_probability
    return spec


def lognormal_int(median, sigma, minimum, maximum, *, null_probability=None):
    spec = {
        "distribution": "lognormal_int",
        "median": median,
        "sigma": sigma,
        "min": minimum,
        "max": maximum,
    }
    if null_probability is not None:
        spec["null_probability"] = null_probability
    return spec


def uniform_date(start, end, *, null_probability=None):
    spec = {"distribution": "uniform_date", "start": start, "end": end}
    if null_probability is not None:
        spec["null_probability"] = null_probability
    return spec


DISCRIMINATOR = uniform_int(1, 10_000_000)


# Only declaring entities are listed. Product distributions, for example, are
# inherited by PhysicalProduct, Electronics, Accessory, and all other Product
# descendants when those tuples are generated.
ATTRIBUTE_DISTRIBUTIONS = {
    "category": {
        "category_name": faker("word"),
        "parent": uniform_int(1, 24_195, null_probability=0.08),
    },
    "product": {
        "sku": faker("bothify", text="SKU-????-########"),
        "product_name": faker("catch_phrase"),
        "base_price": lognormal_int(120, 0.85, 5, 5_000),
        "is_active": categorical([0, 1], [0.15, 0.85]),
        "quantity": {
            "distribution": "mixture",
            "components": [
                {"weight": 0.08, "value": 0},
                {
                    "weight": 0.92,
                    "spec": lognormal_int(25, 1.0, 1, 1_000),
                },
            ],
        },
        "mv_attributes": categorical(
            ["eco", "new", "sale", "premium", "refurbished", "limited", "popular", "imported"],
            [0.10, 0.16, 0.20, 0.12, 0.08, 0.07, 0.18, 0.09],
        ),
    },
    "physicalproduct": {
        "dimensions": categorical(
            ["small", "medium", "large", "oversize"], [0.24, 0.46, 0.25, 0.05]
        )
    },
    "digitalproduct": {
        "delivery_type": categorical(
            ["download", "license_key", "stream", "account_activation"],
            [0.42, 0.31, 0.20, 0.07],
        )
    },
    "electronics": {
        "warranty_months": categorical([0, 6, 12, 24, 36], [0.05, 0.10, 0.47, 0.30, 0.08])
    },
    "computer": {
        "cpu": categorical(
            ["Core i3", "Core i5", "Core i7", "Core i9", "Ryzen 5", "Ryzen 7", "Apple M3"],
            [0.08, 0.25, 0.23, 0.07, 0.16, 0.14, 0.07],
        ),
        "ram_gb": categorical([4, 8, 16, 32, 64, 128], [0.04, 0.20, 0.38, 0.25, 0.10, 0.03]),
    },
    "desktop": {"form_factor": categorical(["tower", "mini", "all-in-one", "small-form"], [0.46, 0.15, 0.21, 0.18])},
    "laptop": {"battery_wh": normal_int(65, 15, 30, 120)},
    "tablet": {"screen_size_in": categorical([8, 10, 11, 13], [0.12, 0.35, 0.40, 0.13])},
    "smartwatch": {"band_size": categorical(["XS", "S", "M", "L", "XL"], [0.05, 0.18, 0.45, 0.25, 0.07])},
    "camera": {"sensor_mp": categorical([12, 16, 20, 24, 32, 48, 64], [0.05, 0.09, 0.18, 0.28, 0.18, 0.15, 0.07])},
    "phone": {"carrier_lock": categorical(["unlocked", "locked"], [0.70, 0.30])},
    "accessory": {"accessory_type": categorical(["case", "charger", "cable", "adapter", "stand", "headset"], [0.25, 0.20, 0.20, 0.12, 0.08, 0.15])},
    "appliance": {"energy_rating": categorical(["A++", "A+", "A", "B", "C", "D"], [0.10, 0.22, 0.31, 0.21, 0.11, 0.05])},
    "kitchenappliance": {"warranty_years": categorical([1, 2, 3, 5], [0.35, 0.38, 0.20, 0.07])},
    "apparel": {"size_system": categorical(["US", "EU", "UK", "alpha"], [0.37, 0.28, 0.12, 0.23])},
    "clothing": {"material": categorical(["cotton", "polyester", "wool", "linen", "denim", "blend"], [0.31, 0.22, 0.10, 0.08, 0.12, 0.17])},
    "menclothing": {"fit_type_men": categorical(["slim", "regular", "relaxed", "athletic"], [0.28, 0.43, 0.19, 0.10])},
    "womenclothing": {"fit_type_women": categorical(["petite", "regular", "tall", "plus"], [0.14, 0.56, 0.12, 0.18])},
    "footwear": {"sole_material": categorical(["rubber", "leather", "EVA", "TPU", "synthetic"], [0.42, 0.14, 0.19, 0.10, 0.15])},
    "media": {"format": categorical(["ebook", "audio", "video", "music", "printable"], [0.28, 0.17, 0.25, 0.20, 0.10])},
    "software": {"license_type": categorical(["subscription", "perpetual", "freemium", "open_source"], [0.47, 0.24, 0.18, 0.11])},
    "user": {
        "email": faker("email"),
        "password_hash": faker("sha256"),
        "mv_user": categorical(["buyer", "seller", "reviewer", "subscriber", "admin"], [0.40, 0.12, 0.22, 0.23, 0.03]),
    },
    "customer": {
        "loyalty_tier": categorical(["bronze", "silver", "gold", "platinum"], [0.48, 0.29, 0.17, 0.06]),
        "contact_no": faker("phone_number"),
    },
    "primecustomer": {
        "renewal_date": uniform_date("2026-01-01", "2027-12-31", null_probability=0.08),
        "subscription_addons": categorical(["video", "music", "cloud", "delivery", "support", "family"], [0.23, 0.18, 0.13, 0.25, 0.08, 0.13]),
    },
    "businesscustomer": {"company_name": faker("company")},
    "employee": {"employee_no": faker("bothify", text="EMP-########")},
    "productimage": {
        "image_id": DISCRIMINATOR,
        "url": faker("image_url"),
        "alt_text": faker("sentence", nb_words=6),
        "sort_order": categorical([1, 2, 3, 4, 5, 6, 7, 8], [0.30, 0.22, 0.16, 0.11, 0.08, 0.06, 0.04, 0.03]),
    },
    "productvariant": {
        "variant_id": DISCRIMINATOR,
        "price_override": lognormal_int(130, 0.8, 5, 5_000, null_probability=0.35),
        "barcode": faker("ean13"),
        "is_active_variant": categorical([0, 1], [0.12, 0.88]),
    },
    "pricehistory": {
        "price_id": DISCRIMINATOR,
        "starts_at": uniform_date("2021-01-01", "2026-08-01"),
        "ends_at": uniform_date("2021-01-02", "2026-12-31", null_probability=0.20),
        "price": lognormal_int(110, 0.85, 5, 5_000),
    },
    "tag": {"tag_name": categorical(["new", "sale", "popular", "eco", "premium", "gift", "seasonal", "exclusive"], [0.15, 0.20, 0.18, 0.10, 0.12, 0.09, 0.09, 0.07])},
    "address": {
        "address_id": DISCRIMINATOR,
        "kind": categorical(["home", "work", "billing", "shipping", "other"], [0.34, 0.12, 0.18, 0.31, 0.05]),
        "line1": faker("street_address"),
        "city": faker("city"),
        "state": faker("state_abbr"),
        "country": categorical(["US", "CA", "GB", "DE", "FR", "AU", "JP", "IN"], [0.45, 0.10, 0.10, 0.08, 0.07, 0.06, 0.06, 0.08]),
        "postal_code": faker("postcode"),
    },
    "paymentmethod": {
        "payment_method_id": DISCRIMINATOR,
        "brand": categorical(["Visa", "Mastercard", "Amex", "Discover", "PayPal"], [0.43, 0.32, 0.11, 0.05, 0.09]),
        "last4": faker("numerify", text="####"),
        "exp_month": uniform_int(1, 12),
        "exp_year": uniform_int(2026, 2032),
        "is_default": categorical(["true", "false"], [0.22, 0.78]),
    },
    "cart": {"cart_id": DISCRIMINATOR, "updated_at": uniform_date("2025-01-01", "2026-08-01")},
    "wishlist": {"wishlist_id": DISCRIMINATOR, "wishlist_name": categorical(["default", "birthday", "holiday", "later", "favorites"], [0.43, 0.12, 0.14, 0.18, 0.13])},
    "review": {
        "review_id": DISCRIMINATOR,
        "rating": categorical([1, 2, 3, 4, 5], [0.06, 0.08, 0.16, 0.31, 0.39]),
        "title": faker("sentence", nb_words=6),
        "body": faker("text", max_nb_chars=180),
        "created_at": uniform_date("2022-01-01", "2026-08-01"),
    },
    "browsingsession": {
        "session_id": DISCRIMINATOR,
        "started_at": uniform_date("2025-01-01", "2026-08-01"),
        "device": categorical(["mobile", "desktop", "tablet", "other"], [0.57, 0.32, 0.09, 0.02]),
    },
    "custorder": {
        "placed_at": uniform_date("2022-01-01", "2026-08-01"),
        "status": categorical(["pending", "paid", "processing", "shipped", "delivered", "cancelled", "returned"], [0.05, 0.07, 0.10, 0.14, 0.50, 0.08, 0.06]),
    },
    "shipment": {
        "shipment_id": DISCRIMINATOR,
        "carrier": categorical(["UPS", "FedEx", "USPS", "DHL", "local"], [0.28, 0.24, 0.25, 0.15, 0.08]),
        "tracking_no": faker("bothify", text="??##########"),
        "shipped_at": uniform_date("2022-01-01", "2026-08-01", null_probability=0.08),
        "delivered_at": uniform_date("2022-01-02", "2026-08-07", null_probability=0.25),
    },
    "promotion": {
        "promo_name": faker("catch_phrase"),
        "starts_at": uniform_date("2024-01-01", "2026-12-01"),
        "ends_at": uniform_date("2024-01-02", "2027-03-31"),
        "discount_type": categorical(["percent", "fixed", "free_shipping"], [0.58, 0.29, 0.13]),
        "discount_value": categorical(["5", "10", "15", "20", "25", "50"], [0.12, 0.26, 0.24, 0.20, 0.12, 0.06]),
    },
    "coupon": {
        "coupon_code": DISCRIMINATOR,
        "max_uses": lognormal_int(500, 1.1, 1, 100_000),
        "per_user_limit": categorical([1, 2, 3, 5, 10], [0.55, 0.20, 0.12, 0.09, 0.04]),
    },
    "warehouse": {
        "warehouse_name": faker("company"),
        "region": categorical(["Northeast", "Southeast", "Midwest", "Southwest", "West"], [0.20, 0.22, 0.19, 0.14, 0.25]),
    },
    "warehousebin": {"bin_id": DISCRIMINATOR, "code": faker("bothify", text="??-###-??")},
    "supplier": {"supplier_name": faker("company")},
    "suppliercontact": {
        "contact_id": DISCRIMINATOR,
        "email": {**faker("email"), "null_probability": 0.05},
        "phone": {**faker("phone_number"), "null_probability": 0.08},
    },
    "purchaseorder": {
        "created_at": uniform_date("2022-01-01", "2026-08-01"),
        "status": categorical(["draft", "submitted", "approved", "received", "cancelled"], [0.07, 0.13, 0.18, 0.55, 0.07]),
    },
    "courierpartner": {
        "carrier_code": faker("bothify", text="CAR-????"),
        "webhook_url": faker("url"),
    },
}


def declared_non_primary_attributes(schema):
    """Extract locally declared non-primary attributes from this E/R DDL."""

    result = {}
    pattern = re.compile(
        r"CREATE (?:WEAK )?ENTITY\s+(\w+)\s*\((.*?)\)\s*(?:subclass|DEPENDS|;)",
        re.IGNORECASE,
    )
    for statement in schema["create_entity_statements"]:
        match = pattern.match(statement)
        if not match:
            raise ValueError(f"cannot extract attributes from: {statement}")
        node_name = match.group(1).lower()
        attributes = set()
        for declaration in match.group(2).split(","):
            tokens = declaration.strip().split()
            if "PRIMARY" not in {token.upper() for token in tokens}:
                attributes.add(tokens[0])
        result[node_name] = attributes
    return result


def add_distributions(schema):
    missing_nodes = sorted(set(ATTRIBUTE_DISTRIBUTIONS) - set(schema["node_data"]))
    if missing_nodes:
        raise KeyError(f"distribution nodes absent from schema: {missing_nodes}")

    declared = declared_non_primary_attributes(schema)
    missing_attributes = []
    extra_attributes = []
    for node_name, expected in declared.items():
        configured = set(ATTRIBUTE_DISTRIBUTIONS.get(node_name, {}))
        missing_attributes.extend((node_name, name) for name in sorted(expected - configured))
        extra_attributes.extend((node_name, name) for name in sorted(configured - expected))
    if missing_attributes or extra_attributes:
        raise KeyError(
            "distribution coverage mismatch: "
            f"missing={missing_attributes}, extra={extra_attributes}"
        )

    for node_name, domains in ATTRIBUTE_DISTRIBUTIONS.items():
        for attribute_type_hint, spec in ((None, item) for item in domains.values()):
            validate_distribution(spec, attribute_type_hint)
        schema["node_data"][node_name]["attribute_domains"] = domains

    schema["attribute_distribution_metadata"] = {
        "version": 1,
        "seed": 1,
        "faker_locale": "en_US",
        "predicate_independent": True,
        "inheritance_policy": "store once at the declaring entity and resolve for descendants",
        "primary_key_policy": "sequential generated identifiers; not sampled from attribute_domains",
        "relationship_policy": "participation_factor and fanout remain in relationship node_data",
        "supported_families": [
            "categorical",
            "constant",
            "faker",
            "lognormal_int",
            "mixture",
            "normal_int",
            "uniform_date",
            "uniform_int",
        ],
    }
    return schema


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    with args.input.open(encoding="utf-8") as source:
        schema = json.load(source)
    add_distributions(schema)
    with args.output.open("w", encoding="utf-8") as destination:
        json.dump(schema, destination, indent=2)
        destination.write("\n")
    print(f"Wrote {args.output} with distributions for {len(ATTRIBUTE_DISTRIBUTIONS)} entities")


if __name__ == "__main__":
    main()
