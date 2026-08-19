#generate ((ABI,CIP,ABI)	(ABI,PBI,ABI)	(ABI,ABI,CIP)	(ABI,ABI,PBI)) for synthetic entity nodes
"""
e.g.
config["r"] = "all_by_itself"
config["r1"] = "contained_in_parent"
config["r3"] = "all_by_itself"
config["r4"] = "all_by_itself"
config["r2"] = "contained_in_parent"
config["r5"] = "all_by_itself"
config["r6"] = "all_by_itself"
config["s"] = "all_by_itself"
config["s1"] = "contained_in_parent"
config["s3"] = "all_by_itself"
config["s4"] = "all_by_itself"
config["s2"] = "contained_in_parent"
config["s5"] = "all_by_itself"
config["s6"] = "all_by_itself"
"""
#example2_synthetic.json
import json
import logging
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))

from er_graph import Graph
from sql_analyzer import parse_and_analyze


load_file = "example2_synthetic.json"

entity_graph = Graph()

def parse_entities_in_hierarchy():
    logging.debug(f"-------------creating entities and relationships")
    with open(load_file, "r") as f:
        data = json.load(f)
        create_entity_statements = data["create_entity_statements"]
        create_relationship_statements = data["create_relationship_statements"]
        #connected_subgraphs = data[data["use_connected_subgraph"]]

    for statement in create_entity_statements:
        result = parse_and_analyze(statement)
        entity_graph.add_entity(result)
        logging.debug(f"Parsed: {statement}")
        logging.debug(f"Result: {result}")

def compute_levels():
    levels = {}
    level = 0

    def compute_levels_helper(node, node_level_num):
        levels[node.unique_name] = node_level_num
        for child in node.children:
            levels[child.unique_name] = node_level_num+1
            compute_levels_helper(child, node_level_num+1)

    for entity_node in entity_graph.nodes:
        if entity_node.is_entity() and not entity_node.is_subclass and len(entity_node.children)>0:#root in hierarchies
            compute_levels_helper(entity_node, level)
    print("# Levels")
    print(levels)
    return levels

def build_level_config(level_mapping_dict):
    parse_entities_in_hierarchy()
    node_levels = compute_levels()

    config_generated = {}

    for node_name, node_level_num in node_levels.items():
        config_generated[node_name] = level_mapping_dict[node_level_num]
    return config_generated

def print_config(level_mapping):
    """
    Print config in the format:
      config["r"] = "all_by_itself"
    """
    config_generated = build_level_config(level_mapping)
    print("# Config")
    for node_name, level_mapping_name in config_generated.items():
        print(f'config["{node_name}"] = "{level_mapping_name}"')

# -------------------------------------------------------
# level-0 -> all_by_itself
# level-1 -> contained_in_parent
# level-2 -> all_by_itself
# -------------------------------------------------------
level_mapping_1 = {
    0: "all_by_itself",
    1: "contained_in_parent",
    2: "all_by_itself",
}

level_mapping_2 = {
    0: "all_by_itself",
    1: "partially_by_itself",
    2: "all_by_itself",
}

level_mapping_3 = {
    0: "all_by_itself",
    1: "all_by_itself",
    2: "contained_in_parent",
}

level_mapping_4 = {
    0: "all_by_itself",
    1: "all_by_itself",
    2: "partially_by_itself",
}

print_config(level_mapping_4)



