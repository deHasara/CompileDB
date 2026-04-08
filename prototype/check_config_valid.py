import logging
import math

import graphviz

from partition_rules import (check_conditions_for_abstract_table, check_mvd_conditions_for_folded_weak_entity, check_if_folded_weak_entity_participates_in_relationship)

def check_config_is_valid(graph, config):
    is_config_valid = True
    for key, value in config.items():
        node = graph.get_node_by_name(key)
        if value == "no_table":
            if check_conditions_for_abstract_table(node, config):
                continue
            else:
                is_config_valid = False
                break
        if node.is_entity() and node.is_weak_entity and value == "contained_in_parent":
            if (check_mvd_conditions_for_folded_weak_entity(node, config) and check_if_folded_weak_entity_participates_in_relationship(graph, node, config)):
                continue
            else:
                is_config_valid = False
                break
    return is_config_valid

