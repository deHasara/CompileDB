"""Generate E/R query workloads calibrated to generated conceptual data.

The input workload supplies query shapes. Literal predicates in each WHERE
clause are replaced with values selected from the initialization-time
conceptual reservoir profile. HAVING predicates are preserved and explicitly
marked as requiring result-level calibration if their output selectivity must
also be controlled.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import random
import re
from pathlib import Path

from data_profile import (
    choose_predicate,
    load_profile,
    predicate_selectivity,
    profile_values,
)


ALIAS_PATTERN = re.compile(
    r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
IN_PATTERN = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s+"
    r"(NOT\s+IN|IN)\s*\(([^()]*)\)",
    re.IGNORECASE,
)
IS_NULL_PATTERN = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s+"
    r"(IS\s+NOT\s+NULL|IS\s+NULL)",
    re.IGNORECASE,
)
SCALAR_PATTERN = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*"
    r"(>=|<=|<>|!=|=|>|<)\s*"
    r"('(?:''|[^'])*'|-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
COLUMN_COMPARISON_PATTERN = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*"
    r"(>=|<=|<>|!=|=|>|<)\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
LITERAL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])('(?:''|[^'])*'|-?\d+(?:\.\d+)?)(?![A-Za-z0-9_])"
)


def sql_literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return repr(value)
    return "'" + str(value).replace("'", "''") + "'"


def parse_literal(token):
    token = token.strip()
    if token.startswith("'") and token.endswith("'"):
        return token[1:-1].replace("''", "'")
    if "." in token:
        return float(token)
    return int(token)


def literal_arguments(sql):
    values = [parse_literal(match.group(1)) for match in LITERAL_PATTERN.finditer(sql)]
    return {f"p{index}": value for index, value in enumerate(values)}


def where_region(sql):
    where = re.search(r"\bWHERE\b", sql, re.IGNORECASE)
    if where is None:
        return None
    end = re.search(r"\b(?:GROUP\s+BY|HAVING)\b|;", sql[where.end():], re.IGNORECASE)
    end_position = where.end() + (end.start() if end else len(sql) - where.end())
    return where.end(), end_position, sql[where.end():end_position]


def query_aliases(sql):
    return {
        alias.lower(): object_name.lower()
        for object_name, alias in ALIAS_PATTERN.findall(sql)
    }


def _predicate_record(object_name, attribute, operator, estimated, **extra):
    result = {
        "object": object_name,
        "attribute": attribute,
        "operator": " ".join(operator.upper().split()),
        "estimated_selectivity": estimated,
    }
    result.update(extra)
    return result


def calibrate_query(sql, profile, target_selectivity):
    aliases = query_aliases(sql)
    region = where_region(sql)
    if region is None:
        return sql, {
            "scope": "no_where_predicate",
            "target_selectivity": None,
            "estimated_selectivity": None,
            "predicates": [],
            "requires_result_calibration": "HAVING" in sql.upper(),
        }

    start, _end, where_sql = region
    adjustable = []
    fixed = []
    occupied = []

    for match in IN_PATTERN.finditer(where_sql):
        alias, attribute, operator, contents = match.groups()
        object_name = aliases.get(alias.lower())
        if object_name is None:
            continue
        count = len(list(LITERAL_PATTERN.finditer(contents)))
        adjustable.append({
            "object": object_name,
            "attribute": attribute,
            "operator": " ".join(operator.upper().split()),
            "span": (start + match.start(4), start + match.end(4)),
            "in_value_count": count,
        })
        occupied.append((match.start(), match.end()))

    for match in SCALAR_PATTERN.finditer(where_sql):
        if any(left <= match.start() < right for left, right in occupied):
            continue
        alias, attribute, operator, _literal = match.groups()
        object_name = aliases.get(alias.lower())
        if object_name is None:
            continue
        adjustable.append({
            "object": object_name,
            "attribute": attribute,
            "operator": operator,
            "span": (start + match.start(4), start + match.end(4)),
            "in_value_count": None,
        })
        occupied.append((match.start(), match.end()))

    for match in IS_NULL_PATTERN.finditer(where_sql):
        alias, attribute, operator = match.groups()
        object_name = aliases.get(alias.lower())
        if object_name is None:
            continue
        values = profile_values(profile, object_name, attribute)
        estimated = predicate_selectivity(values, " ".join(operator.upper().split()), None)
        fixed.append(_predicate_record(object_name, attribute, operator, estimated))

    for match in COLUMN_COMPARISON_PATTERN.finditer(where_sql):
        left_alias, left_attribute, operator, right_alias, right_attribute = match.groups()
        left_object = aliases.get(left_alias.lower())
        right_object = aliases.get(right_alias.lower())
        if left_object is None or right_object is None:
            continue
        left_values = profile_values(profile, left_object, left_attribute)
        right_values = profile_values(profile, right_object, right_attribute)
        count = min(len(left_values), len(right_values))
        comparisons = 0
        valid = 0
        for left, right in zip(left_values[:count], reversed(right_values[:count])):
            if left is None or right is None:
                continue
            valid += 1
            comparisons += {
                "<": left < right,
                "<=": left <= right,
                ">": left > right,
                ">=": left >= right,
                "=": left == right,
                "!=": left != right,
                "<>": left != right,
            }[operator]
        estimated = comparisons / count if count else None
        fixed.append({
            "left_object": left_object,
            "left_attribute": left_attribute,
            "operator": operator,
            "right_object": right_object,
            "right_attribute": right_attribute,
            "estimated_selectivity": estimated,
            "method": "independent_profile_pairing",
        })

    fixed_product = math.prod(
        predicate["estimated_selectivity"]
        for predicate in fixed
        if predicate["estimated_selectivity"] is not None
    )
    if adjustable:
        remaining = min(1.0, target_selectivity / fixed_product) if fixed_product else 1.0
        per_predicate_target = remaining ** (1.0 / len(adjustable))
    else:
        per_predicate_target = None

    replacements = []
    calibrated = []
    for predicate in adjustable:
        values = profile_values(profile, predicate["object"], predicate["attribute"])
        value, achieved = choose_predicate(
            values,
            predicate["operator"],
            per_predicate_target,
            in_value_count=predicate["in_value_count"],
        )
        if predicate["operator"] in {"IN", "NOT IN"}:
            replacement = ", ".join(sql_literal(item) for item in value)
            stored_value = list(value)
        else:
            replacement = sql_literal(value)
            stored_value = value
        replacements.append((*predicate["span"], replacement))
        calibrated.append(_predicate_record(
            predicate["object"],
            predicate["attribute"],
            predicate["operator"],
            achieved,
            target_selectivity=per_predicate_target,
            value=stored_value,
            sample_size=len(values),
        ))

    rewritten = sql
    for left, right, replacement in sorted(replacements, reverse=True):
        rewritten = rewritten[:left] + replacement + rewritten[right:]

    all_predicates = calibrated + fixed
    estimated = (
        math.prod(
            predicate["estimated_selectivity"]
            for predicate in all_predicates
            if predicate["estimated_selectivity"] is not None
        )
        if all_predicates
        else None
    )
    return rewritten, {
        "scope": "where_filter_over_join_input",
        "target_selectivity": target_selectivity if adjustable else None,
        "estimated_selectivity": estimated,
        "absolute_error": (
            abs(estimated - target_selectivity)
            if adjustable and estimated is not None
            else None
        ),
        "predicates": all_predicates,
        "assumption": "generated attributes are independent and relationship endpoints are sampled uniformly",
        "requires_result_calibration": "HAVING" in sql.upper(),
    }


def target_schedule(query_count, targets, seed):
    values = [targets[index % len(targets)] for index in range(query_count)]
    random.Random(seed).shuffle(values)
    return values


def generate_workloads(
    schema_path,
    profile_path,
    template_path,
    output_directory,
    *,
    workload_count=10,
    queries_per_workload=100,
    targets=(0.01, 0.05, 0.10, 0.25, 0.50),
    seed=1,
):
    schema_bytes = Path(schema_path).read_bytes()
    schema_hash = hashlib.sha256(schema_bytes).hexdigest()
    profile_bytes = Path(profile_path).read_bytes()
    profile_hash = hashlib.sha256(profile_bytes).hexdigest()
    profile = load_profile(profile_path)
    if profile["schema_sha256"] != schema_hash:
        raise ValueError("schema/profile hash mismatch; regenerate the initialization profile")

    template = json.loads(Path(template_path).read_text(encoding="utf-8"))
    queries = template["queries"]
    if len(queries) != queries_per_workload:
        raise ValueError(
            f"template contains {len(queries)} queries, expected {queries_per_workload}"
        )
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    output_paths = []
    for workload_number in range(1, workload_count + 1):
        schedule = target_schedule(
            queries_per_workload,
            list(targets),
            seed + workload_number - 1,
        )
        generated_queries = []
        calibrated_count = 0
        errors = []
        for index, (source_query, target) in enumerate(zip(queries, schedule), 1):
            sql, selectivity = calibrate_query(source_query["sql"], profile, target)
            query = dict(source_query)
            query["id"] = f"Q{index:03d}"
            query["sql"] = sql
            query["literal_arguments"] = literal_arguments(sql)
            query["selectivity"] = selectivity
            if selectivity["target_selectivity"] is not None:
                calibrated_count += 1
                if selectivity["absolute_error"] is not None:
                    errors.append(selectivity["absolute_error"])
            generated_queries.append(query)

        workload = dict(template)
        category_counts = Counter(
            query.get("category", "uncategorized")
            for query in generated_queries
        )
        workload.update({
            "format_version": 2,
            "workload_name": f"example2_selectivity_aligned_100_w{workload_number:02d}",
            "schema_source": Path(schema_path).name,
            "schema_sha256": schema_hash,
            "data_profile_source": Path(profile_path).name,
            "data_profile_sha256": profile_hash,
            "selectivity_method": "initialization_time_conceptual_reservoir",
            "selectivity_targets": list(targets),
            "selectivity_seed": seed + workload_number - 1,
            "calibrated_where_query_count": calibrated_count,
            "mean_absolute_where_selectivity_error": (
                sum(errors) / len(errors) if errors else None
            ),
            "query_count": len(generated_queries),
            "total_frequency": sum(query.get("frequency", 1) for query in generated_queries),
            "contains_select_star": any(
                re.search(r"\bSELECT\s+\*", query["sql"], re.IGNORECASE)
                for query in generated_queries
            ),
            "category_counts": dict(sorted(category_counts.items())),
            "queries": generated_queries,
        })
        output_path = output_directory / f"er_query_workload_100_{workload_number:02d}.json"
        output_path.write_text(json.dumps(workload, indent=2) + "\n", encoding="utf-8")
        output_paths.append(output_path)
    return output_paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--template-workload", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("er_query_workloads"))
    parser.add_argument("--workload-count", type=int, default=10)
    parser.add_argument("--queries-per-workload", type=int, default=100)
    parser.add_argument("--targets", default="0.01,0.05,0.10,0.25,0.50")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    targets = tuple(float(value) for value in args.targets.split(","))
    if not targets or any(not 0.0 <= value <= 1.0 for value in targets):
        raise ValueError("every selectivity target must be between 0 and 1")

    paths = generate_workloads(
        args.schema,
        args.profile,
        args.template_workload,
        args.output_dir,
        workload_count=args.workload_count,
        queries_per_workload=args.queries_per_workload,
        targets=targets,
        seed=args.seed,
    )
    print(f"Generated {len(paths)} workloads with {args.queries_per_workload} E/R queries each")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
