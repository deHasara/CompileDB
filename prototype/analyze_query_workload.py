import json
import logging

from sql_analyzer import parse_and_analyze


def analyze_db_initializing_insert_queries(graph, load_file):
    with open(load_file, "r") as f:
        data = json.load(f)
        insert_statements = data["insert_statements_for_db_initializing"]

    for insert_statement in insert_statements:
        #logging.debug(f"Insert Statement: {insert_statement}")
        parsed = parse_and_analyze(insert_statement)
        entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        entity_or_relationship_node.insert_frequency += 1
        entity_or_relationship_node.relation_size +=1

def analyze_select_queries(graph, load_file):
    with open(load_file, "r") as f:
        data = json.load(f)
        select_statements = data["select_statements_of_query_workload"]

    for select_statement in select_statements:
        parsed = parse_and_analyze(select_statement)
        entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        entity_or_relationship_node.workload_select_frequency += 1

def analyze_insert_queries(graph, load_file):
    with open(load_file, "r") as f:
        data = json.load(f)
        insert_statements = data["insert_statements_of_query_workload"]

    for insert_statement in insert_statements:
        #logging.debug(f"Insert Statement: {insert_statement}")
        parsed = parse_and_analyze(insert_statement)
        entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        entity_or_relationship_node.workload_insert_frequency += 1
        entity_or_relationship_node.relation_size +=1

#initialize cardinalities for entites(root of hierarchy or just regular strong entities), subclasses, entities which have mvds(whose entity may be a parent in a hierarchy)
def propagate_cardinality_for_inheritance_hierarchy_helper(node):#from child node to all the way top parent in hierarchy
    for child in node.children:
        if len(child.children) > 0:
            propagate_cardinality_for_inheritance_hierarchy_helper(child)
        node.relation_size += child.relation_size

def propagate_cardinality_for_inheritance_hierarchy(graph):
    for node in graph.nodes:#to retrieve multiple roots if there are multiple inheritance hierarchies
        if node.is_entity() and not node.is_weak_entity and not node.is_subclass:#not subclass clause ensures we get a root - this way it can handle multiple inheritance hierarchies
            if len(node.children) > 0:
                propagate_cardinality_for_inheritance_hierarchy_helper(node)
