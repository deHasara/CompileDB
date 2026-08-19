"""Generate one deterministic conceptual INSERT workload for DB initialization.

This builds the E/R graph from the schema and writes conceptual INSERT
statements. The resulting file is mapping-independent: reuse it when loading
every candidate relational mapping.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from construct_create_statements1 import generate_table_mappings, initialize_keys
from data_profile import ConceptualDataProfile
from er_graph import Graph
from initialize_attribute_list_for_node import generate_attribute_list
from search_algorithm_all_attributes import initialize_dummy_schema_config
from sql_analyzer import parse_and_analyze
from workload_generator import (
    generate_insert_data_for_db_initialization,
    set_generation_seed,
)


def build_er_graph(schema):
    graph = Graph()
    for statement in schema["create_entity_statements"]:
        graph.add_entity(parse_and_analyze(statement))
    for statement in schema["create_relationship_statements"]:
        graph.add_relationship(parse_and_analyze(statement))
    return graph


def initialize_generation_metadata(graph):
    """Initialize keys and canonical conceptual attribute order.

    The dummy mapping is used only because the existing project derives key and
    attribute metadata through its mapping initialization code. It does not
    make the emitted E/R INSERT workload specific to that physical mapping.
    """

    initialize_dummy_schema_config(graph)
    table_mappings = generate_table_mappings(graph)
    initialize_keys(graph, table_mappings)
    for node in graph.nodes:
        generate_attribute_list(node)


def generate(schema_path, output_directory, seed, profile_sample_size=10_000):
    schema_path = schema_path.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    insert_path = output_directory / "insert_db_initialization.sql"
    manifest_path = output_directory / "db_initialization_workload.json"
    profile_path = output_directory / "conceptual_data_profile.json"

    schema_bytes = schema_path.read_bytes()
    schema = json.loads(schema_bytes)
    graph = build_er_graph(schema)
    initialize_generation_metadata(graph)
    set_generation_seed(seed)
    data_profile = ConceptualDataProfile(
        sample_size=profile_sample_size,
        seed=seed,
    )

    generate_insert_data_for_db_initialization(
        graph,
        str(schema_path),
        output_file=str(insert_path),
        data_profile=data_profile,
    )

    # Physical relation sizes may include propagated subclass cardinalities, so
    # count emitted conceptual INSERTs directly instead of summing those sizes.
    with insert_path.open("rb") as insert_file:
        statement_count = sum(
            block.count(b"\n")
            for block in iter(lambda: insert_file.read(1024 * 1024), b"")
        )

    relation_sizes = {
        node.unique_name: node.relation_size
        for node in graph.nodes
        if node.is_entity() or node.is_relationship()
    }
    schema_sha256 = hashlib.sha256(schema_bytes).hexdigest()
    data_profile.write(
        profile_path,
        schema_sha256=schema_sha256,
        generation_seed=seed,
    )
    manifest = {
        "format_version": 1,
        "workload_type": "conceptual_db_initialization",
        "schema_source": schema_path.name,
        "schema_sha256": schema_sha256,
        "generation_seed": seed,
        # Existing mapping-aware loaders open this value directly, so use an
        # absolute path rather than assuming their working directory.
        "insert_statements_for_db_initializing": str(insert_path.resolve()),
        "conceptual_statement_count": statement_count,
        "conceptual_data_profile": str(profile_path.resolve()),
        "profile_sample_size": profile_sample_size,
        "relation_sizes": relation_sizes,
        "mapping_independent": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return insert_path, manifest_path, profile_path, statement_count


def main():
    parser = argparse.ArgumentParser(
        description="Generate the fixed E/R INSERT workload used to initialize every candidate mapping."
    )
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--profile-sample-size", type=int, default=10_000)
    args = parser.parse_args()

    insert_path, manifest_path, profile_path, statement_count = generate(
        args.schema,
        args.output_dir,
        args.seed,
        args.profile_sample_size,
    )
    print(f"Generated {statement_count} conceptual INSERT statements")
    print(f"INSERT workload: {insert_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Conceptual data profile: {profile_path}")


if __name__ == "__main__":
    main()
