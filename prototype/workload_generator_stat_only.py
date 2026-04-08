import json
import logging
import random
from faker import Faker
from er_graph import Graph, Node
from analyze_query_workload import propagate_cardinality_for_inheritance_hierarchy
from workload_generator_helper import (generate_insert_query_workload_data_entity, generate_insert_query_workload_data_weak_entity,
                                       generate_insert_query_workload_data_relationship,generate_insert_query_workload_data_relationship_M_N)

random.seed(1)


def check_if_relationship_is_1_N(node):
    if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:
        return node.entity2.unique_name, node.entity1.unique_name
    elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:
        return node.entity1.unique_name, node.entity2.unique_name
    else:#False for M:N relationship
        return False


def generate_stat_data_entity(graph, node, load_file, insert_file):#strong entity
    with open(load_file, "r") as f:
        data = json.load(f)

    node_name = node.unique_name
    node_data = data.get("node_data").get(node_name)
    node_count = node_data.get("node_count")
    node.relation_size = node_count
    node.strict_relation_size = node_count
    node.insert_frequency = node_count
    return

def generate_stat_data_weak_entity(graph, node, load_file, parent_generated_data_list, insert_file):
    with open(load_file, "r") as f:
        data = json.load(f)
    node_name = node.unique_name
    node_data = data.get("node_data").get(node_name)
    node_count = node_data.get("node_count")
    node.relation_size = node_count
    node.insert_frequency = node_count
    return

def generate_stat_data_relationship(graph, node, load_file, side_N_entity_unique_name, side_N_entity_generated_data_list_size,
                               side_1_entity_unique_name, side_1_entity_generated_data_list, insert_file):
    with open(load_file, "r") as f:
        data = json.load(f)
    node_name = node.unique_name
    node_data = data.get("node_data").get(node_name)
    participation_factor = node_data.get("participation_factor", 1)#factor of participation - is 1 if total participation - defaults to total participation if factor not given in node_data
    node_generated_data_list = []
    # total number of tuples to select from many side
    k = round(side_N_entity_generated_data_list_size * participation_factor)
    node.relation_size = k
    node.insert_frequency = k
    return

def generate_stat_data_relationship_M_N(graph, node, load_file, entity1_unique_name, entity1_generated_data_list_size,
                                        entity2_unique_name, entity2_generated_data_list_size, insert_file):

    with open(load_file, "r") as f:
        data = json.load(f)
    node_name = node.unique_name
    #node_count = data.get("node_count").get(node_name)
    node_data = data.get("node_data").get(node_name)
    participation_factor = node_data.get("participation_factor", 1)#factor of participation - is 1 if total participation - defaults to total participation if factor not given in node_data
    entity1_per_entity2_count = node_data.get(entity1_unique_name + "_to_" + entity2_unique_name)#per entity_1 tuple, on avg maps to this many entity_2 tuples - this is defined only for m:n relationships
    node_generated_data_list = []
    node_relation_size = 0
    k = round(entity1_generated_data_list_size * participation_factor)#participation factor defined for entity1

    no_of_participating_tuples_from_entity1 = k
    for i in range(no_of_participating_tuples_from_entity1):
        entity2_sample_size = random.randint(1, entity1_per_entity2_count)
        node.relation_size += entity2_sample_size
        node.insert_frequency += entity2_sample_size
    return

def generate_select_statements_for_entity_or_relationship(entity_or_relationship_unique_name, select_frequency):
    sql_statement = f"SELECT * FROM {entity_or_relationship_unique_name};"
    return [sql_statement]*select_frequency

def update_relation_size_from_propagations_of_subclasses(graph):
    propagate_cardinality_for_inheritance_hierarchy(graph)

#For a weak entity or relationship, a tuple that gets mapped to, is randomly selected.
#when assigning parent tuples(to randomly pick from) to weak entities or relationship, if the entity is a parent in a hierarchy,
# all children tuples should be included as well(in addition to parent tuples) for random selection
#e.g. if Person has weak entity dependent, all tuples from Person, Student, Instructor should be included in the pool to which a dependent tuple is matched.
def union_tuples_of_subclasses_to_participating_parents(parent_entity):
    generated_data_list_size = parent_entity.relation_size
    for child_node in parent_entity.children:
        generated_data_list_size += union_tuples_of_subclasses_to_participating_parents(child_node)

    return generated_data_list_size

def reset_workload_file():
    empty_schema = {}

    with open("workload.json", "w") as f:
        json.dump(empty_schema, f, indent=2)

def generate_insert_data_for_db_initialization(graph, load_file):

    #generate insert stat data for db initializing

    insert_file = open("insert_db_initialization.sql", "w")#resets insert_db_initialization.sql - inserts for db initialization

    for node in graph.nodes:
        if node.is_entity() and not node.is_weak_entity:
            generate_stat_data_entity(graph, node, load_file, insert_file)
            print(node.unique_name, "done")
        elif node.is_entity() and node.is_weak_entity:
            if len(node.parent_entity.children)>0:#need to include all tuples from entire hierarchy below parent_entity(all subclasses which are rooted by parent entity immediate and below )
                parent_generated_data_list_size = union_tuples_of_subclasses_to_participating_parents(node.parent_entity)
                generate_stat_data_weak_entity(graph, node, load_file, parent_generated_data_list_size, insert_file)
            else:#just include parent_entity's tuples since it doesn't have a hierarchy - only pick from entity itself for weak entity
                generate_stat_data_weak_entity(graph, node, load_file, node.parent_entity.relation_size, insert_file)
            print(node.unique_name, "done")
        elif node.is_relationship():
            if check_if_relationship_is_1_N(node):
                side_N_entity_unique_name, side_1_entity_unique_name = check_if_relationship_is_1_N(node)

                side_N_entity = graph.get_node_by_name(side_N_entity_unique_name)
                side_1_entity = graph.get_node_by_name(side_1_entity_unique_name)

                if len(side_N_entity.children)>0:#need to include all tuples from all subclasses rooted from side_N_entity
                    side_N_generated_data_list_size = union_tuples_of_subclasses_to_participating_parents(side_N_entity)
                else:#simply tuples only from entity
                    side_N_generated_data_list_size = side_N_entity.relation_size

                if len(side_1_entity.children)>0:#need to include all tuples from all subclasses rooted from side_1_entity
                    side_1_generated_data_list_size = union_tuples_of_subclasses_to_participating_parents(side_1_entity)
                else:#simply tuples only from entity
                    side_1_generated_data_list_size = side_1_entity.relation_size

                generate_stat_data_relationship(graph, node, load_file, side_N_entity_unique_name, side_N_generated_data_list_size,
                                           side_1_entity_unique_name, side_1_generated_data_list_size, insert_file)
                #for many-to-one relationships, a many side tuple can participte in relationship at most once - hence these tuples whch were selected
                #for db initialization cannot be used for generating insert workload tuples
            else:
                entity1_unique_name = node.entity1.unique_name
                entity2_unique_name = node.entity2.unique_name

                if len(node.entity1.children)>0:#entity1 belongs to a hierarchy - need to include all tuples from all subclasses rooted from entity_1
                    entity1_generated_data_list_size = union_tuples_of_subclasses_to_participating_parents(node.entity1)
                else:#simply tuples only from entity
                    entity1_generated_data_list_size = node.entity1.relation_size

                if len(node.entity2.children)>0:#entity2 belongs to a hierarchy - need to include all tuples from all subclasses rooted from entity_2
                    entity2_generated_data_list_size = union_tuples_of_subclasses_to_participating_parents(node.entity2)
                else:#simply tuples only from entity
                    entity2_generated_data_list_size = node.entity2.relation_size

                generate_stat_data_relationship_M_N(graph, node, load_file, entity1_unique_name, entity1_generated_data_list_size,
                                                                       entity2_unique_name, entity2_generated_data_list_size, insert_file)

            print(node.unique_name, "done")

    insert_file.close()

    update_relation_size_from_propagations_of_subclasses(graph)#propagate relation sizes from children to parent for inheritance hierarchies

    return

def generate_select_all_queries_for_query_workload(graph, load_file):
    #generate select * statements of query workload
    select_sql_statements = []
    with open(load_file, "r") as f:
        data = json.load(f)
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            workload_select_frequency_for_node = data.get("select_all_frequencies").get(node.unique_name) if data.get("select_all_frequencies") else None
            if workload_select_frequency_for_node:
                node.workload_select_frequency += workload_select_frequency_for_node

    return

def generate_insert_queries_for_query_workload(graph, load_file):

    with open(load_file, "r") as f:
        data = json.load(f)

    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            workload_insert_frequency_for_node = data.get("insert_frequencies").get(node.unique_name) if data.get("insert_frequencies") else None
            if workload_insert_frequency_for_node:
                node.workload_insert_frequency += workload_insert_frequency_for_node


def generate_test_stat_data(graph, load_file):
    reset_workload_file()

    #generate insert data for db initializing
    generate_insert_data_for_db_initialization(graph, load_file)
    logging.debug("---db initializing insert data generation done")

    #generate select * queries for query workload
    select_sql_statements = generate_select_all_queries_for_query_workload(graph, load_file)
    logging.debug("---select * query workload generation done")

    #generate insert queries for query workload
    generate_insert_queries_for_query_workload(graph, load_file)
    logging.debug("---insert query workload generation done")

    #write to workload file
    workload = {}
    workload["insert_statements_for_db_initializing"] = "insert_db_initialization.sql"
    workload["select_statements_of_query_workload"] = select_sql_statements
    workload["insert_statements_of_query_workload"] = "insert_query_workload.sql"
    with open('workload.json', 'w') as f:
        json.dump(workload, f, indent=4)
    return 'workload.json'


