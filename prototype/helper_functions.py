import argparse
import copy
import csv
import glob
import io
import json
import logging
import multiprocessing
import os
import random
import statistics
import time

import psycopg2
from numpy.matlib import empty
from psycopg2 import sql
from psycopg2.extras import execute_values

from er_graph import Graph, serialize_graph, deserialize_graph
from sql_analyzer import parse_and_analyze, new_parse
from construct_create_statements1 import create_table_statements, initialize_keys, generate_table_mappings
from sql_parser import attribute_list
from initialize_attribute_list_for_node import generate_attribute_list
from analyze_query_workload import analyze_insert_queries, analyze_select_queries, propagate_cardinality_for_inheritance_hierarchy
from map_insert_statements import generate_insert_statements, format_sql_statement
#from generate_batch_insert_csv import generate_insert_statements_in_batch, aggregate_folded_weak_entity_by_table_pk
from generate_batch_insert_in_memory_csv import generate_insert_statements_in_batch, aggregate_folded_weak_entity_by_table_pk
#from map_select_queries import initialize_select_tables_for_single_entity_or_relationship, generate_select_query_for_single_entity_or_relationship, init_memoized_select_all_queries
#from map_select_queries_all_attributes_extended import initialize_select_tables_for_single_entity_or_relationship, generate_select_query_for_single_entity_or_relationship, init_memoized_select_all_queries
from map_select_queries_all_attributes_extended_for_strict_all_by_itself import initialize_select_tables_for_single_entity_or_relationship, generate_select_query_for_single_entity_or_relationship, init_memoized_attributes_and_select_all_queries
#from search_algorithm import (exhaustive_search, greedy_search, greedy_search_with_random_starts, initialize_dummy_schema_config, reset_partitioning_options_for_node,
#                              initialize_partitioning_options_for_node, heuristic_default_option, define_the_generated_physical_schema,
#                              calculate_insert_select_cost_for_single_entity_or_relationship, update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes,
#                              calculate_table_width_for_physical_tables_in_config)
from search_algorithm_all_attributes import (exhaustive_search, greedy_search,
                                             stochastic_greedy_search_with_random_starts,
                                             progressive_stochastic_greedy_search,
                                             initialize_dummy_schema_config, reset_partitioning_options_for_node,
                                             initialize_partitioning_options_for_node, heuristic_default_option,
                                             define_the_generated_physical_schema,
                                             calculate_insert_select_cost_for_entity_relationship_workload,
                                             update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes,
                                             calculate_table_width_for_physical_tables_in_config,
                                             initialize_table_cover_for_nodes, get_nodes_cost,
                                             get_folded_relationship_weak_entity_count_for_tables,
                                             progressive_stochastic_greedy_search_with_random_starts,
                                             greedy_search_with_random_starts,
                                             greedy_search_with_random_starts_for_obj_of_optimizing_for_normalized_costs)
from check_config_valid import check_config_is_valid
from check_config_valid import uct_search
from workload_generator import generate_test_data

#methods for db initialization inserts
from helper_functions_extended import insert_data_in_batches_with_csv_with_templatization, \
    insert_data_in_batches_with_templatization, insert_data_in_batches_with_templatization_parallelized, \
    insert_data_in_batches_with_csv_with_templatization_parallelized

#method for insert query workload
from templatize_workload_insert_query import insert_workload_queries_with_templatization

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def create_database_if_not_exists(db_name):
    assert db_name != "postgres", "Cannot use the default PostgreSQL database"

    # Connect to the PostgreSQL server
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="password")
    conn.autocommit = True
    cursor = conn.cursor()

    # Check if the database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    exists = cursor.fetchone()

    if exists:
        logging.debug(f"Database {db_name} already exists.. deleting and recreating")#deleting all tables - so that only db is remained

        # Connect to the existing database
        conn.close()
        conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
        cursor = conn.cursor()

        # Delete all tables from the database
        cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """)

        tables = cursor.fetchall()

        for table in tables:
            logging.debug("Dropping table: %s", table[0])
            cursor.execute(f"DROP TABLE IF EXISTS {table[0]} CASCADE")

        conn.commit()
    else:
        logging.debug(f"Database {db_name} does not exist.. creating")
        # Create the database
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))

        # Close the connection
    cursor.close()
    conn.close()

def run_tuple_count_query_for_asserting_correctness(db_name, query, entity_or_relationship_node):
    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    conn.autocommit = True
    cursor = conn.cursor()

    # Execute the query (limit 0 rows for efficiency)
    cursor.execute(f"SELECT * FROM ({query}) AS t LIMIT 0")
    num_columns = len(cursor.description)
    assert num_columns == entity_or_relationship_node.select_all_attributes_count

    """
    count_sql = f"SELECT COUNT(*) FROM ({query}) AS t" #this hangs through python script on certain queries - e.g. bundle_components - hence replaced with explain analyse
    #t0 = time.time()
    count_sql = f"SELECT COUNT(*) FROM (SELECT 1 FROM ({query}) AS q) AS t"
    cursor.execute(count_sql)
    #t1 = time.time()
    tuple_count = cursor.fetchone()[0]
    #t2 = time.time()
    #print("execute_ms", (t1-t0)*1000, "fetch_ms", (t2-t1)*1000)
    assert tuple_count == entity_or_relationship_node.relation_size
    cursor.close()
    conn.close()
    """
    count_sql = f"EXPLAIN (ANALYZE, FORMAT JSON) {query}"
    cursor.execute(count_sql)
    plan_list = cursor.fetchone()[0]
    plan = plan_list[0]['Plan']
    tuple_count = plan['Actual Rows']
    assert tuple_count == entity_or_relationship_node.relation_size
    cursor.close()
    conn.close()

    #print("tuple_count=", tuple_count)


def run_select_all_entity_or_relationship_query_helper(db_name, query, tables, types, graph, executed_nodes):
    parsed = parse_and_analyze(query)
    entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
    print(entity_or_relationship_node.unique_name)
    sql = generate_select_query_for_single_entity_or_relationship(entity_or_relationship_node, tables, types, graph)

    print("---- Running query on database:")
    if entity_or_relationship_node.unique_name not in executed_nodes:
        print(sql)
        executed_nodes.append(entity_or_relationship_node.unique_name)

    #run to check correctness of query first
    run_tuple_count_query_for_asserting_correctness(db_name, sql, entity_or_relationship_node)

    # Run the query and output the results one by one
    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    conn.autocommit = True
    cursor = conn.cursor()

    runs = 5
    runs_exec_times = []
    for i in range(runs):
        # Run EXPLAIN ANALYZE in JSON format
        cursor.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}")
        # Fetch the already-parsed result (as a Python list)
        plan_list = cursor.fetchone()[0]
        # Extract execution time from the top-level plan
        #todo - include optimization time
        execution_time = plan_list[0]["Execution Time"]
        runs_exec_times.append(execution_time)

    median_time = statistics.median(runs_exec_times)
    print(f"Execution Time: {median_time} ms")
    print("-------")
    cursor.close()
    conn.close()
    return float(median_time), entity_or_relationship_node.unique_name

def run_select_all_entity_or_relationship_query(db_name, query, tables, types, graph, select_all_nodes, query_times):
    executed_nodes = []
    if isinstance(query, list):
        for query_item in query:
            execution_time, node_name = run_select_all_entity_or_relationship_query_helper(db_name, query_item, tables, types, graph, executed_nodes)
            query_times.append(execution_time)
            select_all_nodes.append(node_name)
    else:
        execution_time, node_name = run_select_all_entity_or_relationship_query_helper(db_name, query, tables, types, graph, executed_nodes)
        query_times.append(execution_time)
        select_all_nodes.append(node_name)

#run entire workload with a single db connection - close connection after entire workload done
def run_select_all_entity_or_relationship_query_workload(db_name, queries, tables, types, graph, select_all_nodes, query_times):
    executed_nodes = []
    query_list = queries if isinstance(queries, list) else [queries]

    # Run the query and output the results one by one
    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    conn.autocommit = True
    cursor = conn.cursor()

    for query_item in query_list:
        parsed = parse_and_analyze(query_item)
        entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        print(entity_or_relationship_node.unique_name)
        sql_query = generate_select_query_for_single_entity_or_relationship(entity_or_relationship_node, tables, types, graph)

        print("---- Running query on database:")
        if entity_or_relationship_node.unique_name not in executed_nodes:
            print(sql_query)
            executed_nodes.append(entity_or_relationship_node.unique_name)

        #run to check correctness of query first
        # Execute the query (limit 0 rows for efficiency)
        cursor.execute(f"SELECT * FROM ({sql_query}) AS t LIMIT 0")
        num_columns = len(cursor.description)
        assert num_columns == entity_or_relationship_node.select_all_attributes_count

        count_sql = f"SELECT COUNT(*) FROM (SELECT 1 FROM ({sql_query}) AS q) AS t"
        t0 = time.time()
        cursor.execute(count_sql)
        t1 = time.time()
        tuple_count = cursor.fetchone()[0]
        t2 = time.time()
        print("execute_ms", (t1-t0)*1000, "fetch_ms", (t2-t1)*1000)
        assert tuple_count == entity_or_relationship_node.relation_size


        runs = 5
        runs_exec_times = []
        for i in range(runs):
            # Run EXPLAIN ANALYZE in JSON format
            t0 = time.time()
            cursor.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {sql_query}")
            t1 = time.time()
            # Fetch the already-parsed result (as a Python list)
            plan_list = cursor.fetchone()[0]
            t2 = time.time()
            print("execute_ms", (t1-t0)*1000, "fetch_ms", (t2-t1)*1000)
            # Extract execution time from the top-level plan
            #todo - include optimization time
            execution_time = plan_list[0]["Execution Time"]
            jit_time = plan_list[0].get("JIT", {}).get("Total", 0)
            print("jit time", jit_time)
            runs_exec_times.append(execution_time)

        median_time = statistics.median(runs_exec_times)
        print(f"Execution Time: {median_time} ms")
        print("-------")
        query_times.append(float(median_time))
        select_all_nodes.append(entity_or_relationship_node.unique_name)
    cursor.close()
    conn.close()

#get db initialization exec times for chosen schema
def get_db_initialization_exec_times():
    insert_time = 0
    folded_weak_entity_relationship_insert_time = 0

    with open("db-initialization-exec-times.csv", mode="r") as f:
        reader = csv.reader(f)

        header = next(reader)  # skip header
        row = next(reader)     # get the only data row

        insert_time = float(row[0])
        folded_weak_entity_relationship_insert_time = float(row[1])

    return insert_time, folded_weak_entity_relationship_insert_time


def write_output_to_csv(config, cost, individual_node_cost, select_all_nodes, query_times, insert_workload_total_time, total_time, include_db_initialization=False):
    with open('output.csv', 'a') as f:
        config_line = ','.join(f'{k}:{v}' for k, v in config.items())
        f.write(config_line + '\n')
        #individual_node_cost_line = ','.join(f'{k}:{v}' for k, v in individual_node_cost.items())
        #f.write(f'individual nodes cost: {individual_node_cost_line}\n')

        #extract estimated costs for db initialization for selected schema
        db_initialization_keys = ["db_initialization_insert_cost", "db_initialization_folded_weak_entity_relationship_insert_cost"]#first print these 2 in the line of output.csv
        db_initialization_costs = [
            (k, individual_node_cost[k])
            for k in db_initialization_keys
            if k in individual_node_cost
        ]
        if db_initialization_costs:
            db_initialization_costs_line = ', '.join(f"{k}:{v}" for k, v in db_initialization_costs)
            f.write(f'{db_initialization_costs_line}\n')

        #extract estimated cost for entire insert query workload for selected schema
        insert_query_workload_key = "workload_insert_cost"
        insert_query_workload_cost = individual_node_cost.get(insert_query_workload_key)
        if insert_query_workload_cost is not None:
            f.write(f'total insert query workload cost: {insert_query_workload_cost}\n')

        #extract estimated cost for a single select * query for each entity/relationship for selected schema
        non_select_all_query_costs_keys = db_initialization_keys + [insert_query_workload_key]
        node_costs = [
            (k, v)
            for k, v in individual_node_cost.items()
            if k not in non_select_all_query_costs_keys
        ]
        if node_costs:
            individual_node_cost_line = ','.join(f"{k}:{v}" for k, v in node_costs)
            f.write(f'select * query individual nodes cost: {individual_node_cost_line}\n')

        f.write(f'estimated total cost: {cost}\n')

        #if include_db_initialization: #flag
        if db_initialization_costs:#instead of flag - include exec times for db initialization if estimated cost for schema also included cost for db initialization
            insert_time_ms, folded_weak_entity_relationship_insert_time_ms = get_db_initialization_exec_times()
            f.write(f'db initialization insert exec time: {insert_time_ms}\n')
            f.write(f'db initialization folded nodes insert exec time: {folded_weak_entity_relationship_insert_time_ms}\n')
        f.write(f'insert workload exec time: {insert_workload_total_time}\n')
        f.write(f'select * workload individual node exec time: \n')
        f.write((','.join(map(str, select_all_nodes)) if select_all_nodes else "None") + '\n')
        #f.write(','.join(map(str, select_all_nodes)) + '\n')
        f.write((','.join(map(str, query_times)) if query_times else "None") + '\n')
        #f.write(','.join(map(str, query_times)) + '\n')
        f.write(f'{total_time}\n')
        f.write('\n')

def load_select_all_queries(db_name, workload_file):
    with open(workload_file, "r") as f:
        data = json.load(f)
        select_statements = data["select_statements_of_query_workload"]

    sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)

    select_all_nodes = []
    query_times = []
    select_all_queries_total_time = 0

    run_select_all_entity_or_relationship_query(db_name, select_statements, tables, types, graph, select_all_nodes, query_times)
    #run entire workload with a single db connection - close connection after entire workload done
    #run_select_all_entity_or_relationship_query_workload(db_name, select_statements, tables, types, graph, select_all_nodes, query_times)
    select_all_queries_total_time = sum(query_times)

    return select_all_nodes, query_times, select_all_queries_total_time

#for example2_synthetic.json workload - assume workload consists of only select * queries
def load_workload_queries_node_costs_only(db_name, load_file, include_db_initialization_cost=False):

    def write_output_to_csv_node_costs_only(config, cost, individual_node_cost, select_all_nodes):
        with open('output.csv', 'a') as f:
            config_line = ','.join(f'{k}:{v}' for k, v in config.items())
            f.write(config_line + '\n')
            #individual_node_cost_line = ','.join(f'{k}:{v}' for k, v in individual_node_cost.items())
            #f.write(f'individual nodes cost: {individual_node_cost_line}\n')

            #extract estimated costs for db initialization for selected schema
            db_initialization_keys = ["db_initialization_insert_cost", "db_initialization_folded_weak_entity_relationship_insert_cost"]#first print these 2 in the line of output.csv
            db_initialization_costs = [
                (k, individual_node_cost[k])
                for k in db_initialization_keys
                if k in individual_node_cost
            ]
            if db_initialization_costs:
                db_initialization_costs_line = ', '.join(f"{k}:{v}" for k, v in db_initialization_costs)
                f.write(f'{db_initialization_costs_line}\n')

            #extract estimated cost for entire insert query workload for selected schema
            insert_query_workload_key = "workload_insert_cost"
            insert_query_workload_cost = individual_node_cost.get(insert_query_workload_key)
            if insert_query_workload_cost is not None:
                f.write(f'total insert query workload cost: {insert_query_workload_cost}\n')

            #extract estimated cost for a single select * query for each entity/relationship for selected schema
            non_select_all_query_costs_keys = db_initialization_keys + [insert_query_workload_key]
            node_costs = [
                (k, v)
                for k, v in individual_node_cost.items()
                if k not in non_select_all_query_costs_keys
            ]
            if node_costs:
                individual_node_cost_line = ','.join(f"{k}:{v}" for k, v in node_costs)
                f.write(f'select * query individual nodes cost: {individual_node_cost_line}\n')

            f.write(f'estimated total cost: {cost}\n')

            f.write(f'select * workload individual node costs: \n')
            f.write((','.join(map(str, select_all_nodes)) if select_all_nodes else "None") + '\n')
            workload_individual_node_cost_line = [individual_node_cost[node_name] for node_name in select_all_nodes]
            f.write((','.join(map(str, workload_individual_node_cost_line)) if workload_individual_node_cost_line else "None") + '\n')
            f.write('\n')

    def get_select_all_queries_node_names(db_name, load_file):
        select_all_nodes = []

        sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)

        with open(load_file, "r") as f:
            data = json.load(f)
        for node in graph.nodes:
            if node.is_entity() or node.is_relationship():
                workload_select_frequency_for_node = data.get("select_all_frequencies").get(node.unique_name) if data.get("select_all_frequencies") else None
                if workload_select_frequency_for_node:
                    select_all_nodes.extend(
                        [node.unique_name] * workload_select_frequency_for_node
                    )
        return select_all_nodes

    #select * query workload
    logging.debug(f"--------------running select * queries")
    select_all_nodes = get_select_all_queries_node_names(db_name, load_file)
    _, _, _, graph = load_data(db_name)
    write_output_to_csv_node_costs_only(graph.config, graph.cost, graph.nodes_cost, select_all_nodes)


def load_workload_queries(db_name, workload_file, include_db_initialization_cost=False):
    total_time = 0

    if include_db_initialization_cost:
        insert_time_ms, folded_weak_entity_relationship_insert_time_ms = get_db_initialization_exec_times()
        total_time += insert_time_ms
        total_time += folded_weak_entity_relationship_insert_time_ms

    #select * query workload
    logging.debug(f"--------------running select * queries")
    select_all_nodes, query_times, select_all_queries_total_time = load_select_all_queries(db_name, workload_file)
    total_time += select_all_queries_total_time

    #insert query workload
    logging.debug(f"--------------running insert queries")
    insert_queries_total_time = insert_workload_queries_with_templatization(db_name, workload_file)
    total_time += insert_queries_total_time

    _, _, _, graph = load_data(db_name)

    write_output_to_csv(graph.config, graph.cost, graph.nodes_cost, select_all_nodes, query_times, insert_queries_total_time, total_time, include_db_initialization_cost)

    #_, _, _ = load_select_all_queries(db_name, workload_file)#run select_all queries after insert queries to assert relation size
                                                                            #are correctly modified after insert workload

    return total_time#returning total_time - for cost model validation

def initialize_memoized_attributes_and_select_all_queries_for_new_configuration():
    init_memoized_attributes_and_select_all_queries()

def load_data(db_name):
    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    conn.autocommit = True
    cursor = conn.cursor()

    # Query the erdb_objects table for tables, types, and graph
    cursor.execute("SELECT name, data FROM erdb_objects WHERE name IN ('sorted_by_dependencies_tables', 'tables', 'types', 'graph')")
    rows = cursor.fetchall()

    # Deserialize the JSON data
    for row in rows:
        name, data = row
        if name == "sorted_by_dependencies_tables": sorted_by_dependencies_tables = data
        elif name == "tables": tables = data
        elif name == "types": types = data
        elif name == "graph": graph = deserialize_graph(json.dumps(data))
        else:
            logging.debug(f"Unknown object: {name}")
            assert False

    cursor.close()
    conn.close()

    return sorted_by_dependencies_tables, tables, types, graph

def match_to_schema_helper(values, attribute_list):
    ret = {}
    for x, y in zip(values, attribute_list):#way attribute list ordered matters for mapping insert values
        y_name = y["pk_ER_name" if "pk_name" in y else "name"]
        if y.get("is_multivalued", False):#doesn't handle array of composite type
            assert isinstance(x, list), f"Expected a list for {y_name}"
            arr = [int(entry) if y.get("type", False)=="INT" else entry for entry in x ]
            ret[y_name] = arr
        elif y.get("type", False)=="COMPOSITE":
            ret[y_name] = match_to_schema_helper(list(x), y["sub_attributes"])
        else:
            if y.get("type", False)== "INT":
                ret[y_name] = int(x)
            else:
                ret[y_name] = x
    return ret

def check_if_relationship_is_between_subclasses_and_all_subclasses_in_same_table(node):#e.g. [Person, Instructor, Student, Advisor]
    pk = {}
    attr_name = None
    entity1 = node.entity1
    entity2 = node.entity2
    if entity1.is_subclass and entity2.is_subclass:
        if entity1.mapped_table == node.mapped_table and entity2.mapped_table == node.mapped_table:
            if entity1.is_parent_in_table and entity2.is_parent_in_table:
                if entity1.key.table_key[0][0] == entity2.key.table_key[0][0]:#same pk - which means subclasses from same hierarchy - this doesn't have to be that both have same immediate parent
                    return True

def check_if_relationship_is_1_N(node):
    if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:
        return True
    elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:
        return True
    else:
        return False

def match_to_schema(table_name, values, node):
    attribute_list = node.attribute_list
    return match_to_schema_helper(values, attribute_list)

#original one by one insert
def insert_data(db_name, load_file):
    with open(load_file, "r") as f:
        data = json.load(f)
        insert_statements = data["insert_statements_for_db_initializing"]

    sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    # Insert data
    for i, insert_statement in enumerate(insert_statements):
        logging.debug(f"Insert Statement: {insert_statement}")
        parsed = parse_and_analyze(insert_statement)
        entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        values_as_dict = match_to_schema(parsed["table_name"], parsed["values"], entity_or_relationship_node)
        #print(values_as_dict)
        relevant_tables = [table for table in tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.node_tables]]
        insert_data = generate_insert_statements(entity_or_relationship_node, values_as_dict, relevant_tables, types, graph)
        for _, _, statement, values in insert_data:
            logging.debug(f"Inserting statement: {statement}, values: {values}")
            formatted_statement = format_sql_statement(statement, values)
            logging.debug(f"Formatted Statement: {formatted_statement}") if (i + 1) % 1 == 0 else None
            cursor.execute(formatted_statement)
            conn.commit()

    cursor.close()
    conn.close()

    #queries = ["select * from person", "select * from instructor"]
    #run_select_all_entity_or_relationship_query(db_name, queries[0], tables, types, graph)

def delete_batch_csvs():
    # Path to the directory (change as needed)
    directory = 'data'

    # Pattern to match all .csv files
    csv_files = glob.glob(os.path.join(directory, '*.csv'))
    for file in csv_files:
        os.remove(file)

#the methods in this method -> from generate_batch_insert_csv
def insert_data_in_batches_with_csv(db_name, load_file, table_mappings):
    delete_batch_csvs()

    with open(load_file, "r") as f:#todo - modify to insert_db_initialization.sql as in helper_functions_extended
        data = json.load(f)
        insert_statements = data["insert_statements_for_db_initializing"]

    sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    insert_table_attribute_names = {}

    # Insert data
    for i, insert_statement in enumerate(insert_statements):
        #logging.debug(f"Insert Statement: {insert_statement}")
        parsed = parse_and_analyze(insert_statement)
        entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        values_as_dict = match_to_schema(parsed["table_name"], parsed["values"], entity_or_relationship_node)
        #print(values_as_dict)
        relevant_tables = [table for table in tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.node_tables]]
        insert_data = generate_insert_statements_in_batch(entity_or_relationship_node, values_as_dict, relevant_tables, types, graph, insert_table_attribute_names)#from generate_batch_insert_csv

    logging.debug(f"csv generation done")

    by_name = {t[0]: t for t in tables}
    for table_name in sorted_by_dependencies_tables:
        table = by_name.get(table_name)
        assert table is not None, "Table {} not found".format(table_name)
        print(table_name)
        #for tables with only inserts - no updates -> entities with all by itself or, entities in hierarchy, or relationships with all by itself, or mvds with all by itself
        file_path = 'data/' + table[0] + '.csv'
        columns = insert_table_attribute_names[table[0]]
        column_clause = f"({', '.join(columns)})"
        with open(file_path, 'r') as f:
            copy_sql = f"COPY {table[0]} {column_clause} FROM STDIN WITH (FORMAT CSV, NULL 'null')"
            cursor.copy_expert(copy_sql, f)
        conn.commit()

        #check if updates are associated - folded relationships(table associated with parent entity updated), folded weak entities(table associated with strong entity updated)
        assert table[0] in table_mappings
        for node_name in table_mappings[table[0]]:
            entity_or_relationship_node = graph.get_node_by_name(node_name)
            if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and graph.config.get(entity_or_relationship_node.unique_name)==
                    "contained_in_parent"):
                file_name = 'data/' + entity_or_relationship_node.unique_name + '.csv'
                temp_file_name = entity_or_relationship_node.unique_name
                columns = insert_table_attribute_names[temp_file_name]
                table_primary_keys = table[-1]
                aggregated_temp_table_name, attribute_names = aggregate_folded_weak_entity_by_table_pk(file_name, columns, table[0], table_primary_keys, node_name)#for folded weak entities - generate aggregated batch csv
                file_name = 'data/' + aggregated_temp_table_name +'.csv'
                if os.path.exists(file_name):#batch insert to temp table
                    create_temp_table_sql = f"CREATE TABLE {aggregated_temp_table_name} (LIKE {table[0]} INCLUDING ALL);"
                    cursor.execute(create_temp_table_sql)#create temp table
                    columns = attribute_names
                    column_clause = f"({', '.join(columns)})"
                    with open(file_name, 'r') as f:
                        copy_sql = f"COPY {aggregated_temp_table_name} {column_clause} FROM STDIN WITH (FORMAT CSV)"
                        cursor.copy_expert(copy_sql, f)#batch insert to temp table
                    conn.commit()
                    update_clause = []
                    set_clause = []
                    from_clause = []
                    where_clause = []
                    update_clause.append(f"{table[0]}")
                    table_primary_keys = table[-1]
                    for attribute_name in attribute_names:
                        if attribute_name not in table_primary_keys:
                            set_clause.append(f"{attribute_name} = {aggregated_temp_table_name}.{attribute_name}")
                    from_clause.append(f"{aggregated_temp_table_name}")
                    for primary_key in table_primary_keys:
                        where_clause.append(f"{table[0]}.{primary_key} = {aggregated_temp_table_name}.{primary_key}")
                    update_clause_str = ", ".join(update_clause)
                    set_clause_str = ", ".join(set_clause)
                    from_clause_str = ", ".join(from_clause)
                    where_clause_str = " AND ".join(where_clause)
                    update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                    cursor.execute(update_table_clause)
                    conn.commit()

            elif entity_or_relationship_node.is_relationship() and graph.config.get(entity_or_relationship_node.unique_name)=="folded_to_many_side":
                file_name = 'data/' + 'temp_' + table[0] + '_' + entity_or_relationship_node.unique_name +'.csv'
                if os.path.exists(file_name):#batch insert to temp table
                    temp_table_name = "temp_" + table[0] + "_" + entity_or_relationship_node.unique_name
                    create_temp_table_sql = f"CREATE TABLE {temp_table_name} (LIKE {table[0]} INCLUDING ALL);"
                    cursor.execute(create_temp_table_sql)#create temp table
                    columns = insert_table_attribute_names[temp_table_name]
                    column_clause = f"({', '.join(columns)})"
                    with open(file_name, 'r') as f:
                        copy_sql = f"COPY {temp_table_name} {column_clause} FROM STDIN WITH (FORMAT CSV)"
                        cursor.copy_expert(copy_sql, f)#batch insert to temp table
                    conn.commit()

                    #update original table from temp table by pk join
                    update_clause = []
                    set_clause = []
                    from_clause = []
                    where_clause = []

                    update_clause.append(f"{table[0]}")
                    table_primary_keys = table[-1]
                    for attribute_name in columns:
                        if attribute_name not in table_primary_keys:
                            set_clause.append(f"{attribute_name} = {temp_table_name}.{attribute_name}")
                    from_clause.append(f"{temp_table_name}")
                    for primary_key in table_primary_keys:
                        where_clause.append(f"{table[0]}.{primary_key} = {temp_table_name}.{primary_key}")
                    update_clause_str = ", ".join(update_clause)
                    set_clause_str = ", ".join(set_clause)
                    from_clause_str = ", ".join(from_clause)
                    where_clause_str = " AND ".join(where_clause)
                    update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                    cursor.execute(update_table_clause)
                    conn.commit()

    cursor.close()
    conn.close()

#in-memory csv insert - this is without templatization
def insert_data_in_batches(db_name, load_file, table_mappings):#todo - serialize table mappings to graph and retrieve from deserialization

    with open(load_file, "r") as f:
        data = json.load(f)
        insert_statements = data["insert_statements_for_db_initializing"]

    sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    insert_table_attribute_names = {}
    in_memory_csvs = {}

    # Insert data
    for i, insert_statement in enumerate(insert_statements):
        #logging.debug(f"Insert Statement: {insert_statement}")
        #parsed = parse_and_analyze(insert_statement)
        parsed = new_parse(insert_statement)
        entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        values_as_dict = match_to_schema(parsed["table_name"], parsed["values"], entity_or_relationship_node)
        #print(values_as_dict)
        relevant_tables = [table for table in tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.node_tables]]
        insert_data = generate_insert_statements_in_batch(entity_or_relationship_node, values_as_dict, relevant_tables, types, graph, insert_table_attribute_names,
                                                          in_memory_csvs)
    logging.debug(f"in memory csv generation done")
    by_name = {t[0]: t for t in tables}
    for table_name in sorted_by_dependencies_tables:
        table = by_name.get(table_name)
        #for tables with only inserts - no updates -> entities with all by itself or, entities in hierarchy, or relationships with all by itself, or mvds with all by itself
        data = in_memory_csvs[table[0]]
        # Step 1: Write to an in-memory buffer
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator='\n')
        writer.writerows(data)
        # Step 2: Reset buffer to beginning so it can be read
        buffer.seek(0)
        columns = insert_table_attribute_names[table[0]]
        column_clause = f"({', '.join(columns)})"
        copy_sql = f"COPY {table[0]} {column_clause} FROM STDIN WITH (FORMAT CSV, NULL 'null')"
        cursor.copy_expert(copy_sql, buffer)
        conn.commit()
        logging.debug(f"Inserted table: {table[0]}")
        in_memory_csvs[table[0]] = None#free memory

        #check if updates are associated - folded relationships(table associated with parent entity updated), folded weak entities(table associated with strong entity updated)
        assert table[0] in table_mappings
        for node_name in table_mappings[table[0]]:
            entity_or_relationship_node = graph.get_node_by_name(node_name)
            if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and graph.config.get(entity_or_relationship_node.unique_name)==
                    "contained_in_parent"):
                #generate aggregated data for weak entity by pks
                unaggregated_data = in_memory_csvs[entity_or_relationship_node.unique_name]
                unaggregated_columns = insert_table_attribute_names[entity_or_relationship_node.unique_name]
                table_primary_keys = table[-1]
                aggregated_temp_table_name, attribute_names = aggregate_folded_weak_entity_by_table_pk(in_memory_csvs, unaggregated_data, unaggregated_columns, table[0],
                                                                                                       table_primary_keys, node_name)#for folded weak entities - generate aggregated batch csv
                aggregated_data_key_name = "temp_aggregated_" + entity_or_relationship_node.unique_name
                aggregated_data = in_memory_csvs[aggregated_data_key_name]
                # Step 1: Write to an in-memory buffer
                buffer = io.StringIO()
                writer = csv.writer(buffer, lineterminator='\n')
                writer.writerows(aggregated_data)
                # Step 2: Reset buffer to beginning so it can be read
                buffer.seek(0)
                #batch insert to temp table
                create_temp_table_sql = f"CREATE TABLE {aggregated_temp_table_name} (LIKE {table[0]} INCLUDING ALL);"
                cursor.execute(create_temp_table_sql)#create temp table
                columns = attribute_names
                column_clause = f"({', '.join(columns)})"
                copy_sql = f"COPY {aggregated_temp_table_name} {column_clause} FROM STDIN WITH (FORMAT CSV)"
                cursor.copy_expert(copy_sql, buffer)#batch insert to temp table
                conn.commit()
                update_clause = []
                set_clause = []
                from_clause = []
                where_clause = []
                update_clause.append(f"{table[0]}")
                table_primary_keys = table[-1]
                for attribute_name in attribute_names:
                    if attribute_name not in table_primary_keys:
                        set_clause.append(f"{attribute_name} = {aggregated_temp_table_name}.{attribute_name}")
                from_clause.append(f"{aggregated_temp_table_name}")
                for primary_key in table_primary_keys:
                    where_clause.append(f"{table[0]}.{primary_key} = {aggregated_temp_table_name}.{primary_key}")
                update_clause_str = ", ".join(update_clause)
                set_clause_str = ", ".join(set_clause)
                from_clause_str = ", ".join(from_clause)
                where_clause_str = " AND ".join(where_clause)
                update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                cursor.execute(update_table_clause)
                conn.commit()
                logging.debug(f"Inserted table: {table[0]}, Inserted weak entity: {entity_or_relationship_node.unique_name}")
                in_memory_csvs[entity_or_relationship_node.unique_name] = None
                in_memory_csvs[aggregated_data_key_name] = None

            elif entity_or_relationship_node.is_relationship() and graph.config.get(entity_or_relationship_node.unique_name)=="folded_to_many_side":
                data_key_name = 'temp_' + table[0] + '_' + entity_or_relationship_node.unique_name
                data = in_memory_csvs[data_key_name]
                #batch insert to temp table
                temp_table_name = "temp_" + table[0] + "_" + entity_or_relationship_node.unique_name
                create_temp_table_sql = f"CREATE TABLE {temp_table_name} (LIKE {table[0]} INCLUDING ALL);"
                cursor.execute(create_temp_table_sql)#create temp table
                # Step 1: Write to an in-memory buffer
                buffer = io.StringIO()
                writer = csv.writer(buffer, lineterminator='\n')
                writer.writerows(data)
                # Step 2: Reset buffer to beginning so it can be read
                buffer.seek(0)
                columns = insert_table_attribute_names[temp_table_name]
                column_clause = f"({', '.join(columns)})"
                copy_sql = f"COPY {temp_table_name} {column_clause} FROM STDIN WITH (FORMAT CSV)"
                cursor.copy_expert(copy_sql, buffer)#batch insert to temp table
                conn.commit()

                #update original table from temp table by pk join
                update_clause = []
                set_clause = []
                from_clause = []
                where_clause = []

                update_clause.append(f"{table[0]}")
                table_primary_keys = table[-1]
                for attribute_name in columns:
                    if attribute_name not in table_primary_keys:
                        set_clause.append(f"{attribute_name} = {temp_table_name}.{attribute_name}")
                from_clause.append(f"{temp_table_name}")
                for primary_key in table_primary_keys:
                    where_clause.append(f"{table[0]}.{primary_key} = {temp_table_name}.{primary_key}")
                update_clause_str = ", ".join(update_clause)
                set_clause_str = ", ".join(set_clause)
                from_clause_str = ", ".join(from_clause)
                where_clause_str = " AND ".join(where_clause)
                update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                cursor.execute(update_table_clause)
                conn.commit()
                logging.debug(f"Inserted table: {table[0]}, Inserted folded relationship: {entity_or_relationship_node.unique_name}")
                in_memory_csvs[data_key_name] = None

    cursor.close()
    conn.close()


def merge_and_generate_global_in_memory_csvs(local_in_memory_csvs_list):
    in_memory_csvs = {}
    for local_in_memory_csv in local_in_memory_csvs_list:
        for k, v in local_in_memory_csv.items():
            if k in in_memory_csvs:
                in_memory_csvs[k].extend(v)
            else:
                in_memory_csvs[k] = v
    return in_memory_csvs

def generate_insert_table_attribute_names(local_insert_table_attribute_names_list):
    insert_table_attribute_names = {}
    for local_insert_table_attribute_names in local_insert_table_attribute_names_list:
        for table_name, attributes in local_insert_table_attribute_names.items():
            if table_name not in insert_table_attribute_names:
                insert_table_attribute_names[table_name] = attributes
    return insert_table_attribute_names


def parallel_worker(insert_statements_chunk, tables, types, graph):

    local_in_memory_csvs = {}
    local_insert_table_attribute_names = {}

    # Insert data
    for i, insert_statement in enumerate(insert_statements_chunk):
        #logging.debug(f"Insert Statement: {insert_statement}")
        #parsed = parse_and_analyze(insert_statement)
        parsed = new_parse(insert_statement)
        entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        values_as_dict = match_to_schema(parsed["table_name"], parsed["values"], entity_or_relationship_node)
        #print(values_as_dict)
        relevant_tables = [table for table in tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.node_tables]]
        insert_data = generate_insert_statements_in_batch(entity_or_relationship_node, values_as_dict, relevant_tables, types, graph, local_insert_table_attribute_names,
                                                          local_in_memory_csvs)

    return local_in_memory_csvs, local_insert_table_attribute_names

#in-memory csv insert - parallelized
def insert_data_in_batches_parallelized(db_name, load_file, table_mappings):#todo - serialize table mappings to graph and retrieve from deserialization

    with open(load_file, "r") as f:
        data = json.load(f)
        insert_statements = data["insert_statements_for_db_initializing"]

    sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    insert_table_attribute_names = {}
    in_memory_csvs = {}

    # Parallel processing
    n_processes = multiprocessing.cpu_count()
    chunk_size = len(insert_statements) // n_processes + 1
    chunks = [insert_statements[i:i + chunk_size] for i in range(0, len(insert_statements), chunk_size)]

    args = [(chunk, tables, types, graph) for chunk in chunks]
    logging.debug(f"-----------parallelized in-memory csv generation with {n_processes} processes")
    with multiprocessing.Pool(processes=n_processes) as pool:
        results = pool.starmap(parallel_worker, args)

    logging.debug(f"-----------gathering all local in memory csvs from {n_processes} processes")

    in_memory_csvs = merge_and_generate_global_in_memory_csvs([r[0] for r in results])
    insert_table_attribute_names = generate_insert_table_attribute_names([r[1] for r in results])

    logging.debug(f"in memory csv generation done")

    by_name = {t[0]: t for t in tables}
    for table_name in sorted_by_dependencies_tables:
        table = by_name.get(table_name)
        #for tables with only inserts - no updates -> entities with all by itself or, entities in hierarchy, or relationships with all by itself, or mvds with all by itself
        data = in_memory_csvs[table[0]]
        # Step 1: Write to an in-memory buffer
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator='\n')
        writer.writerows(data)
        # Step 2: Reset buffer to beginning so it can be read
        buffer.seek(0)
        columns = insert_table_attribute_names[table[0]]
        column_clause = f"({', '.join(columns)})"
        copy_sql = f"COPY {table[0]} {column_clause} FROM STDIN WITH (FORMAT CSV, NULL 'null')"
        cursor.copy_expert(copy_sql, buffer)
        conn.commit()
        logging.debug(f"Inserted table: {table[0]}")
        in_memory_csvs[table[0]] = None#free memory

        #updating the inserted tuples in table - caused by folded entities or relationships
        #check if updates are associated - folded relationships(table associated with parent entity updated), folded weak entities(table associated with strong entity updated)
        assert table[0] in table_mappings
        for node_name in table_mappings[table[0]]:
            entity_or_relationship_node = graph.get_node_by_name(node_name)
            if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and graph.config.get(entity_or_relationship_node.unique_name)==
                    "contained_in_parent"):
                #generate aggregated data for weak entity by pks
                unaggregated_data = in_memory_csvs[entity_or_relationship_node.unique_name]
                unaggregated_columns = insert_table_attribute_names[entity_or_relationship_node.unique_name]
                table_primary_keys = table[-1]
                aggregated_temp_table_name, attribute_names = aggregate_folded_weak_entity_by_table_pk(in_memory_csvs, unaggregated_data, unaggregated_columns, table[0],
                                                                                                       table_primary_keys, node_name)#for folded weak entities - generate aggregated batch csv
                aggregated_data_key_name = "temp_aggregated_" + entity_or_relationship_node.unique_name
                aggregated_data = in_memory_csvs[aggregated_data_key_name]
                # Step 1: Write to an in-memory buffer
                buffer = io.StringIO()
                writer = csv.writer(buffer, lineterminator='\n')
                writer.writerows(aggregated_data)
                # Step 2: Reset buffer to beginning so it can be read
                buffer.seek(0)
                #batch insert to temp table
                create_temp_table_sql = f"CREATE TABLE {aggregated_temp_table_name} (LIKE {table[0]} INCLUDING ALL);"
                cursor.execute(create_temp_table_sql)#create temp table
                columns = attribute_names
                column_clause = f"({', '.join(columns)})"
                copy_sql = f"COPY {aggregated_temp_table_name} {column_clause} FROM STDIN WITH (FORMAT CSV)"
                cursor.copy_expert(copy_sql, buffer)#batch insert to temp table
                conn.commit()
                update_clause = []
                set_clause = []
                from_clause = []
                where_clause = []
                update_clause.append(f"{table[0]}")
                table_primary_keys = table[-1]
                for attribute_name in attribute_names:
                    if attribute_name not in table_primary_keys:
                        set_clause.append(f"{attribute_name} = {aggregated_temp_table_name}.{attribute_name}")
                from_clause.append(f"{aggregated_temp_table_name}")
                for primary_key in table_primary_keys:
                    where_clause.append(f"{table[0]}.{primary_key} = {aggregated_temp_table_name}.{primary_key}")
                update_clause_str = ", ".join(update_clause)
                set_clause_str = ", ".join(set_clause)
                from_clause_str = ", ".join(from_clause)
                where_clause_str = " AND ".join(where_clause)
                update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                cursor.execute(update_table_clause)
                conn.commit()
                logging.debug(f"Inserted table: {table[0]}, Inserted weak entity: {entity_or_relationship_node.unique_name}")
                in_memory_csvs[entity_or_relationship_node.unique_name] = None
                in_memory_csvs[aggregated_data_key_name] = None

            elif entity_or_relationship_node.is_relationship() and graph.config.get(entity_or_relationship_node.unique_name)=="folded_to_many_side":
                data_key_name = 'temp_' + table[0] + '_' + entity_or_relationship_node.unique_name
                data = in_memory_csvs[data_key_name]
                #batch insert to temp table
                temp_table_name = "temp_" + table[0] + "_" + entity_or_relationship_node.unique_name
                create_temp_table_sql = f"CREATE TABLE {temp_table_name} (LIKE {table[0]} INCLUDING ALL);"
                cursor.execute(create_temp_table_sql)#create temp table
                # Step 1: Write to an in-memory buffer
                buffer = io.StringIO()
                writer = csv.writer(buffer, lineterminator='\n')
                writer.writerows(data)
                # Step 2: Reset buffer to beginning so it can be read
                buffer.seek(0)
                columns = insert_table_attribute_names[temp_table_name]
                column_clause = f"({', '.join(columns)})"
                copy_sql = f"COPY {temp_table_name} {column_clause} FROM STDIN WITH (FORMAT CSV)"
                cursor.copy_expert(copy_sql, buffer)#batch insert to temp table
                conn.commit()

                #update original table from temp table by pk join
                update_clause = []
                set_clause = []
                from_clause = []
                where_clause = []

                update_clause.append(f"{table[0]}")
                table_primary_keys = table[-1]
                for attribute_name in columns:
                    if attribute_name not in table_primary_keys:
                        set_clause.append(f"{attribute_name} = {temp_table_name}.{attribute_name}")
                from_clause.append(f"{temp_table_name}")
                for primary_key in table_primary_keys:
                    where_clause.append(f"{table[0]}.{primary_key} = {temp_table_name}.{primary_key}")
                update_clause_str = ", ".join(update_clause)
                set_clause_str = ", ".join(set_clause)
                from_clause_str = ", ".join(from_clause)
                where_clause_str = " AND ".join(where_clause)
                update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                cursor.execute(update_table_clause)
                conn.commit()
                logging.debug(f"Inserted table: {table[0]}, Inserted folded relationship: {entity_or_relationship_node.unique_name}")
                in_memory_csvs[data_key_name] = None

    cursor.close()
    conn.close()

def is_strictly_all_by_itself_nodes_in_graph(graph):
    for node in graph.nodes:
        if node.is_entity() and node.is_strictly_all_by_itself:
            return True
    return False
def create_tables(db_name, load_file, graph, table_mappings):
    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    tables, all_foreign_key_stmts, types, sorted_table_dependencies = create_table_statements(graph, table_mappings)

    # Create the types
    for x in types:
        t = types[x]

        # Check if type exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = %s
            )
        """, (x,))
        type_exists = cursor.fetchone()[0]

        if not type_exists:
            sql_statement = f"CREATE TYPE {x} AS"
            sql_statement += " (" + ", ".join([attr[0] + " " + attr[1] for attr in t]) + ")"
            logging.debug(sql_statement)
            cursor.execute(sql_statement)
        else:
            logging.debug(f"Type {x} already exists — skipping.")

    for table, table_attributes, __, __, primary_key_stmt in tables:
        columns = []
        columns.extend(f"{name} {type}" for name, type, __, __ in table_attributes)
        logging.debug(f"Columns: {columns}")
        sql_statement = f"""
CREATE TABLE {table} (
    {',\n    '.join(columns)},
    {primary_key_stmt}
);
"""
        logging.debug(sql_statement)
        cursor.execute(sql_statement)

    #pk-fk constraints on tables are relaxed
    #if not is_strictly_all_by_itself_nodes_in_graph(graph):#constraints are added only if no strictly all by itself nodes - key constraints cannot be enforced with strictly all by itself nodes
    if False:
        for sql_statement in all_foreign_key_stmts:
            logging.debug(sql_statement)
            cursor.execute(sql_statement)

    for node in graph.nodes:
        generate_attribute_list(node)#attribute_list for nodes should be initialized after create_table_statements is executed - since keys might be updated in create_table_statements
    initialize_select_tables_for_single_entity_or_relationship(graph)#this should be executed after generate_attribute_list executed for nodes and before graph serialization
                                                                    #otherwise graph wouldn't serialize select_all_tables, select_all_nodes

    tables = [(table, table_attributes, is_both_entity_relationship_in_table, primary_keys) for table, table_attributes, is_both_entity_relationship_in_table, primary_keys, primary_key_stmt in tables]

    # Serialize the objects to JSON
    sorted_table_dependencies_json = json.dumps(sorted_table_dependencies, indent=4)
    tables_json = json.dumps(tables, indent=4)
    types_json = json.dumps(types)
    graph_json = serialize_graph(graph)

    #print(json.dumps(json.loads(sorted_table_dependencies_json), indent=4))
    print(json.dumps(json.loads(tables_json), indent=4))
    #print(json.dumps(json.loads(types_json), indent=4))
    #print(json.dumps(json.loads(graph_json), indent=4))

    # Insert the serialized data into the database
    cursor.execute("INSERT INTO erdb_objects (name, data) VALUES (%s, %s)", ("sorted_by_dependencies_tables", sorted_table_dependencies_json))
    cursor.execute("INSERT INTO erdb_objects (name, data) VALUES (%s, %s)", ("tables", tables_json))
    cursor.execute("INSERT INTO erdb_objects (name, data) VALUES (%s, %s)", ("types", types_json))
    cursor.execute("INSERT INTO erdb_objects (name, data) VALUES (%s, %s)", ("graph", graph_json))

    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

#sorting the tables is important, when doing batch insert for tables, inserts should happen from the least dependent table to most dependent to not violate pk/fk constraints
def sort_tables_to_adhere_to_pk_fk_constraints(graph, table_mapping):
    tables_with_highest_mapped_node_sort_key = {}
    for table_name, mapped_node_list in table_mapping.items():
        for mapped_node_name in mapped_node_list:
            mapped_node_sort_key = graph.get_node_by_name(mapped_node_name).sort_key
            if tables_with_highest_mapped_node_sort_key.get(table_name) is not None:
                if tables_with_highest_mapped_node_sort_key[table_name] < mapped_node_sort_key:
                    tables_with_highest_mapped_node_sort_key[table_name] = mapped_node_sort_key
            else:
                tables_with_highest_mapped_node_sort_key[table_name] = mapped_node_sort_key
    sorted_table_names = sorted(tables_with_highest_mapped_node_sort_key, key=tables_with_highest_mapped_node_sort_key.get)
    return sorted_table_names


def start_search_for_schema(graph, load_file, include_db_initialization_cost=False):
    analyze_insert_queries(graph, load_file)
    analyze_select_queries(graph, load_file)
    propagate_cardinality_for_inheritance_hierarchy(graph)
    exhaustive_search(graph, include_db_initialization_cost)
    greedy_search(graph, include_db_initialization_cost)
    greedy_search_with_random_starts(graph, include_db_initialization_cost)
    greedy_search_with_random_starts_for_obj_of_optimizing_for_normalized_costs(graph)
    #uct_search(graph)

def start_search_for_schema_for_generated_workload(graph, include_db_initialization_cost=False):
    #exhaustive_search(graph, include_db_initialization_cost)
    greedy_search(graph, include_db_initialization_cost)
    #greedy_search_with_random_starts(graph, include_db_initialization_cost)
    #greedy_search_with_random_starts_for_obj_of_optimizing_for_normalized_costs(graph)

def write_output_to_csv_for_cost_model_validation_for_configs(cost, total_time):
    with open('output_cost_model.csv', 'a') as f:
        pair = (cost, total_time)
        f.write(f"{cost},{total_time}\n")

def init_csv_for_cost_model_validation_for_configs():
    with open('output_cost_model.csv', 'w', newline='') as f:#initialize file
        writer = csv.writer(f)
        writer.writerow(['est cost', 'exec time'])  # header

def write_output_to_csv_for_greedy_algorithm_with_progreesively_increasing_iterations(search_iterations, cost, total_time):
    with open('output_progressive_greedy.csv', 'a') as f:
        f.write(f"{search_iterations},{cost},{total_time}\n")

def init_csv_for_greedy_algorithm_with_progreesively_increasing_iterations():
    with open('output_progressive_greedy.csv', 'w', newline='') as f:#initialize file
        writer = csv.writer(f)
        writer.writerow(['iter count', 'est cost', 'exec time'])  # header

def execute_config(db_name, load_file, workload_file, graph, iteration, include_db_initialization_cost=False):
    if iteration != 0:#after initial run, for each config, need to delete db and recreate for new physical configuration
        create_database_if_not_exists(db_name)#need to create new db since new config will change the layout of the physical tables

        conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
        cursor = conn.cursor()

        # Table to hold the metadata as JSON -- there really should only be one row in this
        cursor.execute("CREATE TABLE erdb_objects (id serial primary key, name text, data JSONB)")

        # Commit the transaction and close the connection
        conn.commit()
        cursor.close()
        conn.close()

    logging.debug(f"--------------clearing memoized queries from previous config")
    initialize_memoized_attributes_and_select_all_queries_for_new_configuration()
    table_mappings = generate_table_mappings(graph)
    logging.debug(f"--------------generating tables")
    create_tables(db_name, load_file, graph, table_mappings)#graph with current configs/values serialized - hence deserialization gives correct values for current config
    logging.debug(f"--------------inserting data")
    #insert_data(db_name, workload_file) #-one by one insert
    #insert_data_in_batches(db_name, workload_file, table_mappings) #-in-memory batch insert
    #insert_data_in_batches_with_csv(db_name, workload_file, table_mappings)#csv batch insert
    #insert_data_in_batches_with_csv_with_templatization(db_name, workload_file, table_mappings)#csv batch insert with templatization - can use when have less memory, with ssd
    #insert_data_in_batches_with_csv_with_templatization_parallelized(db_name, workload_file, table_mappings)#csv batch insert with templatization parallelized
    #insert_data_in_batches_with_templatization(db_name, workload_file, table_mappings) #-in-memory batch insert with templatization - can use when have more memory
    insert_data_in_batches_with_templatization_parallelized(db_name, workload_file, table_mappings) #-in-memory batch insert with templatization parallelized -  more memory
    #insert_data_in_batches_parallelized(db_name, workload_file, table_mappings) #in-memory parallelized batch insert
    logging.debug(f"--------------running queries")
    #total_time = load_select_all_queries(db_name, workload_file)#inside the function, deserialize the serialized graph and reconstruct
    total_time = load_workload_queries(db_name, workload_file, include_db_initialization_cost)#inside the function, deserialize the serialized graph and reconstruct
    write_output_to_csv_for_cost_model_validation_for_configs(graph.cost, total_time)
    return

#execute random valid configs for number of iterations
def execute_valid_configs_for_no_of_iterations(db_name, load_file, workload_file, graph, include_db_initialization_cost, iterations=10000):
    reset_partitioning_options_for_node(graph)
    initialize_partitioning_options_for_node(graph)

    init_csv_for_cost_model_validation_for_configs()

    all_components = [graph_node for graph_node in graph.nodes if
                      graph_node.is_entity() or graph_node.is_relationship() or (graph_node.is_attribute() and graph_node.is_multivalued)]
    all_components_except_mvds = [graph_node for graph_node in graph.nodes if
                                  graph_node.is_entity() or graph_node.is_relationship()]#config changes are done to only entities/relationships
                                                                    #for mvds it makes sense to keep it contained in parent throughout without changing


    configs_executed = set()

    #starting config
    config = {}
    cost = 0
    for component in all_components:
        config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)#starting config is config with default options
    tables_dict = define_the_generated_physical_schema(graph, config)
    table_mappings = generate_table_mappings(graph)
    table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
    folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
    initialize_table_cover_for_nodes(graph, config)
    cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict, table_widths,
                                                    folded_weak_entity_relationship_count, include_db_initialization_cost)#cost for workload - node cost * node frequency for all nodes
    update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes(graph, config)
    graph.config = config
    graph.cost = cost
    graph.nodes_cost = get_nodes_cost()

    for iteration in range(iterations+1):#run 1(default) + iterations # of config
        if iteration==0:#initial default config
            logging.debug(f"--------------running a config")
            print("iteration# config:", iteration, config)
            execute_config(db_name, load_file, workload_file, graph, iteration, include_db_initialization_cost)#get execution time for config
            key = frozenset(config.items())   # hashable snapshot
            configs_executed.add(key)
        else:
            #index = random.randint(0, len(all_components) - 1)
            #random_component = all_components[index]
            index = random.randint(0, len(all_components_except_mvds) - 1)#in each iteration, partitioning option is changed only for entities/relationships
            random_component = all_components_except_mvds[index]
            random_partitioning_option_index = random.randint(0, len(random_component.partitioning_options)-1)
            new_config = config.copy()
            new_config[random_component.unique_name] = random_component.partitioning_options[random_partitioning_option_index]
            if check_config_is_valid(graph, new_config):
                key = frozenset(new_config.items())   # hashable snapshot
                if key not in configs_executed:
                    tables_dict = define_the_generated_physical_schema(graph, new_config)
                    table_mappings = generate_table_mappings(graph)#table mapping - each table mapped to the representative node list based on chosen config
                    table_widths = calculate_table_width_for_physical_tables_in_config(graph, new_config, table_mappings)
                    folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, new_config, table_mappings)
                    initialize_table_cover_for_nodes(graph, new_config)
                    cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, new_config, tables_dict, table_widths,
                                                                folded_weak_entity_relationship_count, include_db_initialization_cost)
                    update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes(graph, new_config)
                    graph.config = new_config
                    graph.cost = cost
                    graph.nodes_cost = get_nodes_cost()
                    logging.debug(f"--------------running a config")
                    print("iteration# config:", iteration, new_config)
                    execute_config(db_name, load_file, workload_file, graph, iteration, include_db_initialization_cost)
                    configs_executed.add(key)
                    config = new_config

def run_different_configurations(db_name, load_file, workload_file, graph, include_db_initialization_cost):
    execute_valid_configs_for_no_of_iterations(db_name, load_file, workload_file, graph, include_db_initialization_cost)


def execute_config_for_progressive_greedy(db_name, load_file, workload_file, graph, run, no_of_search_iterations):
    if run != 0:#after initial run, for each config, need to delete db and recreate for new physical configuration
        create_database_if_not_exists(db_name)#need to create new db since new config will change the layout of the physical tables

        conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
        cursor = conn.cursor()

        # Table to hold the metadata as JSON -- there really should only be one row in this
        cursor.execute("CREATE TABLE erdb_objects (id serial primary key, name text, data JSONB)")

        # Commit the transaction and close the connection
        conn.commit()
        cursor.close()
        conn.close()

    logging.debug(f"--------------clearing memoized queries from previous config")
    initialize_memoized_attributes_and_select_all_queries_for_new_configuration()
    table_mappings = generate_table_mappings(graph)
    logging.debug(f"--------------generating tables")
    create_tables(db_name, load_file, graph, table_mappings)#graph with current configs/values serialized - hence deserialization gives correct values for current config
    logging.debug(f"--------------inserting data")
    #insert_data(db_name, workload_file) #-one by one insert
    #insert_data_in_batches(db_name, workload_file, table_mappings) #-in-memory batch insert
    #insert_data_in_batches_with_csv(db_name, workload_file, table_mappings)#csv batch insert
    #insert_data_in_batches_with_csv_with_templatization(db_name, workload_file, table_mappings)#csv batch insert with templatization
    insert_data_in_batches_with_csv_with_templatization_parallelized(db_name, workload_file, table_mappings)#csv batch insert with templatization parallelized
    #insert_data_in_batches_with_templatization(db_name, workload_file, table_mappings) #-in-memory batch insert with templatization
    #insert_data_in_batches_with_templatization_parallelized(db_name, workload_file, table_mappings) #-in-memory batch insert with templatization parallelized
    #insert_data_in_batches_parallelized(db_name, workload_file, table_mappings) #in-memory parallelized batch insert
    logging.debug(f"--------------running queries")
    total_time = load_workload_queries(db_name, workload_file)#inside the function, deserialize the serialized graph and reconstruct
    write_output_to_csv_for_greedy_algorithm_with_progreesively_increasing_iterations(no_of_search_iterations, graph.cost, total_time)
    return

#can get the execution time, estimated cost for each config found by running greedy algorithm for increasing no of iterations for no_of_rounds
def run_greedy_algorithm_for_increasing_no_of_iterations(db_name, load_file, workload_file, graph, include_db_initialization_cost):
    init_csv_for_greedy_algorithm_with_progreesively_increasing_iterations()

    incremental_step = 1000
    no_of_rounds = 50#run greedy algorithm this many times - in each run, it does a search of greedy_search_iterations number of steps
    for iteration in range(no_of_rounds):
        #start with default config, run greedy algorithm for incremental_steps, find a new_config,
        #again run the greedy for incremental_steps starting from previously found config, find a new config etc. continue until no_of_rounds reached
        #progressive_stochastic_greedy_search(graph, iteration, incremental_step)
        progressive_stochastic_greedy_search_with_random_starts(graph, iteration, incremental_step)
        greedy_search_iterations = incremental_step * (iteration + 1)
        execute_config_for_progressive_greedy(db_name, load_file, workload_file, graph, iteration, greedy_search_iterations)

def print_relation_sizes(graph):
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship() or (node.is_attribute() and node.is_multivalued):
            node_strict_relation_size = getattr(node, 'strict_relation_size', 0)#strict relationsize defined for entities only
            print("node, full relation size, strict relation size: ",node.unique_name, node.relation_size,
                  node_strict_relation_size)#strict relation size is defined for hierarchy nodes(including root) only

def print_minimum_node_cover_for_entity_nodes(graph):
    for node in graph.nodes:
        if node.is_entity():
            print("node cover for node:", node.unique_name, node.node_cover)

def initialize_workload_generation(graph, load_file):
    initialize_dummy_schema_config(graph)
    table_mappings = generate_table_mappings(graph)
    initialize_keys(graph, table_mappings)
    for node in graph.nodes:
        generate_attribute_list(node)
    workload_file = generate_test_data(graph, load_file)
    print_relation_sizes(graph)
    return workload_file
