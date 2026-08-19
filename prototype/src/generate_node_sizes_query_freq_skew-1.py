import argparse
from collections import Counter, defaultdict
import importlib.util
import json
import logging
import math
from pathlib import Path
import random
import sys

import numpy as np

try:
    from compiledb_query_adapter import prepare_er_query
except ModuleNotFoundError:
    # Uploaded scratch files live one directory below the compiler modules.
    # Normal project installations keep them together and do not use this.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from compiledb_query_adapter import prepare_er_query

try:
    import sql_analyzer
except ModuleNotFoundError:
    analyzer_path = Path(__file__).with_name("sql_analyzer(1).py")
    specification = importlib.util.spec_from_file_location(
        "sql_analyzer", analyzer_path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {analyzer_path}")
    sql_analyzer = importlib.util.module_from_spec(specification)
    sys.modules["sql_analyzer"] = sql_analyzer
    specification.loader.exec_module(sql_analyzer)

from er_graph import Graph
from sql_analyzer import parse_and_analyze

random.seed(1)
np.random.seed(1)

node_sizes = {}
participation_factor_many_to_one_relationships = {}
participation_factor_many_to_many_relationships = {}
entity1_to_entity2_value_for_many_to_many_relationships = {}

def reset_dictionaries():
    node_sizes.clear()
    participation_factor_many_to_one_relationships.clear()
    participation_factor_many_to_many_relationships.clear()
    entity1_to_entity2_value_for_many_to_many_relationships.clear()

def check_if_relationship_is_1_N(node):
    if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:
        return node.entity2.unique_name, node.entity1.unique_name
    elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:
        return node.entity1.unique_name, node.entity2.unique_name
    else:#False for M:N relationship
        return False

def generate_entity1_to_entity2_value_for_many_to_many_relationships(graph):
    for node in graph.nodes:
        if node.is_relationship() and not check_if_relationship_is_1_N(node):
            entity1_to_entity2_value = random.randint(1, 3)#(1,3)
            entity1_to_entity2_value_for_many_to_many_relationships[node.unique_name] = entity1_to_entity2_value

#participation factor is defined for entity1
def generate_participation_factor_for_many_to_many_relationships(graph):
    for node in graph.nodes:
        if node.is_relationship() and not check_if_relationship_is_1_N(node):
            entity1_side_participation_factor = random.randint(1, 100)#100 is total participation - (1,100)
            entity1_side_participation_factor = entity1_side_participation_factor / 100
            participation_factor_many_to_many_relationships[node.unique_name] = entity1_side_participation_factor

#participation factor defined for many side entity
def generate_participation_factor_for_many_to_one_relationships(graph):
    for node in graph.nodes:
        if node.is_relationship() and check_if_relationship_is_1_N(node):
            many_side_participation_factor = random.randint(1, 100)#100 is total participation
            many_side_participation_factor = many_side_participation_factor / 100
            participation_factor_many_to_one_relationships[node.unique_name] = many_side_participation_factor


#non hierarchical strong entities and weak entities
def generate_node_sizes_for_non_hierarchical_entity_nodes(graph):
    for node in graph.nodes:
        if node.is_entity() and (not len(node.children)>0) and (not node.is_subclass):
            if node.is_weak_entity:
                node_sizes[node.unique_name] = random.randint(10000, 50000)#(100000, 150000)#(10000, 50000)
            else:
                node_sizes[node.unique_name] = random.randint(10000, 50000)#(100000, 250000)#(50000, 150000)#(500000, 900000)#(5000, 50000)


def generate_node_sizes_hierarchical_nodes(zipf_probabilities_for_hierarchy):
    sorted_keys = sorted(zipf_probabilities_for_hierarchy, key=lambda k: zipf_probabilities_for_hierarchy[k])
    minimum_probability_node = sorted_keys[0]
    node_sizes[minimum_probability_node] = 10**4#10**6 #set node with smallest size to 10^6
    all_nodes_sizes = node_sizes[minimum_probability_node] * 1/zipf_probabilities_for_hierarchy[minimum_probability_node] #determine total size based on that
    for node in zipf_probabilities_for_hierarchy:
        if node != minimum_probability_node:
            node_sizes[node] = math.ceil(all_nodes_sizes * zipf_probabilities_for_hierarchy[node])


def extract_inheritance_hierarchies(graph):
    hierarchies = []
    for node in graph.nodes:
        #add root for each hierarchy
        if node.is_entity() and len(node.children)>0 and not node.is_subclass and not node.is_weak_entity:
            assert not node.parent_entity
            hierarchy = []
            hierarchy.append(node.unique_name)
            hierarchies.append(hierarchy)

    def get_all_nodes_in_hierarchy(parent_node, all_nodes):
        for child in parent_node.children:
            all_nodes.append(child.unique_name)
            get_all_nodes_in_hierarchy(child, all_nodes)

    for hierarchy in hierarchies:
        root_node = graph.get_node_by_name(hierarchy[0])
        get_all_nodes_in_hierarchy(root_node, hierarchy)
    return hierarchies

def alpha_for_depth(depth):
    base = 1.2#1.0
    step = 0.1
    alpha = base + step * depth
    return min(alpha, 1.5)

def generate_zipf_for_level(parent_node, parent_node_prob_mass, depth, probabilities):
    level_nodes = []
    level_nodes.append(parent_node.unique_name)
    for child in parent_node.children:
        level_nodes.append(child.unique_name)
    random.shuffle(level_nodes)#randomly set order for zipf distribution
    k = len(level_nodes) #parent+children
    # Deeper levels can use a larger alpha - more skew.
    alpha = alpha_for_depth(depth) #depth of parent determines alpha for zip-f distribution for parent and children at that level
    weights = [1.0/(r**alpha) for r in range(1, k+1)]
    sum_weights = sum(weights)
    for i in range(len(weights)):
        weights[i] /= sum_weights
    level_nodes_weights= dict(zip(level_nodes, weights))
    # The parent's own marginal probability is its incoming probability mass multiplied by the Zipf weight assigned to it at this level.
    parent_prob = parent_node_prob_mass * level_nodes_weights[parent_node.unique_name]
    probabilities[parent_node.unique_name] = parent_prob
    for child in parent_node.children:
        generate_zipf_for_level(child, parent_node_prob_mass * level_nodes_weights[child.unique_name], depth+1, probabilities)

#method 1 for inheritance hierarchies - level by level zipf
def generate_zipf_distribution_for_hierarchy(parent_node, parent_node_prob_mass, depth, probabilities):
    return generate_zipf_for_level(parent_node, parent_node_prob_mass, depth, probabilities)

#method 1 for inheritance hierarchies - level by level zipf
def generate_zipf_distribution_for_hierarchy_method_1(hierarchy_root):
    hierarchical_zipf_probabilities = {}
    generate_zipf_distribution_for_hierarchy(hierarchy_root, 1.0, 0, hierarchical_zipf_probabilities)
    print(hierarchical_zipf_probabilities, sum(hierarchical_zipf_probabilities.values()))
    generate_node_sizes_hierarchical_nodes(hierarchical_zipf_probabilities)



#node sizes for non-leaf nodes
def generate_node_sizes_for_non_leaf_parent_nodes(parent_node_weights, sum_of_descendants_of_parent_nodes):
    for parent_node in parent_node_weights.keys():
        node_sizes[parent_node] = math.ceil(sum_of_descendants_of_parent_nodes[parent_node] * parent_node_weights[parent_node])

#for non-leaf nodes
def get_sum_of_node_sizes_of_descendants(root):
    sum_of_descendants_of_non_leaf_nodes = {}

    def get_sum_of_node_sizes_of_descendants_helper(node, sum_of_descendants_of_non_leaf_nodes):
        if len(node.children)==0:
            return node_sizes[node.unique_name]
        node_size = 0
        for child in node.children:
            node_size += get_sum_of_node_sizes_of_descendants_helper(child, sum_of_descendants_of_non_leaf_nodes)
        sum_of_descendants_of_non_leaf_nodes[node.unique_name] = node_size
        return node_size

    get_sum_of_node_sizes_of_descendants_helper(root, sum_of_descendants_of_non_leaf_nodes)
    print("sum_of_descendants_of_non_leaf_nodes: ",sum_of_descendants_of_non_leaf_nodes)
    return sum_of_descendants_of_non_leaf_nodes


#assign [0.05-2] weights to parents with weights skewed to 0.05
#Beta(α, β) with β ≫ α - If β > α, it skews left (toward 0)
#Typical choices: Beta(1, 5), Beta(1, 8), Beta(1, 10)
def skewed_weight_samples(low=0.005, high=2.0, alpha=1, beta=10, k=10):#low=0.05
    # numbers in [0,1] skewed toward 0
    x = np.random.beta(alpha, beta, size=k)
    # scale to [low, high]
    return low + x * (high - low)

#non-leaf nodes
def get_parent_nodes(root):
    parent_nodes = []

    def get_parent_nodes_helper(parent, parent_nodes):
        if len(parent.children)>0:
            parent_nodes.append(parent.unique_name)
            for child in parent.children:
                get_parent_nodes_helper(child, parent_nodes)

    get_parent_nodes_helper(root, parent_nodes)
    return parent_nodes

#parent's strict tuple count is this weight*sum of all descendants' tuples
def assign_weights_for_parents(root):
    parent_nodes = get_parent_nodes(root)
    #weight_range -> [0.05, 2]
    skewed_weights_for_parents = skewed_weight_samples(k=len(parent_nodes)).tolist()
    random.shuffle(parent_nodes)
    random.shuffle(skewed_weights_for_parents)
    parent_nodes_weights = dict(zip(parent_nodes, skewed_weights_for_parents))
    print("parent nodes weights: ",parent_nodes_weights)
    return parent_nodes_weights

def get_leaf_nodes_for_hierarchy(root):
    leaf_nodes = []

    def get_leaf_nodes_helper(parent, leaf_nodes):
        if len(parent.children)==0:
            leaf_nodes.append(parent.unique_name)
        else:
            for child in parent.children:
                get_leaf_nodes_helper(child, leaf_nodes)

    get_leaf_nodes_helper(root, leaf_nodes)
    return leaf_nodes

def generate_zipf_for_leaves(root):
    leaf_nodes = get_leaf_nodes_for_hierarchy(root)
    random.shuffle(leaf_nodes)#randomly set order for zipf distribution
    k = len(leaf_nodes)
    alpha = 2#2#3
    weights = [1.0/(r**alpha) for r in range(1, k+1)]
    sum_weights = sum(weights)
    for i in range(len(weights)):
        weights[i] /= sum_weights
    leaf_nodes_weights= dict(zip(leaf_nodes, weights))
    return leaf_nodes_weights


#method 2 for inheritance hierarchies - distribute skew for leaves - for a parent [0.05, 2] * sum of descendants with significant skew towards 0.05
def generate_zipf_distribution_for_hierarchy_method_2(hierarchy_root):
    probabilities = {}
    leaf_node_probabilities = generate_zipf_for_leaves(hierarchy_root)
    print(leaf_node_probabilities, sum(leaf_node_probabilities.values()))
    generate_node_sizes_hierarchical_nodes(leaf_node_probabilities)#generate leaf node sizes

    parent_node_weights = assign_weights_for_parents(hierarchy_root)
    sum_of_descendants_of_parent_nodes = get_sum_of_node_sizes_of_descendants(hierarchy_root)
    generate_node_sizes_for_non_leaf_parent_nodes(parent_node_weights, sum_of_descendants_of_parent_nodes)



def generate_node_data(graph):
    node_data = {}
    for node in graph.nodes:
        if node.is_entity():
            node_data[node.unique_name] = {}
            node_data[node.unique_name]["node_count"] = node_sizes.get(node.unique_name, 0)
            for attribute in node.attributes:
                if attribute.is_multivalued:
                    node_data[node.unique_name]["avg_"+attribute.name] = random.randint(1, 3)#avg number of entries for mvd attribute of entity
        elif node.is_relationship():
            node_data[node.unique_name] = {}
            if check_if_relationship_is_1_N(node):
                node_data[node.unique_name]["participation_factor"] = participation_factor_many_to_one_relationships.get(node.unique_name, 0.1)
            else:#m:n
                node_data[node.unique_name]["participation_factor"] = participation_factor_many_to_many_relationships.get(node.unique_name, 0.1)
                entity1_to_entity2_var_name = node.entity1.unique_name + "_to_" + node.entity2.unique_name
                node_data[node.unique_name][entity1_to_entity2_var_name] = entity1_to_entity2_value_for_many_to_many_relationships.get(node.unique_name, 2)
            for attribute in node.attributes:
                if attribute.is_multivalued:
                    node_data[node.unique_name]["avg_"+attribute.name] = random.randint(1, 3)#avg number of entries for mvd attribute of entity

    #json_str = json.dumps(node_data, indent=2)
    #print(json_str)
    return node_data

def write_node_data_to_load_file(load_file, node_data):
    with open(load_file) as f:
        schema_json = json.load(f)
    schema_json["node_data"] = node_data
    with open(load_file, "w") as f:
        json.dump(schema_json, f, indent=2)

#select * query frequencies in workload
def generate_select_all_query_frequencies(graph):
    query_frequencies = {}

    entities_and_relationships = [node for node in graph.nodes if node.is_entity() or node.is_relationship()]
    fraction = 1 / 1#1/6 of entities/relationships for weight-vector experiments
    k = max(1, int(len(entities_and_relationships) * fraction))
    selected = random.sample(entities_and_relationships, k)

    for node in graph.nodes:
        if node in selected:
            if node.is_entity():
                if not node.is_weak_entity:
                    query_frequencies[node.unique_name] = random.randint(1, 1)#(20,30)
                else:
                    query_frequencies[node.unique_name] = random.randint(1, 1)#(1,10)
            elif node.is_relationship():
                query_frequencies[node.unique_name] = random.randint(1, 1)#(1,5)
    return query_frequencies

#insert frequencies in workload
def generate_insert_query_frequencies(graph):
    query_frequencies = {}

    entities_and_relationships = [node for node in graph.nodes if node.is_entity() or node.is_relationship()]
    fraction = 1 / 1#1/6 of entities/relationships for weight-vector experiments
    k = max(1, int(len(entities_and_relationships) * fraction))
    selected = random.sample(entities_and_relationships, k)

    #for node in graph.nodes:
    for node in selected:
        if node.is_entity():
            if not node.is_weak_entity:
                query_frequencies[node.unique_name] = random.randint(1, 1)#(1,20)
            else:
                query_frequencies[node.unique_name] = random.randint(1, 1)#(1,20)
        elif node.is_relationship():
            query_frequencies[node.unique_name] = random.randint(1, 1)#(1,20)
    return query_frequencies


def write_query_frequencies_to_load_file(load_file, query_frequencies, queries_type):
    with open(load_file) as f:
        schema_json = json.load(f)
    schema_json[queries_type] = query_frequencies
    with open(load_file, "w") as f:
        json.dump(schema_json, f, indent=2)


def build_graph_from_schema(schema_file):
    """Parse the conceptual schema needed to bind workload SQL to E/R nodes."""
    with open(schema_file, "r") as file:
        data = json.load(file)
    graph = Graph()
    for statement in data["create_entity_statements"]:
        graph.add_entity(parse_and_analyze(statement))
    for statement in data["create_relationship_statements"]:
        graph.add_relationship(parse_and_analyze(statement))
    return graph


def count_workload_object_reads(graph, workload_file, include_zero=True):
    """Count conceptual scans in a workload using its bound E/R AST.

    Each binding is one logical read.  Consequently a self-join of Product has
    two Product reads.  Every count is multiplied by the query's ``frequency``.
    The original AST, projections, predicates, and join conditions are not
    simplified or changed.
    """
    with open(workload_file, "r") as file:
        workload = json.load(file)
    queries = workload.get("queries")
    if not isinstance(queries, list):
        raise ValueError("workload JSON must contain a queries array")
    declared_count = workload.get("query_count")
    if declared_count is not None and int(declared_count) != len(queries):
        raise ValueError(
            f"workload query_count is {declared_count}, but queries has "
            f"{len(queries)} entries"
        )

    all_object_nodes = {
        node.unique_name: node
        for node in graph.nodes
        if node.is_entity() or node.is_relationship()
    }
    total_reads = Counter()
    reads_by_kind = defaultdict(Counter)
    query_report = []
    total_frequency = 0

    for position, query in enumerate(queries, 1):
        if not isinstance(query, dict):
            raise ValueError(f"workload query {position} must be an object")
        query_id = str(query.get("id", f"Q{position:03d}"))
        sql = query.get("sql")
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError(f"{query_id} has no E/R SQL text")
        frequency = int(query.get("frequency", 1))
        if frequency < 1:
            raise ValueError(f"{query_id} frequency must be positive")

        prepared = prepare_er_query(sql, graph)
        expected_hash = query.get("canonical_template_hash")
        if expected_hash:
            from er_query_rewriter import template_fingerprint

            actual_hash = template_fingerprint(prepared.template)
            if str(expected_hash) != actual_hash:
                raise ValueError(
                    f"{query_id} canonical template hash changed: "
                    f"expected {expected_hash}, got {actual_hash}"
                )

        query_counts = Counter(binding.object_id for binding in prepared.template.bindings)
        kind_counts = defaultdict(Counter)
        for binding in prepared.template.bindings:
            if binding.object_id not in all_object_nodes:
                raise ValueError(
                    f"{query_id} references unknown object {binding.object_id!r}"
                )
            total_reads[binding.object_id] += frequency
            reads_by_kind[binding.kind][binding.object_id] += frequency
            kind_counts[binding.kind][binding.object_id] += 1
        total_frequency += frequency
        query_report.append(
            {
                "id": query_id,
                "frequency": frequency,
                "object_reads_per_occurrence": dict(sorted(query_counts.items())),
                "object_reads_by_kind_per_occurrence": {
                    kind: dict(sorted(counts.items()))
                    for kind, counts in sorted(kind_counts.items())
                },
            }
        )

    declared_frequency = workload.get("total_frequency")
    if declared_frequency is not None and int(declared_frequency) != total_frequency:
        raise ValueError(
            f"workload total_frequency is {declared_frequency}, but query "
            f"frequencies sum to {total_frequency}"
        )

    frequencies = {
        object_id: int(total_reads.get(object_id, 0))
        for object_id in sorted(all_object_nodes)
        if include_zero or total_reads.get(object_id, 0) > 0
    }
    report = {
        "workload_file": str(workload_file),
        "query_shape_count": len(queries),
        "total_query_frequency": total_frequency,
        "total_conceptual_object_reads": sum(total_reads.values()),
        "select_all_frequencies": frequencies,
        "object_reads_by_kind": {
            kind: dict(sorted(counts.items()))
            for kind, counts in sorted(reads_by_kind.items())
        },
        "queries": query_report,
    }
    return frequencies, report


def rewrite_select_all_frequencies(
        schema_file,
        workload_file,
        output_file=None,
        report_file=None,
        include_zero=True,
):
    """Write a schema copy whose select frequencies come from the workload."""
    graph = build_graph_from_schema(schema_file)
    frequencies, report = count_workload_object_reads(
        graph,
        workload_file,
        include_zero=include_zero,
    )
    with open(schema_file, "r") as file:
        schema = json.load(file)
    schema["select_all_frequencies"] = frequencies

    destination = Path(output_file) if output_file else Path(schema_file)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("w") as file:
        json.dump(schema, file, indent=2)
        file.write("\n")
    temporary.replace(destination)

    if report_file:
        report_destination = Path(report_file)
        report_destination.parent.mkdir(parents=True, exist_ok=True)
        report_temporary = report_destination.with_suffix(report_destination.suffix + ".tmp")
        with report_temporary.open("w") as file:
            json.dump(report, file, indent=2)
            file.write("\n")
        report_temporary.replace(report_destination)
    return destination, report


def init_node_sizes_and_query_frequencies(load_file, workload_file=None):
    reset_dictionaries()
    graph = Graph()

    logging.debug(f"-------------creating entities and relationships")
    with open(load_file, "r") as f:
        data = json.load(f)
        create_entity_statements = data["create_entity_statements"]
        create_relationship_statements = data["create_relationship_statements"]
        #connected_subgraphs = data[data["use_connected_subgraph"]]

    for statement in create_entity_statements:
        result = parse_and_analyze(statement)
        graph.add_entity(result)
        logging.debug(f"Parsed: {statement}")
        logging.debug(f"Result: {result}")

    for statement in create_relationship_statements:
        result = parse_and_analyze(statement)
        print(result)
        graph.add_relationship(result)
        logging.debug(f"Parsed: {statement}")
        logging.debug(f"Result: {result}")

    logging.debug(f"--------------generating db initializing node sizes")
    logging.debug(f"--------------generating hierarchical entity node sizes skew")
    hierarchies = extract_inheritance_hierarchies(graph)
    for hierarchy in hierarchies:#if er schema contains multiple hierarchies
        hierarchy_root = graph.get_node_by_name(hierarchy[0])
        #generate_zipf_distribution_for_hierarchy_method_1(hierarchy_root)
        generate_zipf_distribution_for_hierarchy_method_2(hierarchy_root)
    print(node_sizes)
    logging.debug(f"--------------generating non-hierarchical entity node sizes")
    generate_node_sizes_for_non_hierarchical_entity_nodes(graph)
    logging.debug(f"--------------generating relationship node values")
    generate_participation_factor_for_many_to_one_relationships(graph)#participation factor defined for many side
    generate_participation_factor_for_many_to_many_relationships(graph)#participation factor defined for entity1 side
    generate_entity1_to_entity2_value_for_many_to_many_relationships(graph)
    logging.debug(f"--------------generating node data")
    node_data = generate_node_data(graph)
    logging.debug(f"--------------writing node data to load file")
    write_node_data_to_load_file(load_file, node_data)
    logging.debug(f"--------------generating query frequencies")
    if workload_file is not None:
        logging.debug(
            "--------------deriving select frequencies from E/R workload ASTs"
        )
        query_frequencies, _ = count_workload_object_reads(
            graph, workload_file, include_zero=True
        )
    else:
        # Compatibility path for the original synthetic frequency generator.
        logging.debug(f"--------------generating random select * query frequencies")
        query_frequencies = generate_select_all_query_frequencies(graph)
    logging.debug(f"--------------writing select * query frequencies to load file")
    write_query_frequencies_to_load_file(load_file, query_frequencies, queries_type="select_all_frequencies")
    logging.debug(f"--------------generating insert query frequencies")
    query_frequencies = generate_insert_query_frequencies(graph)
    logging.debug(f"--------------writing insert query frequencies to load file")
    write_query_frequencies_to_load_file(load_file, query_frequencies, queries_type="insert_frequencies")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Read an E/R workload, count bound entity/relationship scans, and "
            "rewrite select_all_frequencies in a schema copy."
        )
    )
    parser.add_argument("schema", type=Path)
    parser.add_argument("workload", type=Path)
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument("--output", type=Path)
    output_group.add_argument("--in-place", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--only-accessed",
        action="store_true",
        help="omit zero-frequency conceptual objects from select_all_frequencies",
    )
    arguments = parser.parse_args()

    destination = arguments.schema if arguments.in_place else arguments.output
    written, report = rewrite_select_all_frequencies(
        arguments.schema,
        arguments.workload,
        destination,
        arguments.report,
        include_zero=not arguments.only_accessed,
    )
    print(f"Updated schema: {written}")
    print(f"Query occurrences: {report['total_query_frequency']}")
    print(f"Conceptual object reads: {report['total_conceptual_object_reads']}")
    for object_id, count in report["select_all_frequencies"].items():
        if count:
            print(f"  {object_id}: {count}")


if __name__ == "__main__":
    main()

