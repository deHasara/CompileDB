import cmd

import psycopg2

from sql_analyzer import parse_and_analyze
from map_select_queries_all_attributes_extended_for_strict_all_by_itself import \
    generate_select_query_for_single_entity_or_relationship, initialize_select_tables_for_single_entity_or_relationship


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
        if "select" == arg[:6]:
            self.do_query(arg)
        else:
            return self.do_exit(arg)

    def do_exit(self, arg):
        """Exit the shell"""
        print("Exiting...")
        return True

    def do_query(self, query):
        """Execute a query"""

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
