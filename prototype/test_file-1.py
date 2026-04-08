from helper_functions import *
from helper_functions_extended import *

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def init_database(db_name, load_file):
    create_database_if_not_exists(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    # Table to hold the metadata as JSON -- there really should only be one row in this
    cursor.execute("CREATE TABLE erdb_objects (id serial primary key, name text, data JSONB)")

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
        graph.add_relationship(result)
        logging.debug(f"Parsed: {statement}")
        logging.debug(f"Result: {result}")


    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

    """
    start_search_for_schema(graph, load_file)
    table_mappings = generate_table_mappings(graph)
    create_tables(db_name, load_file, graph, table_mappings)
    insert_data(db_name, load_file)
    """
    logging.debug(f"--------------generating workload")
    workload_file = initialize_workload_generation(graph, load_file)
    logging.debug(f"--------------starting search for schema")
    start_search_for_schema_for_generated_workload(graph)
    logging.debug(f"node cover for nodes: ")
    print_minimum_node_cover_for_entity_nodes(graph)
    table_mappings = generate_table_mappings(graph)
    logging.debug(f"table_mappings: {table_mappings}")
    logging.debug(f"--------------generating tables")
    create_tables(db_name, load_file, graph, table_mappings)
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
    #load_workload_queries_node_costs_only(db_name, load_file)#get estimated cost without exec time for workload - workload stat only - for synthetic experiments
    load_workload_queries(db_name, workload_file)

#use pre-created workload('workload.json') to test different configurations(physical tables in db will be recreated based on config) without re-generating workload
#to run this - db with tables for workload.json should already exist in psql - which will be deserialized for testing a new config
#relation sizes are initialized and stored in each node in workload generation step only
#since this skips the workload generation and use the pre-created 'workload.json' - db information has to exist for deserialization
#usage - run init once - then run test_config for trying different greedy best config(based on # of iterations)
def test_config(db_name, load_file):

    sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)#derive serialized graph structure from db - entities/relationships are already initialized with relation sizes
    workload_file = 'workload.json'#use pre-created workload without regeneration

    create_database_if_not_exists(db_name)#need to create new db since new config will change the layout of the physical tables

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    # Table to hold the metadata as JSON -- there really should only be one row in this
    cursor.execute("CREATE TABLE erdb_objects (id serial primary key, name text, data JSONB)")

    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

    print_relation_sizes(graph)
    logging.debug(f"--------------starting search for schema")
    start_search_for_schema_for_generated_workload(graph)
    table_mappings = generate_table_mappings(graph)
    logging.debug(f"--------------generating tables")
    create_tables(db_name, load_file, graph, table_mappings)
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
    load_workload_queries(db_name, workload_file)

#do total execution time vs estimated cost comparison for more than 1 # of configurations - not determining best config - doing cost model validation for different configs for same workload
def validate_cost_model_for_configs(db_name, load_file):
    create_database_if_not_exists(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    # Table to hold the metadata as JSON -- there really should only be one row in this
    cursor.execute("CREATE TABLE erdb_objects (id serial primary key, name text, data JSONB)")

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
        graph.add_relationship(result)
        logging.debug(f"Parsed: {statement}")
        logging.debug(f"Result: {result}")


    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

    logging.debug(f"--------------generating workload")
    workload_file = initialize_workload_generation(graph, load_file)#since this generates the workload, graph is initialized with relation sizes
    logging.debug(f"--------------running different configs")
    run_different_configurations(db_name, load_file, workload_file, graph)

#The greedy algorithm is executed iteratively, with the number of iterations increasing progressively to explore improved solutions over time.
def run_progressively_increasing_iterative_greedy_algorithm(db_name, load_file):
    create_database_if_not_exists(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    # Table to hold the metadata as JSON -- there really should only be one row in this
    cursor.execute("CREATE TABLE erdb_objects (id serial primary key, name text, data JSONB)")

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
        graph.add_relationship(result)
        logging.debug(f"Parsed: {statement}")
        logging.debug(f"Result: {result}")


    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

    logging.debug(f"--------------generating workload")
    workload_file = initialize_workload_generation(graph, load_file)#since this generates the workload, graph is initialized with relation sizes
    logging.debug(f"--------------running greedy algorithm progressively increasing iterations")
    run_greedy_algorithm_for_increasing_no_of_iterations(db_name, load_file, workload_file, graph)

def main():
    parser = argparse.ArgumentParser(description="ER Shell")
    parser.add_argument("command", choices=["init", "shell", "insert", "test_config", "run_different_configs", "prog_greedy"], help="Command to execute")
    parser.add_argument("db_name", help="Database name")
    parser.add_argument("load_file", nargs="?", help="CREATE file for initialization as JSON")

    args = parser.parse_args()

    if args.command == "init" or args.command == "insert" or args.command == "test_config" or args.command == "run_different_configs" or args.command == "prog_greedy":
        if not args.load_file:
            print("A file with create table statements is required for initialization")
            return
        if args.command == "init":
            init_database(args.db_name, args.load_file)
        elif args.command == "test_config":
            test_config(args.db_name, args.load_file)
        elif args.command == "run_different_configs":#execute #of different configs for testing cost model - how well it fits the execution times
            validate_cost_model_for_configs(args.db_name, args.load_file)
        elif args.command == "prog_greedy":#execute greedy algorithm with number of iterations increasing progressively to explore
            run_progressively_increasing_iterative_greedy_algorithm(args.db_name, args.load_file)                                                      #improved solutions over time.
        else:
            insert_data(args.db_name, args.load_file)
            #insert_data(args.db_name, args.load_file)
        print(f"Database {args.db_name} initialized with data from {args.load_file}")

if __name__ == "__main__":
    main()