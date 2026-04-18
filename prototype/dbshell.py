import ast
import cmd
import re
import time

import psycopg2

from templatize_workload_insert_query import get_many_side, check_relationship_has_mvd_attr_in_separate_table, \
    is_conditions_True_for_which_may_give_zero_row_count_for_insert, \
    update_nodes_relation_size_for_workload_insert_queries
from templatize_workload_insert_query_helper import (generate_insert_statements, execute_templatized_insert,
                                                               format_sql_statement)
from sql_analyzer import parse_and_analyze
from map_select_queries_all_attributes_extended_for_strict_all_by_itself import \
    generate_select_query_for_single_entity_or_relationship, initialize_select_tables_for_single_entity_or_relationship
from helper_functions_extended import match_to_schema


class DBCmdLine(cmd.Cmd):
    prompt = 'comDB> '
    intro = 'Welcome to CompileDB. Type help or ? to list commands.\n'

    def __init__(self, db_name, tables, types, graph):
        super().__init__()
        self.db_name = db_name
        self.tables = tables
        self.types = types
        self.graph = graph

    def default(self, arg):#arg is query
        if "select" == arg[:6] or "insert" == arg[:6]:
            self.do_query(arg)
        else:
            return self.do_exit(arg)

    def do_exit(self, arg):
        """Exit the shell"""
        print("Exiting...")
        return True

    def do_query(self, query):#select query
        """Execute a query"""
        if "select" == query[:6]:
            self.do_select_query(query)
        elif "insert" == query[:6]:
            self.do_insert_query(query)
        return


    def do_select_query(self, query):
        parsed = parse_and_analyze(query)
        entity_or_relationship_node = [node for node in self.graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        initialize_select_tables_for_single_entity_or_relationship(self.graph)
        sql = generate_select_query_for_single_entity_or_relationship(entity_or_relationship_node, self.tables, self.types, self.graph)

        print("---- Running query on database:")
        print(sql)
        # Run the query and output the results one by one
        conn = psycopg2.connect(dbname=self.db_name, user="postgres", password="password")
        conn.autocommit = True
        cursor = conn.cursor()

        # -----------------------------------
        # Run EXPLAIN ANALYZE (JSON)
        # -----------------------------------
        explain_sql = f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}"
        cursor.execute(explain_sql)

        plan = cursor.fetchone()[0][0]   # JSON structure

        # Extract execution time
        execution_time = plan["Execution Time"]

        # Extract tuple count (actual rows at root)
        tuple_count = plan["Plan"]["Actual Rows"]

        print(f"Tuple count: {tuple_count}")
        print(f"Execution Time: {execution_time} ms")
        print("-------")

        cursor.close()
        conn.close()
        return

    def do_insert_query(self, query):
        conn = psycopg2.connect(dbname=self.db_name, user="postgres", password="password")
        cursor = conn.cursor()

        insert_table_attribute_names = {}
        table_index_mappings = {}

        elapsed_insert_time_ms = 0

        # Insert data
        parsed = self.do_parse(query)#parse_and_analyze(query)#new_parse(query)

        entity_or_relationship_node = [node for node in self.graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        values_as_dict, index_mapping = match_to_schema(parsed["table_name"], parsed["values"], entity_or_relationship_node)
        node_index_to_attribute_mapping = {v: k for k, v in index_mapping.items()}
        #print(values_as_dict)
        relevant_tables = [table for table in self.tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.node_tables]]

        #for folded relationship and weak entity if their many side/parent distributed in node cover, need to add all tables in table cover as relevant tables
        #insert statement is generated to each table - but only one will result in an actual insert - that is the table where corresponding many side/parent tuple exists
        #out of all tables in node cover
        #in the db initialization insert, this was not a problem since each table in node cover did a join with temp table which was generated for folded relationship/weak entity
        if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and entity_or_relationship_node.is_contained_in_parent and
                len(entity_or_relationship_node.parent_entity.node_cover)>1):
            mapped_tables_list = [table for table in self.tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.mapped_tables_list]]
            relevant_tables = relevant_tables + [x for x in mapped_tables_list if x not in relevant_tables]
        if (entity_or_relationship_node.is_relationship() and self.graph.config[entity_or_relationship_node.unique_name] == "folded_to_many_side" and
                len(get_many_side(entity_or_relationship_node).node_cover) > 1):
            mapped_tables_list = [table for table in self.tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.mapped_tables_list]]
            relevant_tables = relevant_tables + [x for x in mapped_tables_list if x not in relevant_tables]

        if entity_or_relationship_node.unique_name not in table_index_mappings:
            table_index_mappings[entity_or_relationship_node.unique_name] = {}#for the node, attribute index mapping for each table to which node makes an insert
            insert_data = generate_insert_statements(entity_or_relationship_node, values_as_dict, index_mapping, relevant_tables, self.types, self.graph,
                                                     insert_table_attribute_names, table_index_mappings[entity_or_relationship_node.unique_name])
        else:
            insert_data = execute_templatized_insert(self.graph, entity_or_relationship_node, values_as_dict,
                                                     table_index_mappings[entity_or_relationship_node.unique_name], node_index_to_attribute_mapping, relevant_tables)
        if insert_data:
            for statement, values in insert_data:
                print("---- Running query on database:")
                #logging.debug(f"Inserting statement: {statement}, values: {values}")
                formatted_statement = format_sql_statement(statement, values)
                #logging.debug(f"Inserting Formatted Statement: {formatted_statement}")
                print(formatted_statement)
                explain_sql = f"EXPLAIN (ANALYZE, FORMAT JSON) {formatted_statement}"
                cursor.execute(explain_sql)
                conn.commit()
                plan = cursor.fetchone()[0][0]   # JSON structure
                plan_root = plan["Plan"]
                rows_affected = plan_root["Plans"][0]["Actual Rows"]
                execution_time = plan["Execution Time"]
                print(f"Rows affected: {rows_affected}")
                print(f"Execution Time: {execution_time} ms")
                print("-------")

        update_nodes_relation_size_for_workload_insert_queries(self.graph)
        # Serialize the graph object to JSON after update
        """
        graph_json = serialize_graph(graph)
        cursor.execute("INSERT INTO erdb_objects (name, data) VALUES (%s, %s)", ("graph", graph_json))
        conn.commit()
        """
        cursor.close()
        conn.close()
        return

    def do_parse(self, stmt):
        match = re.match(r"INSERT\s+INTO\s+(\w+)\s+VALUES\s*\((.*)\)", stmt, re.IGNORECASE)
        if match:
            relation = match.group(1)
            value_str = match.group(2)

            # Safely evaluate as Python tuple
            values = list(ast.literal_eval(f"({value_str})"))
            return {
                'table_name': relation,
                'values': values
            }