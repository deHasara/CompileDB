import copy
import json
from typing import List, Tuple, Dict, Any
import psycopg2
from er_graph import Graph, serialize_graph, Node

#original one by one insert statement generation

def flatten_composite(value: Any, type_name: str, custom_types: Dict[str, List[Tuple[str, str]]]) -> Tuple[List[Any], str]:
    if type_name not in custom_types:
        return [value], '%s'

    flat_values = []
    placeholders = []

    for attr_name, attr_type in custom_types[type_name]:
        #doesn't handle array of composite type
        sub_values, sub_placeholder = flatten_composite(value[attr_name], attr_type, custom_types)
        flat_values.extend(sub_values)
        placeholders.append(sub_placeholder)

    return flat_values, f"ROW({', '.join(placeholders)})::{type_name}"


def check_if_the_table_for_insert_own_mvd_attribute(graph:Graph, node:Node, table_name):#normalizing own mvds
    for attribute in node.attribute_list:
        if attribute.get("is_multivalued") and attribute.get("mapped_table") is not None and attribute.get("is_in_separate_table"):#mvd in separate table
            if attribute.get("entity_unique_name") == node.unique_name and attribute.get("mapped_table")[1] == table_name:#mvd came from node
                attribute_entity = graph.get_node_by_name(attribute.get("entity_unique_name"))
                assert attribute_entity is not None
                assert attribute.get("mapped_table")[1] == table_name
                return True

    return False

def check_if_the_table_for_insert_parent_mvd(graph:Graph, node:Node, table_name):#this can happen if,
    #node contained in parent and parent has separate mvd table, node partially contained in parent and parent has separate mvd table, node all by itself but parent has a separate mvd table
    #if parent doesn't have a table, parent mvd stored as array inside child
    if node.is_entity() and node.is_subclass:
        for attribute in node.attribute_list:
            if attribute.get("is_multivalued") and attribute.get("mapped_table") is not None and attribute.get("is_in_separate_table"):#mvd in separate table
                if attribute.get("entity_unique_name") != node.unique_name and attribute.get("mapped_table")[1] == table_name:#mvd came from parent node not from node itself
                    attribute_entity = graph.get_node_by_name(attribute.get("entity_unique_name"))
                    assert attribute_entity is not None
                    assert attribute_entity.mapped_table is not None
                    assert attribute.get("mapped_table")[1] == table_name
                    return True
    return False

def get_corresponding_key_in_insert_values(graph:Graph, node:Node, values):
    assert len(node.key.table_key)==1
    for attribute in node.attribute_list:
       if attribute.get("pk_name", False):
           if attribute["pk_name"] in values:#assume single pk for class hierarchies
               return attribute["pk_name"]


def get_keys_for_insert_to_a_parent_from_node(graph:Graph, node:Node, table_name, primary_keys, values):
    assert len(node.key.table_key)==1#we can assume only one pk exists for class hierarchy
    #print(primary_keys)
    assert len(primary_keys)==1
    return (primary_keys[0], node.key.table_key[0][0])#table pk, pk in values

def check_if_folded_relationship_is_between_subclasses_and_all_subclasses_in_same_table(graph:Graph, node:Node, table_name):#e.g. [Person, Instructor, Student, Advisor]
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

def get_pk_ER_name_for_relationship(node, pk):
    for attribute in node.attribute_list:
        if attribute.get("pk_name", False) == pk:
            return attribute["pk_ER_name"]

def map_values_from_ER_names_to_physical_schema_keys(graph:Graph, node:Node, values):
    values_copy = {}
    for attribute in node.attribute_list:
        if attribute.get("pk_name", False):
            values_copy[attribute.get("pk_name")] = values.pop(attribute.get("pk_ER_name"))
        else:
            values_copy[attribute.get("name")] = values.pop(attribute.get("name"))
    return values_copy

#UPDATE table_name SET attr_name = 30 WHERE pk = 2; -> {table_name:, {attr_name:val,..}, pk:{pk1:, pk2:}}
def generate_insert_statements(entity_or_relationship_node:Node, values, tables: List[Tuple[str, List[Tuple[str, str, str]]]], custom_types: Dict[str, List[Tuple[str, str]]],
                               graph:Graph) -> List[str]:
    insert_statements = []

    #if an insert happens to Instructor, if there is a Person table, that insert should reflect in Person table as well
    #if an insert happens to a node, if its mvd in a separate table, that insert should be propagated

    values_deep_copy= copy.deepcopy(values)
    values_updated_to_match_table_columns = map_values_from_ER_names_to_physical_schema_keys(graph, entity_or_relationship_node, values_deep_copy)


    for table_name, attributes, is_both_entity_relationship_in_table, primary_keys in tables:
        if is_both_entity_relationship_in_table and entity_or_relationship_node.is_relationship():#folded relationship - relationship has to be 1:N
            if (check_if_folded_relationship_is_between_subclasses_and_all_subclasses_in_same_table(graph, entity_or_relationship_node, table_name) and
                    check_if_relationship_is_1_N(entity_or_relationship_node)):
                values_copy_2 = {}
                values_copy = copy.deepcopy(values)
                primary_key =  primary_keys[0]
                primary_key_ER_name = get_pk_ER_name_for_relationship(entity_or_relationship_node, primary_key)
                primary_key_value = values_copy.pop(primary_key_ER_name)#single pk for subclasses
                attr_name = entity_or_relationship_node.name.lower()+"_id" #e.g. advisor_id
                attr_name_ER_name = get_pk_ER_name_for_relationship(entity_or_relationship_node, attr_name)
                values_copy[attr_name] = values_copy.pop(attr_name_ER_name)
                values_copy_2["table_name"] = table_name
                values_copy_2["attributes"] = values_copy
                values_copy_2["primary_keys"] = {primary_key:primary_key_value}
                insert_update_statement = generate_update_statement(values_copy_2, table_name, attributes, custom_types)
                if insert_update_statement:
                    insert_statements.append(insert_update_statement)

            elif check_if_relationship_is_1_N(entity_or_relationship_node): #e.g. [Student, Advisor] - relationship folded to N side
                values_copy = copy.deepcopy(values)
                primary_key_values = {}
                values_copy_2 = {}
                for primary_key in primary_keys:#there could be more than 1 pks - e.g. if parent table is weak entity
                    primary_key_ER_name = get_pk_ER_name_for_relationship(entity_or_relationship_node, primary_key)
                    primary_key_values[primary_key] = values_copy.pop(primary_key_ER_name)
                values_copy_2["table_name"] = table_name
                values_copy_2["primary_keys"] = primary_key_values
                values_copy_2["attributes"] = values_copy
                insert_update_statement = generate_update_statement(values_copy_2, table_name, attributes, custom_types)
                if insert_update_statement:
                    insert_statements.append(insert_update_statement)
        else:

            #check for mvd tables
            if check_if_the_table_for_insert_own_mvd_attribute(graph, entity_or_relationship_node, table_name):
                for item in values_updated_to_match_table_columns[attributes[-1][0]]:#assume last entry is the mvd - there could be more than 1 pks but only 1 entry mvd at last
                    values_copy = {}
                    for primary_key in primary_keys:#there could be more than 1 pks - e.g. if parent table is weak entity
                        values_copy[primary_key] = values_updated_to_match_table_columns[primary_key]
                    values_copy[attributes[-1][0]] = item
                    insert_statement = generate_insert_statement_for_one_table(values_copy, table_name, primary_keys, attributes, custom_types)
                    if insert_statement:
                        insert_statements.append(insert_statement)

            elif check_if_the_table_for_insert_parent_mvd(graph, entity_or_relationship_node, table_name):#for class hierarchy - assume single primary key sufficient
                for item in values_updated_to_match_table_columns[attributes[-1][0]]:#assume last entry is the mvd - only 1 pk and only 1 entry mvd at last
                    values_copy = {}
                    primary_key = primary_keys[0]#only 1 pk from parent
                    if primary_key in values_updated_to_match_table_columns:#when child contained in parent which owns mvd- this can happen -e.g. when Instructor in Person, Instructor's pk is also person_id
                        values_copy[primary_key] = values_updated_to_match_table_columns[primary_key]
                    else:
                        values_key = get_corresponding_key_in_insert_values(graph, entity_or_relationship_node, values_updated_to_match_table_columns)
                        values_copy[primary_key] = values_updated_to_match_table_columns[values_key]
                    values_copy[attributes[-1][0]] = item
                    insert_statement = generate_insert_statement_for_one_table(values_copy, table_name, primary_keys, attributes, custom_types)
                    if insert_statement:
                        insert_statements.append(insert_statement)

            elif entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_subclass and entity_or_relationship_node.mapped_table[1] != table_name:#insert from subclass to parent
                attr_name_table, attr_name_in_values = get_keys_for_insert_to_a_parent_from_node(graph, entity_or_relationship_node, table_name, primary_keys, values)
                values_copy = copy.deepcopy(values_updated_to_match_table_columns)
                values_copy.pop(attr_name_in_values)
                values_copy[attr_name_table] = values_updated_to_match_table_columns[attr_name_in_values]
                insert_statement = generate_insert_statement_for_one_table(values_copy, table_name, primary_keys, attributes, custom_types,
                                                                           entity_or_relationship_node.unique_name)
                if insert_statement:
                    insert_statements.append(insert_statement)

            elif entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and entity_or_relationship_node.is_contained_in_parent:#folded weak entity as json array
                insert_update_statement = generate_update_statement_for_folded_weak_entity(values_updated_to_match_table_columns, table_name, primary_keys,
                                                                                           attributes, custom_types, entity_or_relationship_node)
                if insert_update_statement:
                    insert_statements.append(insert_update_statement)
            else:
                insert_statement = generate_insert_statement_for_one_table(values_updated_to_match_table_columns, table_name, primary_keys, attributes, custom_types,
                                                                           entity_or_relationship_node.unique_name, graph)
                if insert_statement:
                    insert_statements.append(insert_statement)

    return insert_statements

def generate_insert_statement_for_one_table(values, table_name, primary_keys, attributes: List[Tuple[str, str]], custom_types: Dict[str, List[Tuple[str, str]]],
                                            entity_name=None, graph=None)-> List[str]:
    temp_values = {}
    placeholders = {}

    for attr_name, attr_type, attr_unique_name in attributes:#Instructor mapped to say Person, Instructor
        if attr_name in values:#table Instructor, insert query Instructor handled here
            # Custom type without an array
            if attr_type in custom_types:#composite
                flat_values, placeholder = flatten_composite(values[attr_name], attr_type, custom_types)
                temp_values[attr_name] = flat_values
                placeholders[attr_name] = placeholder
            elif attr_type.endswith('[]'): #array attribute
                #doesn't handle composite type of array
                temp_values[attr_name] = values[attr_name]
                placeholders[attr_name] = f"ARRAY[{', '.join(['%s'] * len(temp_values[attr_name]))}]"
            else:
                # Here we have a simple attribute, but the value could be a list
                temp_values[attr_name] = [values[attr_name]]
                placeholders[attr_name] = '%s'

        elif '__' in attr_name:  # Check for flattened composite attributes
            parent, child = attr_name.split('__', 1)
            if parent in values and isinstance(values[parent], dict):
                if child in values[parent]:
                    temp_values[attr_name] = [values[parent][child]]
                    placeholders[attr_name] = '%s'

        elif attr_name == "role":
            temp_values[attr_name] = [entity_name]
            placeholders[attr_name] = '%s'


    assert temp_values

    if temp_values:
        columns = ', '.join(temp_values.keys())
        placeholders_str = ', '.join(placeholders.values())
        flat_values = [item for sublist in temp_values.values() for item in (sublist if isinstance(sublist, list) else [sublist])]

        insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders_str})"
        return (table_name, attributes, insert_sql, tuple(flat_values))
    else:
        return None

def generate_update_statement(values, table_name, attributes: List[Tuple[str, str]], custom_types: Dict[str, List[Tuple[str, str]]]):
    pk_values = {}
    pk_placeholders = {}

    temp_values = {}
    placeholders = {}

    for attr_name, attr_type, attr_unique_name in attributes:
        if attr_name in values["primary_keys"]:
            pk_values[attr_name] = [values["primary_keys"][attr_name]]
            pk_placeholders[attr_name] = '%s'
        elif attr_name in values["attributes"]:
            # Custom type without an array
            if attr_type in custom_types:#composite
                flat_values, placeholder = flatten_composite(values["attributes"][attr_name], attr_type, custom_types)
                temp_values[attr_name] = flat_values
                placeholders[attr_name] = placeholder
            elif attr_type.endswith('[]'): #array attribute
                #doesn't handle composite type of array
                temp_values[attr_name] = values["attributes"][attr_name]
                placeholders[attr_name] = f"ARRAY[{', '.join(['%s'] * len(temp_values[attr_name]))}]"
            else:
                # Here we have a simple attribute, but the value could be a list
                temp_values[attr_name] = [values["attributes"][attr_name]]
                placeholders[attr_name] = '%s'
        elif '__' in attr_name:  # Check for flattened composite attributes
            parent, child = attr_name.split('__', 1)
            if parent in values["attributes"] and isinstance(values["attributes"][parent], dict):
                if child in values["attributes"][parent]:
                    temp_values[attr_name] = [values["attributes"][parent][child]]
                    placeholders[attr_name] = '%s'

    assert temp_values, pk_values

    if temp_values and pk_values:
        columns = []
        for key in temp_values.keys():
            columns.append(key + "=" + placeholders[key])
        columns = ', '.join(columns)
        flat_values = [item for sublist in temp_values.values() for item in (sublist if isinstance(sublist, list) else [sublist])]

        pk_columns = []
        for key in pk_values.keys():
            pk_columns.append(key + "=" + pk_placeholders[key])
        pk_columns = 'and '.join(pk_columns)
        pk_flat_values = [item for sublist in pk_values.values() for item in (sublist if isinstance(sublist, list) else [sublist])]
        flat_values += pk_flat_values
        update_sql = f"UPDATE {table_name} SET {columns} WHERE {pk_columns}"
        return (table_name, attributes, update_sql, tuple(flat_values))
    else:
        return None

def generate_update_statement_for_folded_weak_entity(values, table_name, primary_keys, attributes: List[Tuple[str, str]], custom_types: Dict[str, List[Tuple[str, str]]],
                                                     weak_entity, graph=None)-> List[str]:
    pk_values = {}
    pk_placeholders = {}

    temp_values = {}
    placeholders = {}

    for attr_name in values:
        if attr_name in [attr for attr, _, _ in attributes]:
            assert attr_name in primary_keys
            pk_values[attr_name] = [values[attr_name]]
            pk_placeholders[attr_name] = '%s'
        else:
            assert attr_name in [attribute.get("pk_name" if "pk_name" in attribute else "name") for attribute in weak_entity.attribute_list]
            for attribute in weak_entity.attribute_list:
                attribute_name = attribute.get("pk_name" if "pk_name" in attribute else "name")
                if attr_name != attribute_name:
                    continue
                else:
                    attr_type = attribute.get("pk_type" if "pk_type" in attribute else "type")#discriminator attributes and other attributes of weak entity
                    if attr_type in custom_types:#composite
                        flat_values, placeholder = flatten_composite(values[attr_name], attr_type, custom_types)
                        temp_values[attr_name] = flat_values
                    elif attr_type.endswith('[]'): #array attribute
                        #doesn't handle composite type of array
                        temp_values[attr_name] = values[attr_name]
                    else:# Here we have a simple attribute, but the value could be a list
                        temp_values[attr_name] = values[attr_name]
    placeholders[weak_entity.unique_name] = '%s'

    assert temp_values, pk_values
    if temp_values and pk_values:

        flat_values = []
        temp_values_json = json.dumps(temp_values)
        flat_values.append(temp_values_json)

        pk_columns = []
        for key in pk_values.keys():
            pk_columns.append(key + "=" + pk_placeholders[key])
        pk_columns = 'and '.join(pk_columns)
        pk_flat_values = [item for sublist in pk_values.values() for item in (sublist if isinstance(sublist, list) else [sublist])]
        flat_values += pk_flat_values
        update_sql = f"UPDATE {table_name} SET {weak_entity.unique_name} = {weak_entity.unique_name} || {placeholders[weak_entity.unique_name]}::JSONB WHERE {pk_columns} "
        return (table_name, attributes, update_sql, tuple(flat_values))
    else:
        return None


def format_sql_statement(sql: str, values: Tuple[Any, ...]) -> str:
    # Use psycopg2's mogrify function to properly format the SQL statement
    # We create a dummy connection that we won't actually use to connect
    dummy_conn = psycopg2.connect(dbname="postgres", user="postgres", password="password")
    dummy_cursor = dummy_conn.cursor()

    # mogrify returns bytes, so we decode it to a string
    formatted_sql = dummy_cursor.mogrify(sql, values).decode('utf-8')

    # Close the dummy connection
    dummy_cursor.close()
    dummy_conn.close()

    return formatted_sql





