import csv
import io
import json
import logging
import multiprocessing
import os
import glob
import time
from functools import partial
import re
import shutil
from collections import defaultdict

import psycopg2

from sql_analyzer import parse_and_analyze, new_parse
from er_graph import deserialize_graph, serialize_graph
from templatize_workload_insert_query_helper import generate_insert_statements, execute_templatized_insert,format_sql_statement
from helper_functions_extended import match_to_schema, load_data

#inserts for db initialization(node counts for each entity and relationship) is done as batch insert by templatize_insert_to_csv.py or for in-memory - templatize_insert_to_in_memory_csv.py
#this is for templatizing in an insert query which is from the query workload - not the insert queries for db initialization

#one by one insert with templatization
#templatization - node attributes are indexed - for each table to which a node does an insert, corresponding columns of the table are mapped to node attribute indexes
def insert_workload_queries_with_templatization(db_name, load_file):#todo - serialize table mappings to graph and retrieve from deserialization

    with open(load_file, "r") as f:
        data = json.load(f)
        insert_statement_file = data["insert_statements_of_query_workload"]

    sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    insert_table_attribute_names = {}
    table_index_mappings = {}

    elapsed_insert_time_ms = 0

    # Insert data
    with (open(insert_statement_file, "r") as f):
        for line in f:
            insert_statement = line.strip()
            if not insert_statement:
                continue

            parsed = new_parse(insert_statement)

            entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
            values_as_dict, index_mapping = match_to_schema(parsed["table_name"], parsed["values"], entity_or_relationship_node)
            node_index_to_attribute_mapping = {v: k for k, v in index_mapping.items()}
            #print(values_as_dict)
            relevant_tables = [table for table in tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.node_tables]]

            #for folded relationship and weak entity if their many side/parent distributed in node cover, need to add all tables in table cover as relevant tables
            #insert statement is generated to each table - but only one will result in an actual insert - that is the table where corresponding many side/parent tuple exists
            #out of all tables in node cover
            #in the db initialization insert, this was not a problem since each table in node cover did a join with temp table which was generated for folded relationship/weak entity
            if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and entity_or_relationship_node.is_contained_in_parent and
                len(entity_or_relationship_node.parent_entity.node_cover)>1):
                mapped_tables_list = [table for table in tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.mapped_tables_list]]
                relevant_tables = relevant_tables + [x for x in mapped_tables_list if x not in relevant_tables]
            if (entity_or_relationship_node.is_relationship() and graph.config[entity_or_relationship_node.unique_name] == "folded_to_many_side" and
                len(get_many_side(entity_or_relationship_node).node_cover) > 1):
                mapped_tables_list = [table for table in tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.mapped_tables_list]]
                relevant_tables = relevant_tables + [x for x in mapped_tables_list if x not in relevant_tables]

            if entity_or_relationship_node.unique_name not in table_index_mappings:
                table_index_mappings[entity_or_relationship_node.unique_name] = {}#for the node, attribute index mapping for each table to which node makes an insert
                insert_data = generate_insert_statements(entity_or_relationship_node, values_as_dict, index_mapping, relevant_tables, types, graph,
                                                                  insert_table_attribute_names, table_index_mappings[entity_or_relationship_node.unique_name])
            else:
                insert_data = execute_templatized_insert(graph, entity_or_relationship_node, values_as_dict,
                                           table_index_mappings[entity_or_relationship_node.unique_name], node_index_to_attribute_mapping, relevant_tables)
            if insert_data:
                print(entity_or_relationship_node.unique_name)
                if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and entity_or_relationship_node.is_contained_in_parent and
                        len(entity_or_relationship_node.parent_entity.node_cover)>1):
                    #no mvd inserts since any mvd attribute of folded weak entity is also CIP
                    #does an insert to each table in which parent is distributed - but only one insert should go through corresponding to table
                    #in which parent tuple exists out of all tables in node cover
                    row_counts = 0
                    for statement, values in insert_data:
                        print("---- Running query on database:")
                        #logging.debug(f"Inserting statement: {statement}, values: {values}")
                        formatted_statement = format_sql_statement(statement, values)
                        #logging.debug(f"Inserting Formatted Statement: {formatted_statement}")
                        print(formatted_statement)
                        start = time.perf_counter()
                        cursor.execute(formatted_statement)
                        conn.commit()
                        end = time.perf_counter()
                        row_counts += cursor.rowcount
                        elapsed_ms = (end - start) * 1000
                        elapsed_insert_time_ms += elapsed_ms
                        print(f"Execution Time: {elapsed_ms} ms")
                        print("-------")
                    assert row_counts == 1#only one insert should happen corresponding to table in which parent tuple exists out of all tables in parent's node cover

                elif (entity_or_relationship_node.is_relationship()
                        and graph.config[entity_or_relationship_node.unique_name] == "folded_to_many_side"
                        and len(get_many_side(entity_or_relationship_node).node_cover) > 1
                        and not check_relationship_has_mvd_attr_in_separate_table(entity_or_relationship_node)):#no mvd inserts since no mvd in separate table
                    #does an insert to each table in which many side is distributed - but only one insert should go through corresponding to table
                    #in which relevant many side tuple exists out of all tables in many side's node cover
                    row_counts = 0
                    for statement, values in insert_data:
                        print("---- Running query on database:")
                        #logging.debug(f"Inserting statement: {statement}, values: {values}")
                        formatted_statement = format_sql_statement(statement, values)
                        #logging.debug(f"Inserting Formatted Statement: {formatted_statement}")
                        print(formatted_statement)
                        start = time.perf_counter()
                        cursor.execute(formatted_statement)
                        conn.commit()
                        end = time.perf_counter()
                        row_counts += cursor.rowcount
                        elapsed_ms = (end - start) * 1000
                        elapsed_insert_time_ms += elapsed_ms
                        print(f"Execution Time: {elapsed_ms} ms")
                        print("-------")
                    assert row_counts == 1#only one insert should happen corresponding to table in which many side tuple relevant to relationship exists out of all tables in node cover

                else:
                    for statement, values in insert_data:
                        print("---- Running query on database:")
                        #logging.debug(f"Inserting statement: {statement}, values: {values}")
                        formatted_statement = format_sql_statement(statement, values)
                        #logging.debug(f"Inserting Formatted Statement: {formatted_statement}")
                        print(formatted_statement)
                        start = time.perf_counter()
                        cursor.execute(formatted_statement)
                        conn.commit()
                        end = time.perf_counter()
                        if cursor.rowcount == 0:
                            assert is_conditions_True_for_which_may_give_zero_row_count_for_insert(graph, entity_or_relationship_node)
                        else:
                            assert cursor.rowcount == 1
                        elapsed_ms = (end - start) * 1000
                        elapsed_insert_time_ms += elapsed_ms
                        print(f"Execution Time: {elapsed_ms} ms")
                        print("-------")

    logging.debug(f"---- inserts done")

    update_nodes_relation_size_for_workload_insert_queries(graph)
    # Serialize the graph object to JSON after update
    """
    graph_json = serialize_graph(graph)
    cursor.execute("INSERT INTO erdb_objects (name, data) VALUES (%s, %s)", ("graph", graph_json))
    conn.commit()
    """
    cursor.close()
    conn.close()
    return elapsed_insert_time_ms


def propagate_workload_insert_frequency_for_inheritance_hierarchy(node):
    workload_insert_frequency = node.workload_insert_frequency
    node.strict_relation_size += node.workload_insert_frequency
    for child in node.children:
        workload_insert_frequency += propagate_workload_insert_frequency_for_inheritance_hierarchy(child)
    node.relation_size += workload_insert_frequency
    return workload_insert_frequency

#for entity/relationships/mvd attributes relation_sizes are updated after insert queries from insert query workload
def update_nodes_relation_size_for_workload_insert_queries(graph):
    for node in graph.nodes:
        if node.is_entity() and not node.is_weak_entity and not node.is_subclass and len(node.children) > 0:#root of hierarchy
            #print("node relation size before: ", node.relation_size)
            propagate_workload_insert_frequency_for_inheritance_hierarchy(node)
            #print("node relation size after: ", node.relation_size)
        elif (node.is_entity() and not node.is_subclass) or node.is_relationship() or (node.is_attribute() and node.is_multivalued):#regular entities, weak entities, relationships,
                                                                                                                                    #mvd attribute
            #print("node: ", node.unique_name)
            #print("node relation size before: ", node.relation_size)
            node.relation_size += node.workload_insert_frequency
            if node.is_entity():
                node.strict_relation_size += node.workload_insert_frequency
            #print("node relation size after: ", node.relation_size)

#for many-to-one relationship
def get_many_side(node):
    return (
        node.entity2
        if node.rel_dict['entity1']['one']
           and not node.rel_dict['entity2']['one']
        else node.entity1
    )

def check_relationship_has_mvd_attr_in_separate_table(node):
    for attribute in node.attribute_list:
        if "pk_name" not in attribute and "name" in attribute:#filter for non-pk attributes
            if attribute.get("is_in_separate_table", False):
                return True
            else:
                continue
    return False

#for folded relationship or weak entity which is folded in a node distributed in node cover, only one insert goes through corresponding to the table which contains the relevant node tuple
#corresponding to relationship/weak entity
#this is because no info about which table in node cover contains the relevant node tuple for relationship/weak entity
#so inserts statements are generated to all tables of node cover - but except for the insert to relevant table, all inserts to other tables in node cover should give row count 0
#e.g. if Product distributed in node cover and productimage weak entity contained in product - an insert will be generated for each table where product is distributed
#assume product distributed in relation_1, relation_4
#UPDATE relation_1 SET productimage = COALESCE(productimage, '[]'::jsonb) || '[{"image_id": 72321, "sort_order": 289}]'::JSONB WHERE product_id=27980
#UPDATE relation_4 SET productimage = COALESCE(productimage, '[]'::jsonb) || '[{"image_id": 72321, "sort_order": 289}]'::JSONB WHERE digitalproduct_id=27980
#of these 2 updates, only one will go through - that is the table which contains product id 27980
def is_conditions_True_for_which_may_give_zero_row_count_for_insert(graph, node):
    if node.is_entity() and node.is_weak_entity and node.is_contained_in_parent and len(node.parent_entity.node_cover)>1:
        return True
    elif node.is_relationship() and graph.config[node.unique_name] == "folded_to_many_side" and len(get_many_side(node).node_cover) > 1:
        return True
    else:
        return False



