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

from templatize_insert_to_csv import generate_insert_statements_in_batch_csv, aggregate_folded_weak_entity_by_table_pk_csv, execute_templatized_insert_to_csv
from templatize_insert_to_in_memory_csv import generate_insert_statements_in_batch, aggregate_folded_weak_entity_by_table_pk, execute_templatized_insert
from sql_analyzer import parse_and_analyze, new_parse
from er_graph import deserialize_graph
import worker_state #for the use of parallelizing csv templatize insert

#for templatizing insert - for both csv(generated files in prototype-2/data folder) and in-memory csv
"""
def match_to_schema_helper(values, attribute_list):
    ret = {}
    index_mapping = {}
    for i, (x, y) in enumerate(zip(values, attribute_list)):#way attribute list ordered matters for mapping insert values
        y_name = y["pk_ER_name" if "pk_name" in y else "name"]
        if y.get("is_multivalued", False):#doesn't handle array of composite type
            assert isinstance(x, list), f"Expected a list for {y_name}"
            arr = [int(entry) if y.get("type", False)=="INT" else entry for entry in x ]
            ret[y_name] = arr
            index_mapping[y_name] = i
        elif y.get("type", False)=="COMPOSITE":
            ret[y_name] = x
            index_mapping[y_name] = i
            #index_mapping |= sub_attribute_index_mapping
        else:
            if y.get("type", False)== "INT":
                ret[y_name] = int(x)
                index_mapping[y_name] = i
            else:
                ret[y_name] = x
                index_mapping[y_name] = i
    return ret, index_mapping
"""

def match_to_schema_helper(values, attribute_list):
    if len(values) != len(attribute_list):
        raise ValueError(
            f"Value count {len(values)} does not match "
            f"attribute count {len(attribute_list)}"
        )

    ret = {}
    index_mapping = {}

    for i, (value, attribute) in enumerate(
            zip(values, attribute_list)
    ):
        attribute_name = attribute[
            "pk_ER_name" if "pk_name" in attribute else "name"
        ]

        # Record the source position regardless of whether the value is NULL.
        index_mapping[attribute_name] = i

        if value is None:
            ret[attribute_name] = None
            continue

        attribute_type = attribute.get(
            "pk_type" if "pk_name" in attribute else "type"
        )

        if attribute.get("is_multivalued", False):
            if not isinstance(value, list):
                raise ValueError(
                    f"Expected a list for {attribute_name}, "
                    f"received {type(value).__name__}"
                )

            ret[attribute_name] = [
                None
                if entry is None
                else int(entry)
                if attribute_type in {"INT", "INTEGER"}
                else entry
                for entry in value
            ]

        elif attribute_type == "COMPOSITE":
            # Keep the tuple structure for to_pg_composite().
            ret[attribute_name] = value

        elif attribute_type in {"INT", "INTEGER"}:
            ret[attribute_name] = int(value)

        else:
            ret[attribute_name] = value

    return ret, index_mapping


def match_to_schema(table_name, values, node):
    attribute_list = node.attribute_list
    return match_to_schema_helper(values, attribute_list)

def load_data(db_name):
    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
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

def delete_batch_csvs():
    # Path to the directory (change as needed)
    directory = 'data'

    # Pattern to match all .csv files
    csv_files = glob.glob(os.path.join(directory, '*.csv'))
    for file in csv_files:
        os.remove(file)

def write_db_initialization_exec_times(elapsed_insert_time_ms, elapsed_folded_weak_entity_relationship_insert_time_ms):
    with open("db-initialization-exec-times.csv", mode="w", newline="") as f:#overwrite the file
        writer = csv.writer(f)

        # Write header
        writer.writerow([
            "insert_time_ms",
            "folded_weak_entity_relationship_insert_time_ms"
        ])

        writer.writerow([
            elapsed_insert_time_ms,
            elapsed_folded_weak_entity_relationship_insert_time_ms
        ])


def check_if_table_exists(db, table_name):
    conn_1 = psycopg2.connect(database=db, user="postgres", password="password")
    cursor_1 = conn_1.cursor()


    cursor_1.execute("""
                     SELECT EXISTS (
                         SELECT FROM information_schema.tables
                         WHERE table_schema = 'public'
                           AND table_name = %s
                     );
                     """, (table_name,))

    exists = cursor_1.fetchone()[0]

    cursor_1.close()
    conn_1.close()
    return exists

def find_all_children_rooted_at_node(node, all_entities):#immediate and not - all children
    for child in node.children:
        if len(child.children) > 0:
            find_all_children_rooted_at_node(child, all_entities)
        all_entities.add(child.unique_name)

#insert to csvs with templatization
def insert_data_in_batches_with_csv_with_templatization(db_name, load_file, table_mappings):#todo - serialize table mappings to graph and retrieve from deserialization
    delete_batch_csvs()

    with open(load_file, "r") as f:
        data = json.load(f)
        insert_statement_file = data["insert_statements_for_db_initializing"] #inserts for db initialization - no of inserts equal to node count of entity/relationship

    sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    insert_table_attribute_names = {}
    table_index_mappings = {}

    # Insert data
    with open(insert_statement_file, "r") as f:
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
            if entity_or_relationship_node.unique_name not in table_index_mappings:
                table_index_mappings[entity_or_relationship_node.unique_name] = {}
                insert_data = generate_insert_statements_in_batch_csv(entity_or_relationship_node, values_as_dict, index_mapping, relevant_tables, types, graph, insert_table_attribute_names,
                                                                      table_index_mappings[entity_or_relationship_node.unique_name])
            else:
                execute_templatized_insert_to_csv(entity_or_relationship_node, values_as_dict,
                                                  table_index_mappings[entity_or_relationship_node.unique_name], node_index_to_attribute_mapping, relevant_tables)

    logging.debug(f"csv generation done")

    elapsed_insert_time_ms = 0#insert cost for all tables in chosen schema
    elapsed_update_time_ms = 0#cost to create update-temp tables and update cost

    for table in tables:#sorted dependency order not required - pk/fk constraints are not executed because of all by itself option for inheritance hierarchy
        table_name = table[0]
        print(table_name)
        assert table is not None, "Table {} not found".format(table_name)
        #for tables with only inserts - no updates -> entities with all by itself or, entities in hierarchy, or relationships with all by itself, or mvds with all by itself
        file_path = 'data/' + table[0] + '.csv'
        if os.path.exists(file_path):#if an entity is all by itself(which means physical mapped table exists), but has no tuples from itself in the workload, no corresponding csv is generated for inserting into its mapped table
            columns = insert_table_attribute_names[table[0]]
            column_clause = f"({', '.join(columns)})"
            with open(file_path, 'r') as f:
                copy_sql = f"COPY {table[0]} {column_clause} FROM STDIN WITH (FORMAT CSV, NULL 'null')"
                start = time.perf_counter()
                cursor.copy_expert(copy_sql, f)
                conn.commit()
                end = time.perf_counter()
                elapsed_ms = (end - start) * 1000
                elapsed_insert_time_ms += elapsed_ms
            logging.debug(f"Inserted table: {table[0]}")#table_name

            #check if updates are associated - folded relationships(table associated with parent entity updated), folded weak entities(table associated with strong entity updated)
            assert table[0] in table_mappings
            for node_name in table_mappings[table[0]]:
                entity_or_relationship_node = graph.get_node_by_name(node_name)
                if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and graph.config.get(entity_or_relationship_node.unique_name)==
                        "contained_in_parent"):
                    print("updating table for node", node_name)
                    file_name = 'data/' + entity_or_relationship_node.unique_name + '.csv'
                    temp_file_name = entity_or_relationship_node.unique_name
                    columns = insert_table_attribute_names[temp_file_name]#columns from temp table
                    table_primary_keys = table[-1]
                    attribute_names = []
                    attribute_names.extend(table_primary_keys)
                    attribute_names.append(entity_or_relationship_node.unique_name)
                    aggregated_temp_table_name = "temp_" + entity_or_relationship_node.unique_name
                    if os.path.exists(file_name):#batch insert to temp table
                        if not check_if_table_exists(db_name, aggregated_temp_table_name):
                            aggregated_temp_table_name, attribute_names = aggregate_folded_weak_entity_by_table_pk_csv(file_name, columns, table[0], table_primary_keys, node_name)#for folded weak entities - generate aggregated batch csv
                            file_name = 'data/' + aggregated_temp_table_name +'.csv'
                            assert os.path.exists(file_name), f"File {file_name} does not exist"
                            create_temp_table_sql = f"CREATE TABLE {aggregated_temp_table_name} (LIKE {table[0]} INCLUDING ALL);"
                            cursor.execute(create_temp_table_sql)#create temp table
                            columns = attribute_names
                            column_clause = f"({', '.join(columns)})"
                            with open(file_name, 'r') as f:
                                copy_sql = f"COPY {aggregated_temp_table_name} {column_clause} FROM STDIN WITH (FORMAT CSV)"
                                start = time.perf_counter()
                                cursor.copy_expert(copy_sql, f)#batch insert to temp table
                                conn.commit() # commit both CREATE + COPY
                                end = time.perf_counter()
                                elapsed_ms = (end - start) * 1000
                                elapsed_update_time_ms += elapsed_ms

                        #update original table from temp table by pk join
                        update_clause = []
                        set_clause = []
                        from_clause = []
                        where_clause = []
                        index_clause = []#create index on join column of temp table - to make the join with temp table faster

                        update_clause.append(f"{table[0]}")

                        table_primary_keys = table[-1]

                        if len(entity_or_relationship_node.parent_entity.node_cover)>1:
                            assert not entity_or_relationship_node.parent_entity.is_weak_entity#should be a strong root or subclass in hierarchy - only 1 pk for parent entity
                            temp_table_pk = insert_table_attribute_names[temp_file_name][0]
                            for attribute_name in attribute_names:
                                if attribute_name not in table_primary_keys and attribute_name != temp_table_pk:
                                    set_clause.append(f"{attribute_name} = {aggregated_temp_table_name}.{attribute_name}")

                            assert len(table_primary_keys) == 1
                            where_clause.append(f"{table[0]}.{table_primary_keys[0]} = {aggregated_temp_table_name}.{temp_table_pk}")
                            index_clause.append(temp_table_pk)
                        else:
                            for attribute_name in attribute_names:
                                if attribute_name not in table_primary_keys:
                                    set_clause.append(f"{attribute_name} = {aggregated_temp_table_name}.{attribute_name}")

                            for primary_key in table_primary_keys:
                                where_clause.append(f"{table[0]}.{primary_key} = {aggregated_temp_table_name}.{primary_key}")
                                index_clause.append(primary_key)


                        #filter for tuples not relevant to parent_entity in which weak entity is folded
                        #otherwise update has to iterate through all tuples - this pushdown may reduce time for update
                        if entity_or_relationship_node.parent_entity.is_subclass and entity_or_relationship_node.parent_entity.is_contained_in_parent:
                            if len(entity_or_relationship_node.parent_entity.node_cover)>1:
                                #of all tables in which parent entity is distributed, only original parent entity's mapped table has to be filtered by only tuples belonging to
                                #parent entity or its child classes to do the update
                                #the other tables which are not parent entity's original mapped_table are the tables from CAD/ABI descendants' tables in node cover
                                #all tuples in for those table need the update since they all are belonging to parent entity entity(since they are subclasses of parent entity)
                                #the check is required to filter ancestor tuples of parent entity which may present in parent entity's original mapped_table
                                if table[0] == entity_or_relationship_node.parent_entity.mapped_table[1]:
                                    if len(entity_or_relationship_node.parent_entity.children)>0:
                                        assert "role" in insert_table_attribute_names[table[0]]
                                        # collect entity names (entity + contained children)
                                        all_entities = {entity_or_relationship_node.parent_entity.unique_name}#add entity itself
                                        #add all children rooted at node
                                        find_all_children_rooted_at_node(entity_or_relationship_node.parent_entity, all_entities)
                                        all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                        where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                                    else:#entity itself - where clause would be just role in (entity_name)
                                        #for leaf subclass contained in parent
                                        assert "role" in insert_table_attribute_names[table[0]]
                                        where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{entity_or_relationship_node.parent_entity.unique_name}')")
                            else:
                                #the check is required to filter ancestor tuples of parent which may present in parent entity's mapped_table
                                #those ancestor tuples are guaranteed to not participate in relationship
                                assert table[0] == entity_or_relationship_node.parent_entity.mapped_table[1]
                                if len(entity_or_relationship_node.parent_entity.children)>0:
                                    assert "role" in insert_table_attribute_names[table[0]]
                                    # collect entity names (entity + contained children)
                                    all_entities = {entity_or_relationship_node.parent_entity.unique_name}#add entity itself
                                    #add all children rooted at node
                                    find_all_children_rooted_at_node(entity_or_relationship_node.parent_entity, all_entities)
                                    all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                    where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                                else:#entity itself - where clause would be just role in (entity_name)
                                    #for leaf subclass contained in parent
                                    assert "role" in insert_table_attribute_names[table[0]]
                                    where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{entity_or_relationship_node.parent_entity.unique_name}')")

                        from_clause.append(f"{aggregated_temp_table_name}")

                        update_clause_str = ", ".join(update_clause)
                        set_clause_str = ", ".join(set_clause)
                        from_clause_str = ", ".join(from_clause)
                        where_clause_str = " AND ".join(where_clause)
                        index_clause_str = "(" + ", ".join(index_clause) + ")"
                        index_table_clause = f"CREATE INDEX IF NOT EXISTS {"idx_"+aggregated_temp_table_name} ON {aggregated_temp_table_name} {index_clause_str};"
                        cursor.execute(index_table_clause)
                        conn.commit()
                        update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                        start = time.perf_counter()
                        cursor.execute(update_table_clause)
                        conn.commit()
                        end = time.perf_counter()
                        elapsed_ms = (end - start) * 1000
                        elapsed_update_time_ms += elapsed_ms
                        logging.debug(f"Inserted table: {table[0]}, Inserted weak entity: {entity_or_relationship_node.unique_name}")

                elif entity_or_relationship_node.is_relationship() and graph.config.get(entity_or_relationship_node.unique_name)=="folded_to_many_side":
                    print("updating table for node", node_name)
                    file_name = 'data/' + 'temp_' + entity_or_relationship_node.unique_name +'.csv'
                    if os.path.exists(file_name):#batch insert to temp table
                        temp_table_name = "temp_" + entity_or_relationship_node.unique_name
                        columns = insert_table_attribute_names[temp_table_name]
                        if not check_if_table_exists(db_name, temp_table_name):
                            create_temp_table_sql = f"CREATE TABLE {temp_table_name} (LIKE {table[0]} INCLUDING ALL);"
                            cursor.execute(create_temp_table_sql)#create temp table
                            column_clause = f"({', '.join(columns)})"
                            with open(file_name, 'r') as f:
                                copy_sql = f"COPY {temp_table_name} {column_clause} FROM STDIN WITH (FORMAT CSV)"
                                start = time.perf_counter()
                                cursor.copy_expert(copy_sql, f)#batch insert to temp table
                                conn.commit() # commit both CREATE + COPY
                                end = time.perf_counter()
                                elapsed_ms = (end - start) * 1000
                                elapsed_update_time_ms += elapsed_ms

                        #update original table from temp table by pk join
                        update_clause = []
                        set_clause = []
                        from_clause = []
                        where_clause = []
                        index_clause = []#create index on join column of temp table - to make the join with temp table faster - otherwise will take a significant time for larger table joins

                        update_clause.append(f"{table[0]}")

                        table_primary_keys = table[-1]

                        many_side = entity_or_relationship_node.entity1 if (not entity_or_relationship_node.rel_dict['entity1']['one'] and
                                                                            entity_or_relationship_node.rel_dict['entity2']['one']) else entity_or_relationship_node.entity2
                        if len(many_side.node_cover)>1:
                            assert not many_side.is_weak_entity#should be a strong root or subclass in hierarchy - only 1 pk
                            temp_table_pk = insert_table_attribute_names[temp_table_name][0]#1 pk from many side
                            for attribute_name in columns:
                                if attribute_name not in table_primary_keys and attribute_name != temp_table_pk:#when many side is distributed, folded relationship is also distributed in
                                    #many side's node cover. Of the set of tables in which relationship is distributed, the table's pk and relationship's pk will be different
                                    #if the table's mapped node is a one from the node cover of many side node except itself.
                                    #Only need to add 1 side pk from relationship since many side is already in the table.
                                    #Has to do an extra check of attribute_name != temp_table_pk to make sure it is not the many side pk.
                                    set_clause.append(f"{attribute_name} = {temp_table_name}.{attribute_name}")

                            assert len(table_primary_keys) == 1
                            where_clause.append(f"{table[0]}.{table_primary_keys[0]} = {temp_table_name}.{temp_table_pk}")
                            index_clause.append(temp_table_pk)
                        else:
                            for attribute_name in columns:
                                if attribute_name not in table_primary_keys:
                                    set_clause.append(f"{attribute_name} = {temp_table_name}.{attribute_name}")
                            for primary_key in table_primary_keys:
                                where_clause.append(f"{table[0]}.{primary_key} = {temp_table_name}.{primary_key}")
                                index_clause.append(primary_key)

                        #filter for tuples not relevant to many_side
                        #otherwise update has to iterate through all tuples - this pushdown may reduce time for update
                        if many_side.is_subclass and many_side.is_contained_in_parent:
                            if len(many_side.node_cover)>1:
                                #of all tables in which many_side is distributed, only original many_side's mapped table has to be filtered by only tuples belonging to
                                #many_side or its child classes to do the update
                                #the other tables which are not many_side's original mapped_table are the tables from CAD/ABI descendants' tables in node cover
                                #all tuples in for those table need the update since they all are belonging to many side entity(since they are subclasses of many side)
                                #the check is required to filter parent tuples of many_side which may present in many_side's original mapped_table
                                if table[0] == many_side.mapped_table[1]:
                                    if len(many_side.children)>0:
                                        assert "role" in insert_table_attribute_names[table[0]]
                                        # collect entity names (entity + contained children)
                                        all_entities = {many_side.unique_name}#add entity itself
                                        #add all children rooted at node
                                        find_all_children_rooted_at_node(many_side, all_entities)
                                        all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                        where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                                    else:#entity itself - where clause would be just role in (entity_name)
                                        #for leaf subclass contained in parent
                                        assert "role" in insert_table_attribute_names[table[0]]
                                        where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{many_side.unique_name}')")
                            else:
                                #the check is required to filter parent tuples of many_side which may present in many_side's mapped_table
                                #those parent tuples are guaranteed to not participate in relationship
                                assert table[0] == many_side.mapped_table[1]
                                if len(many_side.children)>0:
                                    assert "role" in insert_table_attribute_names[table[0]]
                                    # collect entity names (entity + contained children)
                                    all_entities = {many_side.unique_name}#add entity itself
                                    #add all children rooted at node
                                    find_all_children_rooted_at_node(many_side, all_entities)
                                    all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                    where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                                else:#entity itself - where clause would be just role in (entity_name)
                                    #for leaf subclass contained in parent
                                    assert "role" in insert_table_attribute_names[table[0]]
                                    where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{many_side.unique_name}')")

                        from_clause.append(f"{temp_table_name}")

                        update_clause_str = ", ".join(update_clause)
                        set_clause_str = ", ".join(set_clause)
                        from_clause_str = ", ".join(from_clause)
                        where_clause_str = " AND ".join(where_clause)
                        index_clause_str = "(" + ", ".join(index_clause) + ")"
                        index_table_clause = f"CREATE INDEX IF NOT EXISTS {"idx_"+temp_table_name} ON {temp_table_name} {index_clause_str};"
                        cursor.execute(index_table_clause)
                        conn.commit()
                        update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                        start = time.perf_counter()
                        cursor.execute(update_table_clause)
                        conn.commit()
                        end = time.perf_counter()
                        elapsed_ms = (end - start) * 1000
                        elapsed_update_time_ms += elapsed_ms
                        logging.debug(f"Inserted table: {table[0]}, Inserted folded relationship: {entity_or_relationship_node.unique_name}")

    cursor.close()
    conn.close()

    #write db initialization exec times to csv
    write_db_initialization_exec_times(elapsed_insert_time_ms, elapsed_update_time_ms)


def merge_and_generate_global_csvs_from_local_csvs(data_dir="data"):#csvs are in /data folder
    """
    Finds relation_name_<id>_<worker>.csv and merges them into relation_name_<id>.csv
    in the same directory using binary concatenation.
    """
    pattern = re.compile(r"(.+)_\d+\.csv$")  # each local file ends in _<worker process id>

    groups = defaultdict(list)

    for path in glob.glob(os.path.join(data_dir, "*.csv")):
        name = os.path.basename(path)
        m = pattern.match(name)
        if m:
            relation_prefix = m.group(1)
            groups[relation_prefix].append(path)

    for relation, parts in groups.items():
        parts.sort()
        out_path = os.path.join(data_dir, f"{relation}.csv")

        with open(out_path, "wb") as out:
            for p in parts:
                with open(p, "rb") as inp:
                    shutil.copyfileobj(inp, out)

        print(f"Merged {len(parts)} files → {out_path}")

    for parts in groups.values():#remove local files made by workers after global csv files are generated
        for p in parts:
            os.remove(p)

def generate_insert_table_attribute_names_from_local_for_csv(local_insert_table_attribute_names_list):
    insert_table_attribute_names = {}
    for local_insert_table_attribute_names in local_insert_table_attribute_names_list:
        for table_name, attributes in local_insert_table_attribute_names.items():
            if table_name not in insert_table_attribute_names:
                insert_table_attribute_names[table_name] = attributes
    return insert_table_attribute_names

def parallel_worker_csv_generation(insert_statements_chunk, tables, types, graph):
    # Insert data
    #print("Starting parallel worker", worker_state.WORKER_ID)
    local_insert_table_attribute_names = {}
    local_table_index_mappings = {}

    for insert_statement in insert_statements_chunk:
        parsed = new_parse(insert_statement)

        entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        values_as_dict, index_mapping = match_to_schema(parsed["table_name"], parsed["values"], entity_or_relationship_node)
        node_index_to_attribute_mapping = {v: k for k, v in index_mapping.items()}
        #print(values_as_dict)
        relevant_tables = [table for table in tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.node_tables]]
        if entity_or_relationship_node.unique_name not in local_table_index_mappings:
            local_table_index_mappings[entity_or_relationship_node.unique_name] = {}
            insert_data = generate_insert_statements_in_batch_csv(entity_or_relationship_node, values_as_dict, index_mapping, relevant_tables, types, graph, local_insert_table_attribute_names,
                                                                  local_table_index_mappings[entity_or_relationship_node.unique_name])
        else:
            execute_templatized_insert_to_csv(entity_or_relationship_node, values_as_dict,
                                              local_table_index_mappings[entity_or_relationship_node.unique_name], node_index_to_attribute_mapping, relevant_tables)

    return local_insert_table_attribute_names

#streams, doesn't load whole file - insert_db_initialization.sql
def iter_sql_chunks(path: str, chunk_lines: int = 50000):
    chunk = []
    with open(path, "r") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            chunk.append(s)
            if len(chunk) >= chunk_lines:
                yield chunk
                chunk = []
    if chunk:
        yield chunk

def init_worker():
    worker_state.WORKER_ID = multiprocessing.current_process()._identity[0] - 1

#insert to csvs with templatization and parallelized processing the insert statements
def insert_data_in_batches_with_csv_with_templatization_parallelized(db_name, load_file, table_mappings):#todo - serialize table mappings to graph and retrieve from deserialization
    delete_batch_csvs()

    with open(load_file, "r") as f:
        data = json.load(f)
        insert_statement_file = data["insert_statements_for_db_initializing"]

    sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    insert_table_attribute_names = {}
    table_index_mappings = {}

    # Parallel processing
    n_processes = multiprocessing.cpu_count()
    chunk_lines = 100000#50000

    logging.debug(f"-----------parallelized csv generation with {n_processes} processes")
    with multiprocessing.Pool(processes=n_processes, initializer=init_worker) as pool:
        it = iter_sql_chunks(insert_statement_file, chunk_lines=chunk_lines)
        worker_fn = partial(
            parallel_worker_csv_generation,
            tables=tables,
            types=types,
            graph=graph
        )

        results_iter = pool.imap_unordered(worker_fn, it, chunksize=1)
        logging.debug(f"-----------gathering all local csvs from {n_processes} processes")
        insert_table_attribute_names = generate_insert_table_attribute_names_from_local_for_csv(list(results_iter))

    merge_and_generate_global_csvs_from_local_csvs()
    logging.debug(f"csv generation done")

    elapsed_insert_time_ms = 0#insert cost for all tables in chosen schema
    elapsed_update_time_ms = 0#cost to create update-temp tables and update cost

    for table in tables:#sorted dependency order not required - pk/fk constraints are not executed because of all by itself option for inheritance hierarchy
        table_name = table[0]
        print(table_name)
        assert table is not None, "Table {} not found".format(table_name)
        #for tables with only inserts - no updates -> entities with all by itself or, entities in hierarchy, or relationships with all by itself, or mvds with all by itself
        file_path = 'data/' + table[0] + '.csv'
        if os.path.exists(file_path):#if an entity is all by itself(which means physical mapped table exists), but has no tuples from itself in the workload, no corresponding csv is generated for inserting into its mapped table
            columns = insert_table_attribute_names[table[0]]
            column_clause = f"({', '.join(columns)})"
            with open(file_path, 'r') as f:
                copy_sql = f"COPY {table[0]} {column_clause} FROM STDIN WITH (FORMAT CSV, NULL 'null')"
                start = time.perf_counter()
                cursor.copy_expert(copy_sql, f)
                conn.commit()
                end = time.perf_counter()
                elapsed_ms = (end - start) * 1000
                elapsed_insert_time_ms += elapsed_ms
            logging.debug(f"Inserted table: {table[0]}")#table_name

            #check if updates are associated - folded relationships(table associated with parent entity updated), folded weak entities(table associated with strong entity updated)
            assert table[0] in table_mappings
            for node_name in table_mappings[table[0]]:
                entity_or_relationship_node = graph.get_node_by_name(node_name)
                if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and graph.config.get(entity_or_relationship_node.unique_name)==
                        "contained_in_parent"):
                    print("updating table for node", node_name)
                    file_name = 'data/' + entity_or_relationship_node.unique_name + '.csv'
                    temp_file_name = entity_or_relationship_node.unique_name
                    columns = insert_table_attribute_names[temp_file_name]#columns from temp table
                    table_primary_keys = table[-1]
                    attribute_names = []
                    attribute_names.extend(table_primary_keys)
                    attribute_names.append(entity_or_relationship_node.unique_name)
                    aggregated_temp_table_name = "temp_" + entity_or_relationship_node.unique_name
                    if os.path.exists(file_name):#batch insert to temp table
                        if not check_if_table_exists(db_name, aggregated_temp_table_name):
                            aggregated_temp_table_name, attribute_names = aggregate_folded_weak_entity_by_table_pk_csv(file_name, columns, table[0], table_primary_keys, node_name)#for folded weak entities - generate aggregated batch csv
                            file_name = 'data/' + aggregated_temp_table_name +'.csv'
                            assert os.path.exists(file_name), f"File {file_name} does not exist"
                            create_temp_table_sql = f"CREATE TABLE {aggregated_temp_table_name} (LIKE {table[0]} INCLUDING ALL);"
                            cursor.execute(create_temp_table_sql)#create temp table
                            columns = attribute_names
                            column_clause = f"({', '.join(columns)})"
                            with open(file_name, 'r') as f:
                                copy_sql = f"COPY {aggregated_temp_table_name} {column_clause} FROM STDIN WITH (FORMAT CSV, NULL 'null')"
                                start = time.perf_counter()
                                cursor.copy_expert(copy_sql, f)#batch insert to temp table
                                conn.commit() # commit both CREATE + COPY
                                end = time.perf_counter()
                                elapsed_ms = (end - start) * 1000
                                elapsed_update_time_ms += elapsed_ms

                        #update original table from temp table by pk join
                        update_clause = []
                        set_clause = []
                        from_clause = []
                        where_clause = []
                        index_clause = []#create index on join column of temp table - to make the join with temp table faster

                        update_clause.append(f"{table[0]}")

                        table_primary_keys = table[-1]

                        if len(entity_or_relationship_node.parent_entity.node_cover)>1:
                            assert not entity_or_relationship_node.parent_entity.is_weak_entity#should be a strong root or subclass in hierarchy - only 1 pk for parent entity
                            temp_table_pk = insert_table_attribute_names[temp_file_name][0]
                            for attribute_name in attribute_names:
                                if attribute_name not in table_primary_keys and attribute_name != temp_table_pk:
                                    set_clause.append(f"{attribute_name} = {aggregated_temp_table_name}.{attribute_name}")

                            assert len(table_primary_keys) == 1
                            where_clause.append(f"{table[0]}.{table_primary_keys[0]} = {aggregated_temp_table_name}.{temp_table_pk}")
                            index_clause.append(temp_table_pk)
                        else:
                            for attribute_name in attribute_names:
                                if attribute_name not in table_primary_keys:
                                    set_clause.append(f"{attribute_name} = {aggregated_temp_table_name}.{attribute_name}")

                            for primary_key in table_primary_keys:
                                where_clause.append(f"{table[0]}.{primary_key} = {aggregated_temp_table_name}.{primary_key}")
                                index_clause.append(primary_key)


                        #filter for tuples not relevant to parent_entity in which weak entity is folded
                        #otherwise update has to iterate through all tuples - this pushdown may reduce time for update
                        if entity_or_relationship_node.parent_entity.is_subclass and entity_or_relationship_node.parent_entity.is_contained_in_parent:
                            if len(entity_or_relationship_node.parent_entity.node_cover)>1:
                                #of all tables in which parent entity is distributed, only original parent entity's mapped table has to be filtered by only tuples belonging to
                                #parent entity or its child classes to do the update
                                #the other tables which are not parent entity's original mapped_table are the tables from CAD/ABI descendants' tables in node cover
                                #all tuples in for those table need the update since they all are belonging to parent entity entity(since they are subclasses of parent entity)
                                #the check is required to filter ancestor tuples of parent entity which may present in parent entity's original mapped_table
                                if table[0] == entity_or_relationship_node.parent_entity.mapped_table[1]:
                                    if len(entity_or_relationship_node.parent_entity.children)>0:
                                        assert "role" in insert_table_attribute_names[table[0]]
                                        # collect entity names (entity + contained children)
                                        all_entities = {entity_or_relationship_node.parent_entity.unique_name}#add entity itself
                                        #add all children rooted at node
                                        find_all_children_rooted_at_node(entity_or_relationship_node.parent_entity, all_entities)
                                        all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                        where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                                    else:#entity itself - where clause would be just role in (entity_name)
                                        #for leaf subclass contained in parent
                                        assert "role" in insert_table_attribute_names[table[0]]
                                        where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{entity_or_relationship_node.parent_entity.unique_name}')")
                            else:
                                #the check is required to filter ancestor tuples of parent which may present in parent entity's mapped_table
                                #those ancestor tuples are guaranteed to not participate in relationship
                                assert table[0] == entity_or_relationship_node.parent_entity.mapped_table[1]
                                if len(entity_or_relationship_node.parent_entity.children)>0:
                                    assert "role" in insert_table_attribute_names[table[0]]
                                    # collect entity names (entity + contained children)
                                    all_entities = {entity_or_relationship_node.parent_entity.unique_name}#add entity itself
                                    #add all children rooted at node
                                    find_all_children_rooted_at_node(entity_or_relationship_node.parent_entity, all_entities)
                                    all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                    where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                                else:#entity itself - where clause would be just role in (entity_name)
                                    #for leaf subclass contained in parent
                                    assert "role" in insert_table_attribute_names[table[0]]
                                    where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{entity_or_relationship_node.parent_entity.unique_name}')")

                        from_clause.append(f"{aggregated_temp_table_name}")

                        update_clause_str = ", ".join(update_clause)
                        set_clause_str = ", ".join(set_clause)
                        from_clause_str = ", ".join(from_clause)
                        where_clause_str = " AND ".join(where_clause)
                        index_clause_str = "(" + ", ".join(index_clause) + ")"
                        index_table_clause = f"CREATE INDEX IF NOT EXISTS {"idx_"+aggregated_temp_table_name} ON {aggregated_temp_table_name} {index_clause_str};"
                        cursor.execute(index_table_clause)
                        conn.commit()
                        update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                        print(update_table_clause)
                        start = time.perf_counter()
                        cursor.execute(update_table_clause)
                        conn.commit()
                        end = time.perf_counter()
                        elapsed_ms = (end - start) * 1000
                        elapsed_update_time_ms += elapsed_ms
                        logging.debug(f"Inserted table: {table[0]}, Inserted weak entity: {entity_or_relationship_node.unique_name}")

                elif entity_or_relationship_node.is_relationship() and graph.config.get(entity_or_relationship_node.unique_name)=="folded_to_many_side":
                    print("updating table for node", node_name)
                    file_name = 'data/' + 'temp_' + entity_or_relationship_node.unique_name +'.csv'
                    if os.path.exists(file_name):#batch insert to temp table
                        temp_table_name = "temp_" + entity_or_relationship_node.unique_name
                        columns = insert_table_attribute_names[temp_table_name]
                        if not check_if_table_exists(db_name, temp_table_name):
                            create_temp_table_sql = f"CREATE TABLE {temp_table_name} (LIKE {table[0]} INCLUDING ALL);"
                            cursor.execute(create_temp_table_sql)#create temp table
                            column_clause = f"({', '.join(columns)})"
                            with open(file_name, 'r') as f:
                                copy_sql = f"COPY {temp_table_name} {column_clause} FROM STDIN WITH (FORMAT CSV, NULL 'null')"
                                start = time.perf_counter()
                                cursor.copy_expert(copy_sql, f)#batch insert to temp table
                                conn.commit() # commit both CREATE + COPY
                                end = time.perf_counter()
                                elapsed_ms = (end - start) * 1000
                                elapsed_update_time_ms += elapsed_ms

                        #update original table from temp table by pk join
                        update_clause = []
                        set_clause = []
                        from_clause = []
                        where_clause = []
                        index_clause = []#create index on join column of temp table - to make the join with temp table faster - otherwise will take a significant time for larger table joins

                        update_clause.append(f"{table[0]}")

                        table_primary_keys = table[-1]

                        many_side = entity_or_relationship_node.entity1 if (not entity_or_relationship_node.rel_dict['entity1']['one'] and
                                                                            entity_or_relationship_node.rel_dict['entity2']['one']) else entity_or_relationship_node.entity2
                        if len(many_side.node_cover)>1:
                            assert not many_side.is_weak_entity#should be a strong root or subclass in hierarchy - only 1 pk
                            temp_table_pk = insert_table_attribute_names[temp_table_name][0]#1 pk from many side
                            for attribute_name in columns:
                                if attribute_name not in table_primary_keys and attribute_name != temp_table_pk:#when many side is distributed, folded relationship is also distributed in
                                    #many side's node cover. Of the set of tables in which relationship is distributed, the table's pk and relationship's pk will be different
                                    #if the table's mapped node is a one from the node cover of many side node except itself.
                                    #Only need to add 1 side pk from relationship since many side is already in the table.
                                    #Has to do an extra check of attribute_name != temp_table_pk to make sure it is not the many side pk.
                                    set_clause.append(f"{attribute_name} = {temp_table_name}.{attribute_name}")

                            assert len(table_primary_keys) == 1
                            where_clause.append(f"{table[0]}.{table_primary_keys[0]} = {temp_table_name}.{temp_table_pk}")
                            index_clause.append(temp_table_pk)
                        else:
                            for attribute_name in columns:
                                if attribute_name not in table_primary_keys:
                                    set_clause.append(f"{attribute_name} = {temp_table_name}.{attribute_name}")
                            for primary_key in table_primary_keys:
                                where_clause.append(f"{table[0]}.{primary_key} = {temp_table_name}.{primary_key}")
                                index_clause.append(primary_key)


                        #filter for tuples not relevant to many_side
                        #otherwise update has to iterate through all tuples - this pushdown may reduce time for update
                        if many_side.is_subclass and many_side.is_contained_in_parent:
                            if len(many_side.node_cover)>1:
                                #of all tables in which many_side is distributed, only original many_side's mapped table has to be filtered by only tuples belonging to
                                #many_side or its child classes to do the update
                                #the other tables which are not many_side's original mapped_table are the tables from CAD/ABI descendants' tables in node cover
                                #all tuples in for those table need the update since they all are belonging to many side entity(since they are subclasses of many side)
                                #the check is required to filter parent tuples of many_side which may present in many_side's original mapped_table
                                if table[0] == many_side.mapped_table[1]:
                                    if len(many_side.children)>0:
                                        assert "role" in insert_table_attribute_names[table[0]]
                                        # collect entity names (entity + contained children)
                                        all_entities = {many_side.unique_name}#add entity itself
                                        #add all children rooted at node
                                        find_all_children_rooted_at_node(many_side, all_entities)
                                        all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                        where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                                    else:#entity itself - where clause would be just role in (entity_name)
                                        #for leaf subclass contained in parent
                                        assert "role" in insert_table_attribute_names[table[0]]
                                        where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{many_side.unique_name}')")
                            else:
                                #the check is required to filter parent tuples of many_side which may present in many_side's mapped_table
                                #those parent tuples are guaranteed to not participate in relationship
                                assert table[0] == many_side.mapped_table[1]
                                if len(many_side.children)>0:
                                    assert "role" in insert_table_attribute_names[table[0]]
                                    # collect entity names (entity + contained children)
                                    all_entities = {many_side.unique_name}#add entity itself
                                    #add all children rooted at node
                                    find_all_children_rooted_at_node(many_side, all_entities)
                                    all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                    where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                                else:#entity itself - where clause would be just role in (entity_name)
                                    #for leaf subclass contained in parent
                                    assert "role" in insert_table_attribute_names[table[0]]
                                    where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{many_side.unique_name}')")

                        from_clause.append(f"{temp_table_name}")

                        update_clause_str = ", ".join(update_clause)
                        set_clause_str = ", ".join(set_clause)
                        from_clause_str = ", ".join(from_clause)
                        where_clause_str = " AND ".join(where_clause)
                        index_clause_str = "(" + ", ".join(index_clause) + ")"
                        index_table_clause = f"CREATE INDEX IF NOT EXISTS {"idx_"+temp_table_name} ON {temp_table_name} {index_clause_str};"
                        cursor.execute(index_table_clause)
                        conn.commit()
                        update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                        print(update_table_clause)
                        start = time.perf_counter()
                        cursor.execute(update_table_clause)
                        conn.commit()
                        end = time.perf_counter()
                        elapsed_ms = (end - start) * 1000
                        elapsed_update_time_ms += elapsed_ms
                        logging.debug(f"Inserted table: {table[0]}, Inserted folded relationship: {entity_or_relationship_node.unique_name}")

    cursor.close()
    conn.close()

    #write db initialization exec times to csv
    write_db_initialization_exec_times(elapsed_insert_time_ms, elapsed_update_time_ms)

#in-memory csvs
def insert_data_in_batches_with_templatization(db_name, load_file, table_mappings):#todo - serialize table mappings to graph and retrieve from deserialization

    with open(load_file, "r") as f:
        data = json.load(f)
        insert_statement_file = data["insert_statements_for_db_initializing"]

    sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    insert_table_attribute_names = {}
    in_memory_csvs = {}
    table_index_mappings = {}

    # Insert data
    with open(insert_statement_file, "r") as f:
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
            if entity_or_relationship_node.unique_name not in table_index_mappings:
                table_index_mappings[entity_or_relationship_node.unique_name] = {}
                insert_data = generate_insert_statements_in_batch(entity_or_relationship_node, values_as_dict, index_mapping, relevant_tables, types, graph, insert_table_attribute_names,
                                                                  in_memory_csvs, table_index_mappings[entity_or_relationship_node.unique_name])
            else:
                execute_templatized_insert(in_memory_csvs, entity_or_relationship_node, values_as_dict,
                                           table_index_mappings[entity_or_relationship_node.unique_name], node_index_to_attribute_mapping, relevant_tables)

    logging.debug(f"in memory csv generation done")

    elapsed_insert_time_ms = 0#insert cost for all tables in chosen schema
    elapsed_update_time_ms = 0#cost to create update-temp tables and update cost

    #by_name = {t[0]: t for t in tables}
    #for table_name in sorted_by_dependencies_tables:
    for table in tables:
        table_name = table[0]
        print(table_name)
        assert table is not None, "Table {} not found".format(table_name)
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
        start = time.perf_counter()
        cursor.copy_expert(copy_sql, buffer)
        conn.commit()
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        elapsed_insert_time_ms += elapsed_ms
        logging.debug(f"Inserted table: {table[0]}")
        in_memory_csvs[table[0]] = None#free memory

        #check if updates are associated - folded relationships(table associated with parent entity updated), folded weak entities(table associated with strong entity updated)
        assert table[0] in table_mappings
        for node_name in table_mappings[table[0]]:
            entity_or_relationship_node = graph.get_node_by_name(node_name)
            if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and graph.config.get(entity_or_relationship_node.unique_name)==
                    "contained_in_parent"):
                print("updating table for node", node_name)
                table_primary_keys = table[-1]
                attribute_names = []
                attribute_names.extend(table_primary_keys)
                attribute_names.append(entity_or_relationship_node.unique_name)
                aggregated_temp_table_name = "temp_aggregated_" + entity_or_relationship_node.unique_name
                if not check_if_table_exists(db_name, aggregated_temp_table_name):#batch insert to temp table
                    #generate aggregated data for weak entity by pks
                    unaggregated_data = in_memory_csvs[entity_or_relationship_node.unique_name]
                    unaggregated_columns = insert_table_attribute_names[entity_or_relationship_node.unique_name]
                    aggregated_temp_table_name, attribute_names = aggregate_folded_weak_entity_by_table_pk(in_memory_csvs, unaggregated_data, unaggregated_columns, table[0],
                                                                                                           table_primary_keys, node_name)#for folded weak entities - generate aggregated batch csv
                    aggregated_data_key_name = "temp_aggregated_" + entity_or_relationship_node.unique_name
                    aggregated_data = in_memory_csvs[aggregated_data_key_name]#aggregated_temp_table_name and aggregated_data_key_name same
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
                    start = time.perf_counter()
                    cursor.copy_expert(copy_sql, buffer)#batch insert to temp table
                    conn.commit()
                    end = time.perf_counter()
                    elapsed_ms = (end - start) * 1000
                    elapsed_update_time_ms += elapsed_ms

                #update original table from temp table by pk join
                update_clause = []
                set_clause = []
                from_clause = []
                where_clause = []
                index_clause = []#create index on join column of temp table - to make the join with temp table faster

                update_clause.append(f"{table[0]}")

                table_primary_keys = table[-1]

                if len(entity_or_relationship_node.parent_entity.node_cover)>1:
                    assert not entity_or_relationship_node.parent_entity.is_weak_entity#should be a strong root or subclass in hierarchy - only 1 pk for parent entity
                    temp_table_pk = insert_table_attribute_names[entity_or_relationship_node.unique_name][0]
                    for attribute_name in attribute_names:
                        if attribute_name not in table_primary_keys and attribute_name != temp_table_pk:
                            set_clause.append(f"{attribute_name} = {aggregated_temp_table_name}.{attribute_name}")

                    assert len(table_primary_keys) == 1
                    where_clause.append(f"{table[0]}.{table_primary_keys[0]} = {aggregated_temp_table_name}.{temp_table_pk}")
                    index_clause.append(temp_table_pk)
                else:
                    for attribute_name in attribute_names:
                        if attribute_name not in table_primary_keys:
                            set_clause.append(f"{attribute_name} = {aggregated_temp_table_name}.{attribute_name}")

                    for primary_key in table_primary_keys:
                        where_clause.append(f"{table[0]}.{primary_key} = {aggregated_temp_table_name}.{primary_key}")
                        index_clause.append(primary_key)


                #filter for tuples not relevant to parent_entity in which weak entity is folded
                #otherwise update has to iterate through all tuples - this pushdown may reduce time for update
                if entity_or_relationship_node.parent_entity.is_subclass and entity_or_relationship_node.parent_entity.is_contained_in_parent:
                    if len(entity_or_relationship_node.parent_entity.node_cover)>1:
                        #of all tables in which parent entity is distributed, only original parent entity's mapped table has to be filtered by only tuples belonging to
                        #parent entity or its child classes to do the update
                        #the other tables which are not parent entity's original mapped_table are the tables from CAD/ABI descendants' tables in node cover
                        #all tuples in for those table need the update since they all are belonging to parent entity entity(since they are subclasses of parent entity)
                        #the check is required to filter ancestor tuples of parent entity which may present in parent entity's original mapped_table
                        if table[0] == entity_or_relationship_node.parent_entity.mapped_table[1]:
                            if len(entity_or_relationship_node.parent_entity.children)>0:
                                assert "role" in insert_table_attribute_names[table[0]]
                                # collect entity names (entity + contained children)
                                all_entities = {entity_or_relationship_node.parent_entity.unique_name}#add entity itself
                                #add all children rooted at node
                                find_all_children_rooted_at_node(entity_or_relationship_node.parent_entity, all_entities)
                                all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                            else:#entity itself - where clause would be just role in (entity_name)
                                #for leaf subclass contained in parent
                                assert "role" in insert_table_attribute_names[table[0]]
                                where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{entity_or_relationship_node.parent_entity.unique_name}')")
                    else:
                        #the check is required to filter ancestor tuples of parent which may present in parent entity's mapped_table
                        #those ancestor tuples are guaranteed to not participate in relationship
                        assert table[0] == entity_or_relationship_node.parent_entity.mapped_table[1]
                        if len(entity_or_relationship_node.parent_entity.children)>0:
                            assert "role" in insert_table_attribute_names[table[0]]
                            # collect entity names (entity + contained children)
                            all_entities = {entity_or_relationship_node.parent_entity.unique_name}#add entity itself
                            #add all children rooted at node
                            find_all_children_rooted_at_node(entity_or_relationship_node.parent_entity, all_entities)
                            all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                            where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                        else:#entity itself - where clause would be just role in (entity_name)
                            #for leaf subclass contained in parent
                            assert "role" in insert_table_attribute_names[table[0]]
                            where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{entity_or_relationship_node.parent_entity.unique_name}')")

                from_clause.append(f"{aggregated_temp_table_name}")

                update_clause_str = ", ".join(update_clause)
                set_clause_str = ", ".join(set_clause)
                from_clause_str = ", ".join(from_clause)
                where_clause_str = " AND ".join(where_clause)
                index_clause_str = "(" + ", ".join(index_clause) + ")"
                index_table_clause = f"CREATE INDEX IF NOT EXISTS {"idx_"+aggregated_temp_table_name} ON {aggregated_temp_table_name} {index_clause_str};"
                cursor.execute(index_table_clause)
                conn.commit()
                update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                start = time.perf_counter()
                cursor.execute(update_table_clause)
                conn.commit()
                end = time.perf_counter()
                elapsed_ms = (end - start) * 1000
                elapsed_update_time_ms += elapsed_ms
                logging.debug(f"Inserted table: {table[0]}, Inserted weak entity: {entity_or_relationship_node.unique_name}")
                if in_memory_csvs[entity_or_relationship_node.unique_name]:
                    in_memory_csvs[entity_or_relationship_node.unique_name] = None
                if in_memory_csvs[aggregated_temp_table_name]:
                    in_memory_csvs[aggregated_temp_table_name] = None

            elif entity_or_relationship_node.is_relationship() and graph.config.get(entity_or_relationship_node.unique_name)=="folded_to_many_side":
                print("updating table for node", node_name)
                temp_table_name = 'temp_' + entity_or_relationship_node.mapped_table[1] + '_' + entity_or_relationship_node.unique_name
                data = in_memory_csvs[temp_table_name]
                columns = insert_table_attribute_names[temp_table_name]
                if not check_if_table_exists(db_name, temp_table_name):
                    #batch insert to temp table
                    temp_table_name = "temp_" + entity_or_relationship_node.mapped_table[1] + "_" + entity_or_relationship_node.unique_name
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
                    start = time.perf_counter()
                    cursor.copy_expert(copy_sql, buffer)#batch insert to temp table
                    conn.commit()
                    end = time.perf_counter()
                    elapsed_ms = (end - start) * 1000
                    elapsed_update_time_ms += elapsed_ms

                #update original table from temp table by pk join
                update_clause = []
                set_clause = []
                from_clause = []
                where_clause = []
                index_clause = []#create index on join column of temp table - to make the join with temp table faster - otherwise will take a significant time for larger table joins

                update_clause.append(f"{table[0]}")

                table_primary_keys = table[-1]

                many_side = entity_or_relationship_node.entity1 if (not entity_or_relationship_node.rel_dict['entity1']['one'] and
                                                                    entity_or_relationship_node.rel_dict['entity2']['one']) else entity_or_relationship_node.entity2
                if len(many_side.node_cover)>1:
                    assert not many_side.is_weak_entity#should be a strong root or subclass in hierarchy - only 1 pk
                    temp_table_pk = insert_table_attribute_names[temp_table_name][0]#1 pk from many side
                    for attribute_name in columns:
                        if attribute_name not in table_primary_keys and attribute_name != temp_table_pk:#when many side is distributed, folded relationship is also distributed in
                            #many side's node cover. Of the set of tables in which relationship is distributed, the table's pk and relationship's pk will be different
                            #if the table's mapped node is a one from the node cover of many side node except itself.
                            #Only need to add 1 side pk from relationship since many side is already in the table.
                            #Has to do an extra check of attribute_name != temp_table_pk to make sure it is not the many side pk.
                            set_clause.append(f"{attribute_name} = {temp_table_name}.{attribute_name}")

                    assert len(table_primary_keys) == 1
                    where_clause.append(f"{table[0]}.{table_primary_keys[0]} = {temp_table_name}.{temp_table_pk}")
                    index_clause.append(temp_table_pk)
                else:
                    for attribute_name in columns:
                        if attribute_name not in table_primary_keys:
                            set_clause.append(f"{attribute_name} = {temp_table_name}.{attribute_name}")
                    for primary_key in table_primary_keys:
                        where_clause.append(f"{table[0]}.{primary_key} = {temp_table_name}.{primary_key}")
                        index_clause.append(primary_key)


                #filter for tuples not relevant to many_side
                #otherwise update has to iterate through all tuples - this pushdown may reduce time for update
                if many_side.is_subclass and many_side.is_contained_in_parent:
                    if len(many_side.node_cover)>1:
                        #of all tables in which many_side is distributed, only original many_side's mapped table has to be filtered by only tuples belonging to
                        #many_side or its child classes to do the update
                        #the other tables which are not many_side's original mapped_table are the tables from CAD/ABI descendants' tables in node cover
                        #all tuples in for those table need the update since they all are belonging to many side entity(since they are subclasses of many side)
                        #the check is required to filter parent tuples of many_side which may present in many_side's original mapped_table
                        if table[0] == many_side.mapped_table[1]:
                            if len(many_side.children)>0:
                                assert "role" in insert_table_attribute_names[table[0]]
                                # collect entity names (entity + contained children)
                                all_entities = {many_side.unique_name}#add entity itself
                                #add all children rooted at node
                                find_all_children_rooted_at_node(many_side, all_entities)
                                all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                            else:#entity itself - where clause would be just role in (entity_name)
                                #for leaf subclass contained in parent
                                assert "role" in insert_table_attribute_names[table[0]]
                                where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{many_side.unique_name}')")
                    else:
                        #the check is required to filter parent tuples of many_side which may present in many_side's mapped_table
                        #those parent tuples are guaranteed to not participate in relationship
                        assert table[0] == many_side.mapped_table[1]
                        if len(many_side.children)>0:
                            assert "role" in insert_table_attribute_names[table[0]]
                            # collect entity names (entity + contained children)
                            all_entities = {many_side.unique_name}#add entity itself
                            #add all children rooted at node
                            find_all_children_rooted_at_node(many_side, all_entities)
                            all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                            where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                        else:#entity itself - where clause would be just role in (entity_name)
                            #for leaf subclass contained in parent
                            assert "role" in insert_table_attribute_names[table[0]]
                            where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{many_side.unique_name}')")


                from_clause.append(f"{temp_table_name}")

                update_clause_str = ", ".join(update_clause)
                set_clause_str = ", ".join(set_clause)
                from_clause_str = ", ".join(from_clause)
                where_clause_str = " AND ".join(where_clause)
                index_clause_str = "(" + ", ".join(index_clause) + ")"
                index_table_clause = f"CREATE INDEX IF NOT EXISTS {"idx_"+temp_table_name} ON {temp_table_name} {index_clause_str};"
                cursor.execute(index_table_clause)
                conn.commit()
                update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                start = time.perf_counter()
                cursor.execute(update_table_clause)
                conn.commit()
                end = time.perf_counter()
                elapsed_ms = (end - start) * 1000
                elapsed_update_time_ms += elapsed_ms
                logging.debug(f"Inserted table: {table[0]}, Inserted folded relationship: {entity_or_relationship_node.unique_name}")
                if in_memory_csvs[temp_table_name]:
                    in_memory_csvs[temp_table_name] = None

    cursor.close()
    conn.close()

    #write db initialization exec times to csv
    write_db_initialization_exec_times(elapsed_insert_time_ms, elapsed_update_time_ms)

def merge_and_generate_global_in_memory_csvs_from_local_in_memory_csvs(local_in_memory_csvs_list):
    in_memory_csvs = {}
    for local_in_memory_csv in local_in_memory_csvs_list:
        for k, v in local_in_memory_csv.items():
            if k in in_memory_csvs:
                in_memory_csvs[k].extend(v)
            else:
                in_memory_csvs[k] = v
    return in_memory_csvs

def generate_insert_table_attribute_names_from_local(local_insert_table_attribute_names_list):
    insert_table_attribute_names = {}
    for local_insert_table_attribute_names in local_insert_table_attribute_names_list:
        for table_name, attributes in local_insert_table_attribute_names.items():
            if table_name not in insert_table_attribute_names:
                insert_table_attribute_names[table_name] = attributes
    return insert_table_attribute_names


def parallel_worker_in_memory_csv_generation(insert_statements_chunk, tables, types, graph):

    local_insert_table_attribute_names = {}
    local_in_memory_csvs = {}
    local_table_index_mappings = {}

    # Insert data
    for i, insert_statement in enumerate(insert_statements_chunk):
        parsed = new_parse(insert_statement)

        entity_or_relationship_node = [node for node in graph.nodes if node.name.lower() == parsed["table_name"].lower()][0]
        values_as_dict, index_mapping = match_to_schema(parsed["table_name"], parsed["values"], entity_or_relationship_node)
        node_index_to_attribute_mapping = {v: k for k, v in index_mapping.items()}
        #print(values_as_dict)
        relevant_tables = [table for table in tables if table[0] in [node_table for sort_key, node_table in entity_or_relationship_node.node_tables]]
        if entity_or_relationship_node.unique_name not in local_table_index_mappings:
            local_table_index_mappings[entity_or_relationship_node.unique_name] = {}
            insert_data = generate_insert_statements_in_batch(entity_or_relationship_node, values_as_dict, index_mapping, relevant_tables, types, graph, local_insert_table_attribute_names,
                                                              local_in_memory_csvs, local_table_index_mappings[entity_or_relationship_node.unique_name])
        else:
            execute_templatized_insert(local_in_memory_csvs, entity_or_relationship_node, values_as_dict,
                                       local_table_index_mappings[entity_or_relationship_node.unique_name], node_index_to_attribute_mapping, relevant_tables)

    return local_in_memory_csvs, local_insert_table_attribute_names, local_table_index_mappings



#in-memory csvs - templatized and parallelized
#parallelize processing insert stmts to generate in-memory csvs
def insert_data_in_batches_with_templatization_parallelized(db_name, load_file, table_mappings):#todo - serialize table mappings to graph and retrieve from deserialization

    with open(load_file, "r") as f:
        data = json.load(f)
        insert_statement_file = data["insert_statements_for_db_initializing"]

    with open(insert_statement_file, "r") as f:
        sql_text = f.read()

    insert_statements = [
        stmt.strip()
        for stmt in sql_text.split(";")
        if stmt.strip()
    ]

    sorted_by_dependencies_tables, tables, types, graph = load_data(db_name)

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="password")
    cursor = conn.cursor()

    insert_table_attribute_names = {}
    in_memory_csvs = {}
    table_index_mappings = {}

    # Parallel processing
    n_processes = multiprocessing.cpu_count()
    chunk_size = len(insert_statements) // n_processes + 1
    chunks = [insert_statements[i:i + chunk_size] for i in range(0, len(insert_statements), chunk_size)]

    args = [(chunk, tables, types, graph) for chunk in chunks]
    logging.debug(f"-----------parallelized in-memory csv generation with {n_processes} processes")
    with multiprocessing.Pool(processes=n_processes) as pool:
        results = pool.starmap(parallel_worker_in_memory_csv_generation, args)

    logging.debug(f"-----------gathering all local in memory csvs from {n_processes} processes")

    in_memory_csvs = merge_and_generate_global_in_memory_csvs_from_local_in_memory_csvs([r[0] for r in results])
    insert_table_attribute_names = generate_insert_table_attribute_names_from_local([r[1] for r in results])

    logging.debug(f"in memory csv generation done")

    elapsed_insert_time_ms = 0#insert cost for all tables in chosen schema
    elapsed_update_time_ms = 0#cost to create update-temp tables and update cost

    #by_name = {t[0]: t for t in tables}
    #for table_name in sorted_by_dependencies_tables:
    for table in tables:
        table_name = table[0]
        print(table_name)
        assert table is not None, "Table {} not found".format(table_name)
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
        start = time.perf_counter()
        cursor.copy_expert(copy_sql, buffer)
        conn.commit()
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        elapsed_insert_time_ms += elapsed_ms
        logging.debug(f"Inserted table: {table[0]}")
        in_memory_csvs[table[0]] = None#free memory

        #check if updates are associated - folded relationships(table associated with parent entity updated), folded weak entities(table associated with strong entity updated)
        assert table[0] in table_mappings
        for node_name in table_mappings[table[0]]:
            entity_or_relationship_node = graph.get_node_by_name(node_name)
            if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and graph.config.get(entity_or_relationship_node.unique_name)==
                    "contained_in_parent"):
                print("updating table for node", node_name)
                table_primary_keys = table[-1]
                attribute_names = []
                attribute_names.extend(table_primary_keys)
                attribute_names.append(entity_or_relationship_node.unique_name)
                aggregated_temp_table_name = "temp_aggregated_" + entity_or_relationship_node.unique_name
                if not check_if_table_exists(db_name, aggregated_temp_table_name):#batch insert to temp table
                    #generate aggregated data for weak entity by pks
                    unaggregated_data = in_memory_csvs[entity_or_relationship_node.unique_name]
                    unaggregated_columns = insert_table_attribute_names[entity_or_relationship_node.unique_name]
                    aggregated_temp_table_name, attribute_names = aggregate_folded_weak_entity_by_table_pk(in_memory_csvs, unaggregated_data, unaggregated_columns, table[0],
                                                                                                           table_primary_keys, node_name)#for folded weak entities - generate aggregated batch csv
                    aggregated_data_key_name = "temp_aggregated_" + entity_or_relationship_node.unique_name
                    aggregated_data = in_memory_csvs[aggregated_data_key_name]#aggregated_temp_table_name and aggregated_data_key_name same
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
                    start = time.perf_counter()
                    cursor.copy_expert(copy_sql, buffer)#batch insert to temp table
                    conn.commit()
                    end = time.perf_counter()
                    elapsed_ms = (end - start) * 1000
                    elapsed_update_time_ms += elapsed_ms

                #update original table from temp table by pk join
                update_clause = []
                set_clause = []
                from_clause = []
                where_clause = []
                index_clause = []#create index on join column of temp table - to make the join with temp table faster

                update_clause.append(f"{table[0]}")

                table_primary_keys = table[-1]

                if len(entity_or_relationship_node.parent_entity.node_cover)>1:
                    assert not entity_or_relationship_node.parent_entity.is_weak_entity#should be a strong root or subclass in hierarchy - only 1 pk for parent entity
                    temp_table_pk = insert_table_attribute_names[entity_or_relationship_node.unique_name][0]
                    for attribute_name in attribute_names:
                        if attribute_name not in table_primary_keys and attribute_name != temp_table_pk:
                            set_clause.append(f"{attribute_name} = {aggregated_temp_table_name}.{attribute_name}")

                    assert len(table_primary_keys) == 1
                    where_clause.append(f"{table[0]}.{table_primary_keys[0]} = {aggregated_temp_table_name}.{temp_table_pk}")
                    index_clause.append(temp_table_pk)
                else:
                    for attribute_name in attribute_names:
                        if attribute_name not in table_primary_keys:
                            set_clause.append(f"{attribute_name} = {aggregated_temp_table_name}.{attribute_name}")

                    for primary_key in table_primary_keys:
                        where_clause.append(f"{table[0]}.{primary_key} = {aggregated_temp_table_name}.{primary_key}")
                        index_clause.append(primary_key)


                #filter for tuples not relevant to parent_entity in which weak entity is folded
                #otherwise update has to iterate through all tuples - this pushdown may reduce time for update
                if entity_or_relationship_node.parent_entity.is_subclass and entity_or_relationship_node.parent_entity.is_contained_in_parent:
                    if len(entity_or_relationship_node.parent_entity.node_cover)>1:
                        #of all tables in which parent entity is distributed, only original parent entity's mapped table has to be filtered by only tuples belonging to
                        #parent entity or its child classes to do the update
                        #the other tables which are not parent entity's original mapped_table are the tables from CAD/ABI descendants' tables in node cover
                        #all tuples in for those table need the update since they all are belonging to parent entity entity(since they are subclasses of parent entity)
                        #the check is required to filter ancestor tuples of parent entity which may present in parent entity's original mapped_table
                        if table[0] == entity_or_relationship_node.parent_entity.mapped_table[1]:
                            if len(entity_or_relationship_node.parent_entity.children)>0:
                                assert "role" in insert_table_attribute_names[table[0]]
                                # collect entity names (entity + contained children)
                                all_entities = {entity_or_relationship_node.parent_entity.unique_name}#add entity itself
                                #add all children rooted at node
                                find_all_children_rooted_at_node(entity_or_relationship_node.parent_entity, all_entities)
                                all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                            else:#entity itself - where clause would be just role in (entity_name)
                                #for leaf subclass contained in parent
                                assert "role" in insert_table_attribute_names[table[0]]
                                where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{entity_or_relationship_node.parent_entity.unique_name}')")
                    else:
                        #the check is required to filter ancestor tuples of parent which may present in parent entity's mapped_table
                        #those ancestor tuples are guaranteed to not participate in relationship
                        assert table[0] == entity_or_relationship_node.parent_entity.mapped_table[1]
                        if len(entity_or_relationship_node.parent_entity.children)>0:
                            assert "role" in insert_table_attribute_names[table[0]]
                            # collect entity names (entity + contained children)
                            all_entities = {entity_or_relationship_node.parent_entity.unique_name}#add entity itself
                            #add all children rooted at node
                            find_all_children_rooted_at_node(entity_or_relationship_node.parent_entity, all_entities)
                            all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                            where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                        else:#entity itself - where clause would be just role in (entity_name)
                            #for leaf subclass contained in parent
                            assert "role" in insert_table_attribute_names[table[0]]
                            where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{entity_or_relationship_node.parent_entity.unique_name}')")

                from_clause.append(f"{aggregated_temp_table_name}")

                update_clause_str = ", ".join(update_clause)
                set_clause_str = ", ".join(set_clause)
                from_clause_str = ", ".join(from_clause)
                where_clause_str = " AND ".join(where_clause)
                index_clause_str = "(" + ", ".join(index_clause) + ")"
                index_table_clause = f"CREATE INDEX IF NOT EXISTS {"idx_"+aggregated_temp_table_name} ON {aggregated_temp_table_name} {index_clause_str};"
                cursor.execute(index_table_clause)
                conn.commit()
                update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                start = time.perf_counter()
                cursor.execute(update_table_clause)
                conn.commit()
                end = time.perf_counter()
                elapsed_ms = (end - start) * 1000
                elapsed_update_time_ms += elapsed_ms
                logging.debug(f"Inserted table: {table[0]}, Inserted weak entity: {entity_or_relationship_node.unique_name}")
                if in_memory_csvs[entity_or_relationship_node.unique_name]:
                    in_memory_csvs[entity_or_relationship_node.unique_name] = None
                if in_memory_csvs[aggregated_temp_table_name]:
                    in_memory_csvs[aggregated_temp_table_name] = None

            elif entity_or_relationship_node.is_relationship() and graph.config.get(entity_or_relationship_node.unique_name)=="folded_to_many_side":
                print("updating table for node", node_name)
                temp_table_name = 'temp_' + entity_or_relationship_node.mapped_table[1] + '_' + entity_or_relationship_node.unique_name
                data = in_memory_csvs[temp_table_name]
                columns = insert_table_attribute_names[temp_table_name]
                if not check_if_table_exists(db_name, temp_table_name):
                    #batch insert to temp table
                    temp_table_name = "temp_" + entity_or_relationship_node.mapped_table[1] + "_" + entity_or_relationship_node.unique_name
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
                    start = time.perf_counter()
                    cursor.copy_expert(copy_sql, buffer)#batch insert to temp table
                    conn.commit()
                    end = time.perf_counter()
                    elapsed_ms = (end - start) * 1000
                    elapsed_update_time_ms += elapsed_ms

                #update original table from temp table by pk join
                update_clause = []
                set_clause = []
                from_clause = []
                where_clause = []
                index_clause = []#create index on join column of temp table - to make the join with temp table faster - otherwise will take a significant time for larger table joins

                update_clause.append(f"{table[0]}")

                table_primary_keys = table[-1]

                many_side = entity_or_relationship_node.entity1 if (not entity_or_relationship_node.rel_dict['entity1']['one'] and
                                                                    entity_or_relationship_node.rel_dict['entity2']['one']) else entity_or_relationship_node.entity2
                if len(many_side.node_cover)>1:
                    assert not many_side.is_weak_entity#should be a strong root or subclass in hierarchy - only 1 pk
                    temp_table_pk = insert_table_attribute_names[temp_table_name][0]#1 pk from many side
                    for attribute_name in columns:
                        if attribute_name not in table_primary_keys and attribute_name != temp_table_pk:#when many side is distributed, folded relationship is also distributed in
                            #many side's node cover. Of the set of tables in which relationship is distributed, the table's pk and relationship's pk will be different
                            #if the table's mapped node is a one from the node cover of many side node except itself.
                            #Only need to add 1 side pk from relationship since many side is already in the table.
                            #Has to do an extra check of attribute_name != temp_table_pk to make sure it is not the many side pk.
                            set_clause.append(f"{attribute_name} = {temp_table_name}.{attribute_name}")

                    assert len(table_primary_keys) == 1
                    where_clause.append(f"{table[0]}.{table_primary_keys[0]} = {temp_table_name}.{temp_table_pk}")
                    index_clause.append(temp_table_pk)
                else:
                    for attribute_name in columns:
                        if attribute_name not in table_primary_keys:
                            set_clause.append(f"{attribute_name} = {temp_table_name}.{attribute_name}")
                    for primary_key in table_primary_keys:
                        where_clause.append(f"{table[0]}.{primary_key} = {temp_table_name}.{primary_key}")
                        index_clause.append(primary_key)


                #filter for tuples not relevant to many_side
                #otherwise update has to iterate through all tuples - this pushdown may reduce time for update
                if many_side.is_subclass and many_side.is_contained_in_parent:
                    if len(many_side.node_cover)>1:
                        #of all tables in which many_side is distributed, only original many_side's mapped table has to be filtered by only tuples belonging to
                        #many_side or its child classes to do the update
                        #the other tables which are not many_side's original mapped_table are the tables from CAD/ABI descendants' tables in node cover
                        #all tuples in for those table need the update since they all are belonging to many side entity(since they are subclasses of many side)
                        #the check is required to filter parent tuples of many_side which may present in many_side's original mapped_table
                        if table[0] == many_side.mapped_table[1]:
                            if len(many_side.children)>0:
                                assert "role" in insert_table_attribute_names[table[0]]
                                # collect entity names (entity + contained children)
                                all_entities = {many_side.unique_name}#add entity itself
                                #add all children rooted at node
                                find_all_children_rooted_at_node(many_side, all_entities)
                                all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                                where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                            else:#entity itself - where clause would be just role in (entity_name)
                                #for leaf subclass contained in parent
                                assert "role" in insert_table_attribute_names[table[0]]
                                where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{many_side.unique_name}')")
                    else:
                        #the check is required to filter parent tuples of many_side which may present in many_side's mapped_table
                        #those parent tuples are guaranteed to not participate in relationship
                        assert table[0] == many_side.mapped_table[1]
                        if len(many_side.children)>0:
                            assert "role" in insert_table_attribute_names[table[0]]
                            # collect entity names (entity + contained children)
                            all_entities = {many_side.unique_name}#add entity itself
                            #add all children rooted at node
                            find_all_children_rooted_at_node(many_side, all_entities)
                            all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                            where_clause.append(f"{table[0]}.{"role"} {"IN"} ({all_entities_str})")
                        else:#entity itself - where clause would be just role in (entity_name)
                            #for leaf subclass contained in parent
                            assert "role" in insert_table_attribute_names[table[0]]
                            where_clause.append(f"{table[0]}.{"role"} {"IN"} ('{many_side.unique_name}')")

                from_clause.append(f"{temp_table_name}")

                update_clause_str = ", ".join(update_clause)
                set_clause_str = ", ".join(set_clause)
                from_clause_str = ", ".join(from_clause)
                where_clause_str = " AND ".join(where_clause)
                index_clause_str = "(" + ", ".join(index_clause) + ")"
                index_table_clause = f"CREATE INDEX IF NOT EXISTS {"idx_"+temp_table_name} ON {temp_table_name} {index_clause_str};"
                cursor.execute(index_table_clause)
                conn.commit()
                update_table_clause = f"UPDATE {update_clause_str} SET {set_clause_str} FROM {from_clause_str} WHERE {where_clause_str};"
                start = time.perf_counter()
                cursor.execute(update_table_clause)
                conn.commit()
                end = time.perf_counter()
                elapsed_ms = (end - start) * 1000
                elapsed_update_time_ms += elapsed_ms
                logging.debug(f"Inserted table: {table[0]}, Inserted folded relationship: {entity_or_relationship_node.unique_name}")
                if in_memory_csvs[temp_table_name]:
                    in_memory_csvs[temp_table_name] = None

    cursor.close()
    conn.close()

    #write db initialization exec times to csv
    write_db_initialization_exec_times(elapsed_insert_time_ms, elapsed_update_time_ms)