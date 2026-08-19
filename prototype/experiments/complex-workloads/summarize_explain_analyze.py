"""Summarize per-query and total PostgreSQL EXPLAIN ANALYZE time.

The parser recognizes the Qnnn occurrence markers emitted by
``rewrite_er_query_workloads.py`` and both TEXT and JSON EXPLAIN formats.
Repeated occurrences of the same query are accumulated.
"""

from __future__ import annotations

import argparse
from collections import OrderedDict
import csv
from dataclasses import dataclass, field
import json
from pathlib import Path
import re


QUERY_MARKER = re.compile(
    r"^--\s+(Q\d+)\s+\[([^\]]+)\]\s+occurrence\s+(\d+)/(\d+)\s*$"
)
TEXT_PLANNING_TIME = re.compile(
    r"^\s*Planning Time:\s*([0-9]+(?:\.[0-9]+)?)\s*ms\s*$"
)
TEXT_EXECUTION_TIME = re.compile(
    r"^\s*Execution Time:\s*([0-9]+(?:\.[0-9]+)?)\s*ms\s*$"
)
JSON_PLANNING_TIME = re.compile(
    r'^\s*"Planning Time"\s*:\s*([0-9.eE+-]+)\s*,?\s*$'
)
JSON_EXECUTION_TIME = re.compile(
    r'^\s*"Execution Time"\s*:\s*([0-9.eE+-]+)\s*,?\s*$'
)
WORKLOAD_NAME = re.compile(r"^--\s+Conceptual workload:\s*(.+?)\s*$")
MAPPING_ID = re.compile(r"^--\s+Mapping ID:\s*(.+?)\s*$")
DECLARED_QUERY_COUNT = re.compile(r"^--\s+Query shapes:\s*(\d+)\s*$")
DECLARED_STATEMENT_COUNT = re.compile(r"^--\s+Executed statements:\s*(\d+)\s*$")
POSTGRES_ERROR = re.compile(r"(?:^|\s)(?:ERROR|FATAL):|^psql:", re.IGNORECASE)


@dataclass
class Occurrence:
    number: int
    expected_total: int
    planning_ms: float | None = None
    execution_ms: float | None = None


@dataclass
class QueryTiming:
    query_id: str
    category: str
    expected_occurrences: int
    occurrences: list[Occurrence] = field(default_factory=list)

    @property
    def execution_values(self):
        return [item.execution_ms for item in self.occurrences if item.execution_ms is not None]

    @property
    def planning_values(self):
        return [item.planning_ms for item in self.occurrences if item.planning_ms is not None]


def _match_time(line, text_pattern, json_pattern):
    match = text_pattern.match(line) or json_pattern.match(line)
    return float(match.group(1)) if match else None


def parse_log(path):
    path = Path(path)
    queries = OrderedDict()
    current = None
    metadata = {
        "input_log": str(path.resolve()),
        "workload_name": None,
        "mapping_id": None,
        "declared_query_count": None,
        "declared_statement_count": None,
    }
    errors = []

    with path.open(encoding="utf-8", errors="replace") as source:
        for line_number, raw_line in enumerate(source, 1):
            line = raw_line.rstrip("\r\n")
            if match := WORKLOAD_NAME.match(line):
                metadata["workload_name"] = match.group(1)
            elif match := MAPPING_ID.match(line):
                metadata["mapping_id"] = match.group(1)
            elif match := DECLARED_QUERY_COUNT.match(line):
                metadata["declared_query_count"] = int(match.group(1))
            elif match := DECLARED_STATEMENT_COUNT.match(line):
                metadata["declared_statement_count"] = int(match.group(1))

            if POSTGRES_ERROR.search(line):
                errors.append({"line": line_number, "message": line.strip()})

            marker = QUERY_MARKER.match(line)
            if marker:
                query_id, category, occurrence_number, expected_total = marker.groups()
                occurrence_number = int(occurrence_number)
                expected_total = int(expected_total)
                timing = queries.get(query_id)
                if timing is None:
                    timing = QueryTiming(query_id, category, expected_total)
                    queries[query_id] = timing
                elif timing.category != category or timing.expected_occurrences != expected_total:
                    raise ValueError(
                        f"{path}:{line_number}: inconsistent marker for {query_id}"
                    )
                if any(item.number == occurrence_number for item in timing.occurrences):
                    raise ValueError(
                        f"{path}:{line_number}: duplicate {query_id} occurrence {occurrence_number}"
                    )
                current = Occurrence(occurrence_number, expected_total)
                timing.occurrences.append(current)
                continue

            planning = _match_time(line, TEXT_PLANNING_TIME, JSON_PLANNING_TIME)
            if planning is not None:
                if current is None:
                    raise ValueError(f"{path}:{line_number}: Planning Time before query marker")
                if current.planning_ms is not None:
                    raise ValueError(f"{path}:{line_number}: duplicate Planning Time")
                current.planning_ms = planning
                continue

            execution = _match_time(line, TEXT_EXECUTION_TIME, JSON_EXECUTION_TIME)
            if execution is not None:
                if current is None:
                    raise ValueError(f"{path}:{line_number}: Execution Time before query marker")
                if current.execution_ms is not None:
                    raise ValueError(f"{path}:{line_number}: duplicate Execution Time")
                current.execution_ms = execution

    metadata["postgres_errors"] = errors
    return metadata, queries


def validate(metadata, queries, expected_query_count):
    problems = []
    observed_query_count = len(queries)
    observed_statement_count = sum(len(query.occurrences) for query in queries.values())

    effective_expected_queries = expected_query_count
    if effective_expected_queries is None:
        effective_expected_queries = metadata["declared_query_count"]
    if effective_expected_queries is not None and observed_query_count != effective_expected_queries:
        problems.append(
            f"observed {observed_query_count} query IDs; expected {effective_expected_queries}"
        )
    if (
        metadata["declared_statement_count"] is not None
        and observed_statement_count != metadata["declared_statement_count"]
    ):
        problems.append(
            f"observed {observed_statement_count} occurrences; workload declares "
            f"{metadata['declared_statement_count']}"
        )
    for query in queries.values():
        observed_numbers = sorted(item.number for item in query.occurrences)
        expected_numbers = list(range(1, query.expected_occurrences + 1))
        if observed_numbers != expected_numbers:
            problems.append(
                f"{query.query_id}: occurrences {observed_numbers}; expected {expected_numbers}"
            )
        missing_execution = [
            item.number for item in query.occurrences if item.execution_ms is None
        ]
        missing_planning = [
            item.number for item in query.occurrences if item.planning_ms is None
        ]
        if missing_execution:
            problems.append(f"{query.query_id}: missing Execution Time for {missing_execution}")
        if missing_planning:
            problems.append(f"{query.query_id}: missing Planning Time for {missing_planning}")
    if metadata["postgres_errors"]:
        problems.append(f"log contains {len(metadata['postgres_errors'])} PostgreSQL/psql errors")
    return problems


def query_row(query):
    execution = query.execution_values
    planning = query.planning_values
    total_execution = sum(execution)
    total_planning = sum(planning)
    return {
        "query_id": query.query_id,
        "category": query.category,
        "expected_occurrences": query.expected_occurrences,
        "observed_occurrences": len(query.occurrences),
        "total_execution_ms": total_execution,
        "mean_execution_ms": total_execution / len(execution) if execution else None,
        "min_execution_ms": min(execution) if execution else None,
        "max_execution_ms": max(execution) if execution else None,
        "total_planning_ms": total_planning,
        "mean_planning_ms": total_planning / len(planning) if planning else None,
        "total_planning_plus_execution_ms": total_planning + total_execution,
    }


def write_csv(path, rows):
    fieldnames = list(rows[0]) if rows else []
    with Path(path).open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: f"{value:.6f}" if isinstance(value, float) else value
                    for key, value in row.items()
                }
            )


def summarize(path, expected_query_count=100, output_prefix=None, allow_incomplete=False):
    metadata, queries = parse_log(path)
    problems = validate(metadata, queries, expected_query_count)
    if problems and not allow_incomplete:
        details = "\n".join(f"- {problem}" for problem in problems)
        raise ValueError(f"incomplete or invalid EXPLAIN ANALYZE log:\n{details}")

    rows = [query_row(query) for query in queries.values()]
    total_execution = sum(row["total_execution_ms"] for row in rows)
    total_planning = sum(row["total_planning_ms"] for row in rows)
    statement_count = sum(row["observed_occurrences"] for row in rows)
    summary = {
        **metadata,
        "observed_query_count": len(rows),
        "observed_statement_count": statement_count,
        "total_execution_ms": total_execution,
        "total_planning_ms": total_planning,
        "total_planning_plus_execution_ms": total_execution + total_planning,
        "mean_execution_ms_per_statement": (
            total_execution / statement_count if statement_count else None
        ),
        "validation_problems": problems,
        "per_query": rows,
    }

    input_path = Path(path)
    prefix = Path(output_prefix) if output_prefix else input_path.with_suffix("")
    csv_path = Path(str(prefix) + "_query_times.csv")
    json_path = Path(str(prefix) + "_timing_summary.json")
    write_csv(csv_path, rows)
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary, csv_path, json_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--expected-query-count", type=int, default=100)
    parser.add_argument("--output-prefix", type=Path)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    summary, csv_path, json_path = summarize(
        args.log,
        expected_query_count=args.expected_query_count,
        output_prefix=args.output_prefix,
        allow_incomplete=args.allow_incomplete,
    )
    print(f"Workload: {summary['workload_name']}")
    print(f"Mapping: {summary['mapping_id']}")
    print(f"Queries: {summary['observed_query_count']}")
    print(f"Statements: {summary['observed_statement_count']}")
    print(f"Total execution time: {summary['total_execution_ms']:.3f} ms")
    print(f"Total planning time: {summary['total_planning_ms']:.3f} ms")
    print(
        "Planning + execution: "
        f"{summary['total_planning_plus_execution_ms']:.3f} ms"
    )
    print(f"Per-query CSV: {csv_path}")
    print(f"JSON summary: {json_path}")


if __name__ == "__main__":
    main()
