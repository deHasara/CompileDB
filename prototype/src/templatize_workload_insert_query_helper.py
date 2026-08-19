import copy
import csv
import json
from collections import defaultdict
from typing import List, Tuple, Dict, Any
import psycopg2
from er_graph import Graph, serialize_graph, Node
import re

def escape_pg_composite_element(value):
    if not isinstance(value, str):
        value = str(value)
    # Escape double quotes
    value = value.replace('"', '""')
    # Quote if value contains comma, parentheses, whitespace, or double quotes
    if re.search(r'[,"\s()]', value):
        return f'"{value}"'
    return value

def to_pg_composite(values):
    escaped = [escape_pg_composite_element(v) for v in values]
    return f"({','.join(escaped)})"

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

#get table pk corresponding to weak entity pk component coming from parent(table's pk is weak entity's parent pk)
#when parent is distributed in node cover - pk names will be different
#e.g. when product distributed in product(product_id), physical(physicalproduct_id), digital(digitalproduct_id), weak entity's parent pk component which is product_id
#should be mapped to all 3 pks corresponding to each table
def get_keys_for_insert_to_a_hierarchy_node_distributed_in_node_cover_from_folded_weak_entity_node(graph:Graph, node:Node, table_name, primary_keys, values):
    assert len(node.key.table_key) >= 1#weak entity can have more than 1 component for pk - discriminator key is optional so can be 1 as well
    assert len(primary_keys)==1 #insert table is corresponding to a hierarchy node hence only one primary key - and weak entity folded in it
    return (primary_keys[0], node.key.table_key[0][0][0])#table pk, pk component of weak entity coming from hierarchy parent node
            #in weak entity key list, first entry is from the parent - since parent is a subclass which is a strong entity, weak entity will have at most one identifying parent
            #e.g. if table is product - return product_id, product_id, if table s physical - return physicalproduct_id, product_id etc. for each table in node cover

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

#used for folded relationships only
def get_pk_ER_name_for_relationship(node, pk):
    for attribute in node.attribute_list:
        if "pk_name" in attribute:
            if attribute.get("pk_name", False) == pk:
                return attribute["pk_ER_name"]

    #if the first return didn't work, all remaining cases where relationship pk not equal to table pk should be the cases where
    #relationship should be folded in a node distributed in node cover - and current table's pk name not equal to relationship pk
    for attribute in node.attribute_list:
        if "pk_name" in attribute:
            if attribute.get("pk_name", False) != pk:
                #if table pk not equal to relationship pk - then the relationship should be folded in a node distributed in node cover - and current table's pk name not equal to
                #relationship pk
                #product(product_id) ABI, physical(physicalproduct_id) ABI, digital(digitalproduct_id) ABI and category_products folded
                #for each pk which are product_id, physicalproduct_id, digitalproduct_id - need to return  product_id of category_products as corresponding pk of relationship
                assert check_if_relationship_is_1_N(node) #should assert it is folded as well - but not checked here
                many_side = node.entity2 if (node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']) else node.entity1
                assert len(many_side.node_cover)>1
                #need to get relationship pk corresponding to many side pk - for many-to-one relationship, first key is the key from many side
                #so return the ER name corresponding to very first pk of relationship - that is the first pk_name found while iterating attribute_list
                return attribute["pk_ER_name"]


def map_values_from_ER_names_to_physical_schema_keys(graph:Graph, node:Node, values, index_mapping):
    values_copy = {}
    index_mapping_copy = {}
    for attribute in node.attribute_list:
        if attribute.get("pk_name", False):
            values_copy[attribute.get("pk_name")] = values.pop(attribute.get("pk_ER_name"))
            index_mapping_copy[attribute.get("pk_name")] = index_mapping.pop(attribute.get("pk_ER_name"))
        else:
            values_copy[attribute.get("name")] = values.pop(attribute.get("name"))
            index_mapping_copy[attribute.get("name")] = index_mapping.pop(attribute.get("name"))
    return values_copy, index_mapping_copy

#UPDATE table_name SET attr_name = 30 WHERE pk = 2; -> {table_name:, {attr_name:val,..}, pk:{pk1:, pk2:}}
def generate_insert_statements(entity_or_relationship_node:Node, values, index_mapping, tables: List[Tuple[str, List[Tuple[str, str, str]]]], custom_types: Dict[str, List[Tuple[str, str]]],
                                        graph:Graph, insert_table_attribute_names:Dict, table_index_mapping_for_node) -> List[str]:

    insert_statements = []

    #if an insert happens to Instructor, if there is a Person table, that insert should reflect in Person table as well
    #if an insert happens to a node, if its mvd in a separate table, that insert should be propagated

    values_deep_copy= copy.deepcopy(values)
    index_mapping_deep_copy= copy.deepcopy(index_mapping)
    values_updated_to_match_table_columns, index_mapping_updated_to_match_table_columns = (
        map_values_from_ER_names_to_physical_schema_keys(graph, entity_or_relationship_node, values_deep_copy, index_mapping_deep_copy))


    for table_name, attributes, is_both_entity_relationship_in_table, primary_keys in tables:
        if is_both_entity_relationship_in_table and entity_or_relationship_node.is_relationship():#folded relationship - relationship has to be 1:N
            if (check_if_folded_relationship_is_between_subclasses_and_all_subclasses_in_same_table(graph, entity_or_relationship_node, table_name) and
                    check_if_relationship_is_1_N(entity_or_relationship_node)):
                values_copy_2 = {}
                values_copy = copy.deepcopy(values)
                index_mapping_copy = copy.deepcopy(index_mapping)
                primary_key =  primary_keys[0]
                primary_key_ER_name = get_pk_ER_name_for_relationship(entity_or_relationship_node, primary_key)
                primary_key_value = values_copy.pop(primary_key_ER_name)#single pk for subclasses
                attr_name = entity_or_relationship_node.name.lower()+"_id" #e.g. advisor_id
                attr_name_ER_name = get_pk_ER_name_for_relationship(entity_or_relationship_node, attr_name)
                values_copy[attr_name] = values_copy.pop(attr_name_ER_name)
                values_copy_2["table_name"] = table_name
                values_copy_2["attributes"] = values_copy
                values_copy_2["primary_keys"] = {primary_key:primary_key_value}
                index_mapping_copy[primary_key] = index_mapping_copy.pop(primary_key_ER_name)
                index_mapping_copy[attr_name] = index_mapping_copy.pop(attr_name_ER_name)
                inserted_attribute_names, table_index_list, columns, pk_columns, insert_statement = generate_update_statement(values_copy_2, index_mapping_copy, table_name, attributes, custom_types)
                table_identifier = table_name + "_" + entity_or_relationship_node.unique_name#relationship can be folded in multiple tables - need table_name to uniquly identify
                if table_identifier not in insert_table_attribute_names:#need a global identifier since insert_table_attribute_names dict is for all nodes
                    insert_table_attribute_names[table_identifier] = inserted_attribute_names
                if table_name not in table_index_mapping_for_node:#table_index_mapping_for_node is for node only - also need the actual table name since it will be used for templatized insert
                    table_index_mapping_for_node[table_name] = (table_index_list, columns, pk_columns, False)#(table_indices_list, table columns with placeholder str, pk columns with placeholder str, is_mvd_table)
                if insert_statement:
                    insert_statements.append(insert_statement)

            elif check_if_relationship_is_1_N(entity_or_relationship_node): #e.g. [Student, Advisor] - relationship folded to N side
                values_copy = copy.deepcopy(values)
                index_mapping_copy = copy.deepcopy(index_mapping)
                primary_key_values = {}
                values_copy_2 = {}
                for primary_key in primary_keys:#there could be more than 1 pks - e.g. if parent table is weak entity
                    primary_key_ER_name = get_pk_ER_name_for_relationship(entity_or_relationship_node, primary_key)
                    primary_key_values[primary_key] = values_copy.pop(primary_key_ER_name)
                    index_mapping_copy[primary_key] = index_mapping_copy.pop(primary_key_ER_name)#if relationship folded in hierarchy node distributed in node cover
                                                            #need to map the relationship's pk coming from node distributed in node cover to each corresponding table in node cover
                                #e.g. update product_id of category_products to product_id to product table, to physicalproduct_id to physical p. table etc. if product distributed in node cover
                values_copy_2["table_name"] = table_name
                values_copy_2["primary_keys"] = primary_key_values
                values_copy_2["attributes"] = values_copy
                inserted_attribute_names, table_index_list, columns, pk_columns, insert_statement = generate_update_statement(values_copy_2, index_mapping_copy,
                                                                                                         table_name, attributes, custom_types)
                table_identifier = table_name + "_" + entity_or_relationship_node.unique_name#relationship can be folded in multiple tables - need table_name to uniquly identify
                if table_identifier not in insert_table_attribute_names:
                    insert_table_attribute_names[table_identifier] = inserted_attribute_names
                if table_name not in table_index_mapping_for_node:
                    table_index_mapping_for_node[table_name] = (table_index_list, columns, pk_columns, False)
                if insert_statement:
                    insert_statements.append(insert_statement)
        else:

            #check for mvd tables
            if check_if_the_table_for_insert_own_mvd_attribute(graph, entity_or_relationship_node, table_name):

                table_index_list = []
                for primary_key in primary_keys:#pk consists of both pk from original table and mvd attribute
                    table_index_list.append(index_mapping_updated_to_match_table_columns[primary_key])
                #if table_name not in table_index_mapping_for_node:
                #    table_index_mapping_for_node[table_name] = (table_index_list, True)

                for item in values_updated_to_match_table_columns[attributes[-1][0]]:#assume last entry is the mvd - there could be more than 1 pks but only 1 entry mvd at last
                    values_copy = {}
                    for primary_key in primary_keys:#there could be more than 1 pks - e.g. if parent table is weak entity
                        values_copy[primary_key] = values_updated_to_match_table_columns[primary_key]
                    values_copy[attributes[-1][0]] = item
                    inserted_attribute_names, columns, placeholders_str, insert_statement = generate_insert_statement_for_mvd_table(values_copy,
                                                                                                         table_name, primary_keys, attributes, custom_types)
                    if table_name not in insert_table_attribute_names:
                        insert_table_attribute_names[table_name] = inserted_attribute_names
                    if table_name not in table_index_mapping_for_node:
                        table_index_mapping_for_node[table_name] = (table_index_list, columns, placeholders_str, True)#(table_indices_list, table columns str, placeholder str, is_mvd_table)
                    if insert_statement:
                        insert_statements.append(insert_statement)

            elif check_if_the_table_for_insert_parent_mvd(graph, entity_or_relationship_node, table_name):#for class hierarchy - assume single primary key sufficient

                table_index_list = []
                primary_key = primary_keys[0]#0th index pk - pk consists of [pk, mvd]
                if primary_key in values_updated_to_match_table_columns:#when child contained in parent which owns mvd- this can happen -e.g. when Instructor in Person, Instructor's pk is also person_id
                    table_index_list.append(index_mapping_updated_to_match_table_columns[primary_key])
                else:
                    values_key = get_corresponding_key_in_insert_values(graph, entity_or_relationship_node, values_updated_to_match_table_columns)
                    table_index_list.append(index_mapping_updated_to_match_table_columns[values_key])
                table_index_list.append(index_mapping_updated_to_match_table_columns[attributes[-1][0]])#mvd
                #if table_name not in table_index_mapping_for_node:
                #    table_index_mapping_for_node[table_name] = (table_index_list, True)

                for item in values_updated_to_match_table_columns[attributes[-1][0]]:#assume last entry is the mvd - only 1 pk and only 1 entry mvd at last
                    values_copy = {}
                    primary_key = primary_keys[0]#only 1 pk from parent
                    if primary_key in values_updated_to_match_table_columns:#when child contained in parent which owns mvd- this can happen -e.g. when Instructor in Person, Instructor's pk is also person_id
                        values_copy[primary_key] = values_updated_to_match_table_columns[primary_key]
                    else:
                        values_key = get_corresponding_key_in_insert_values(graph, entity_or_relationship_node, values_updated_to_match_table_columns)
                        values_copy[primary_key] = values_updated_to_match_table_columns[values_key]
                    values_copy[attributes[-1][0]] = item
                    inserted_attribute_names, columns, placeholders_str, insert_statement = generate_insert_statement_for_mvd_table(values_copy, table_name,
                                                                                                         primary_keys, attributes, custom_types)
                    if table_name not in insert_table_attribute_names:
                        insert_table_attribute_names[table_name] = inserted_attribute_names
                    if table_name not in table_index_mapping_for_node:
                        #table_indices_list is handled without getting the indices list since each insert is only - pk, mvd attribute
                        table_index_mapping_for_node[table_name] = (table_index_list, columns, placeholders_str, True)#(table_indices_list, table columns str, placeholder str, is_mvd_table)
                    if insert_statement:
                        insert_statements.append(insert_statement)

            elif entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_subclass and entity_or_relationship_node.mapped_table[1] != table_name:#insert from subclass to parent
                attr_name_table, attr_name_in_values = get_keys_for_insert_to_a_parent_from_node(graph, entity_or_relationship_node, table_name, primary_keys, values)
                values_copy = copy.deepcopy(values_updated_to_match_table_columns)
                values_copy.pop(attr_name_in_values)
                values_copy[attr_name_table] = values_updated_to_match_table_columns[attr_name_in_values]
                index_mapping_updated_to_match_table_columns_copy = copy.deepcopy(index_mapping_updated_to_match_table_columns)
                index_mapping_updated_to_match_table_columns_copy.pop(attr_name_in_values)
                index_mapping_updated_to_match_table_columns_copy[attr_name_table] = index_mapping_updated_to_match_table_columns[attr_name_in_values]
                inserted_attribute_names, table_index_list, columns, placeholders_str, insert_statement = generate_insert_statement_for_one_table(values_copy, index_mapping_updated_to_match_table_columns_copy,
                                                                                                                       table_name, primary_keys, attributes, custom_types, entity_or_relationship_node.unique_name)
                if table_name not in insert_table_attribute_names:
                    insert_table_attribute_names[table_name] = inserted_attribute_names
                if table_name not in table_index_mapping_for_node:
                    table_index_mapping_for_node[table_name] = (table_index_list, columns, placeholders_str, False)#(table_indices_list, table columns str, placeholder str, is_mvd_table)
                if insert_statement:
                    insert_statements.append(insert_statement)

            elif entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and entity_or_relationship_node.is_contained_in_parent:#folded weak entity as json array
                if len(entity_or_relationship_node.parent_entity.node_cover) > 1:#need to match pk of each table in node cover with weak entity's pk component coming from that parent distributed in node cover
                    attr_name_table, attr_name_in_values = get_keys_for_insert_to_a_hierarchy_node_distributed_in_node_cover_from_folded_weak_entity_node(graph,
                                                                                            entity_or_relationship_node, table_name, primary_keys, values)
                    values_copy = copy.deepcopy(values_updated_to_match_table_columns)
                    values_copy.pop(attr_name_in_values)
                    values_copy[attr_name_table] = values_updated_to_match_table_columns[attr_name_in_values]
                    index_mapping_updated_to_match_table_columns_copy = copy.deepcopy(index_mapping_updated_to_match_table_columns)
                    index_mapping_updated_to_match_table_columns_copy.pop(attr_name_in_values)
                    index_mapping_updated_to_match_table_columns_copy[attr_name_table] = index_mapping_updated_to_match_table_columns[attr_name_in_values]
                    inserted_attribute_names, table_index_list, placeholders_node, pk_columns, insert_statement  = generate_update_statement_for_folded_weak_entity(values_copy, index_mapping_updated_to_match_table_columns_copy,
                                                                                                                                                                    table_name, primary_keys, attributes, custom_types, entity_or_relationship_node)
                else:
                    inserted_attribute_names, table_index_list, placeholders_node, pk_columns, insert_statement  = generate_update_statement_for_folded_weak_entity(values_updated_to_match_table_columns, index_mapping_updated_to_match_table_columns,
                                                                                                                   table_name, primary_keys, attributes, custom_types, entity_or_relationship_node)

                table_identifier = table_name + "_" + entity_or_relationship_node.unique_name#weak entity can be folded in multiple tables - need table_name to uniquly identify
                if table_identifier not in insert_table_attribute_names:#need a global identifier since insert_table_attribute_names dict is for all nodes
                    insert_table_attribute_names[table_identifier] = inserted_attribute_names
                if table_name not in table_index_mapping_for_node:#table_index_mapping_for_node is for node only - also need the actual table name since it will be used for templatized insert
                    table_index_mapping_for_node[table_name] = (table_index_list, placeholders_node, pk_columns, False)#(table_indices_list, weak entity columns str, placeholder str, is_mvd_table)
                if insert_statement:
                    insert_statements.append(insert_statement)

            else:
                inserted_attribute_names, table_index_list, columns, placeholders_str, insert_statement = generate_insert_statement_for_one_table(values_updated_to_match_table_columns, index_mapping_updated_to_match_table_columns,
                                                                                                                       table_name, primary_keys, attributes, custom_types, entity_or_relationship_node.unique_name, graph)
                if table_name not in insert_table_attribute_names:
                    insert_table_attribute_names[table_name] = inserted_attribute_names
                if table_name not in table_index_mapping_for_node:
                    table_index_mapping_for_node[table_name] = (table_index_list, columns, placeholders_str, False)#(table_indices_list, table columns str, placeholder str, is_mvd_table)
                if insert_statement:
                    insert_statements.append(insert_statement)
    return insert_statements


#Batch insert - insert to in-memory csv for batch insert
def generate_insert_statement_for_one_table(values, index_mapping, table_name, primary_keys, attributes: List[Tuple[str, str]], custom_types: Dict[str, List[Tuple[str, str]]],
                                            entity_name=None, graph=None)-> List[str]:
    attribute_names = []
    table_index_mapping = []

    temp_values = {}
    placeholders = {}

    for attr_name, attr_type, attr_unique_name, attr_entity_unique_name in attributes:#Instructor mapped to say Person, Instructor
        if attr_name in values:#table Instructor, insert query Instructor handled here
            # Custom type without an array
            if attr_type in custom_types:#composite
                #flat_values, placeholder = flatten_composite(values[attr_name], attr_type, custom_types)
                temp_values[attr_name] = [to_pg_composite(values[attr_name])]
                placeholders[attr_name] = '%s'
                attribute_names.append(attr_name)
                table_index_mapping.append(index_mapping[attr_name])
            elif attr_type.endswith('[]'): #array attribute
                #doesn't handle composite type of array
                temp_values[attr_name] = ["{" + ",".join(values[attr_name]) + "}"]
                placeholders[attr_name] = '%s'
                attribute_names.append(attr_name)
                table_index_mapping.append(index_mapping[attr_name])
            else:
                # Here we have a simple attribute, but the value could be a list
                temp_values[attr_name] = [values[attr_name]]
                placeholders[attr_name] = '%s'
                attribute_names.append(attr_name)
                table_index_mapping.append(index_mapping[attr_name])

        elif '__' in attr_name:  # Check for flattened composite attributes
            parent, child = attr_name.split('__', 1)
            if parent in values and isinstance(values[parent], dict):
                if child in values[parent]:
                    temp_values[attr_name] = [values[parent][child]]
                    placeholders[attr_name] = '%s'
                    attribute_names.append(attr_name)
                    table_index_mapping.append(index_mapping[attr_name])

        elif attr_name == "role":
            temp_values[attr_name] = [entity_name]
            placeholders[attr_name] = '%s'
            attribute_names.append(attr_name)
            table_index_mapping.append(entity_name)

        else:#null - if multiple children mapped to same table - some columns will be null for each child in insert
            temp_values[attr_name] = [None]
            placeholders[attr_name] = '%s'
            attribute_names.append(attr_name)
            table_index_mapping.append(None)

    assert temp_values

    if temp_values:
        columns = ', '.join(temp_values.keys())
        placeholders_str = ', '.join(placeholders.values())
        flat_values = [item for sublist in temp_values.values() for item in (sublist if isinstance(sublist, list) else [sublist])]

        insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders_str})"
        return attribute_names, table_index_mapping, columns, placeholders_str, (insert_sql, tuple(flat_values))
    else:
        return None


def generate_insert_statement_for_mvd_table(values, table_name, primary_keys, attributes: List[Tuple[str, str]], custom_types: Dict[str, List[Tuple[str, str]]],
                                            entity_name=None, graph=None)-> List[str]:
    attribute_names = []

    temp_values = {}
    placeholders = {}

    for attr_name, attr_type, attr_unique_name, attr_entity_unique_name in attributes:#Instructor mapped to say Person, Instructor
        if attr_name in values:#table Instructor, insert query Instructor handled here
            # Custom type without an array
            if attr_type in custom_types:#composite
                #flat_values, placeholder = flatten_composite(values[attr_name], attr_type, custom_types)
                temp_values[attr_name] = [to_pg_composite(values[attr_name])]
                placeholders[attr_name] = '%s'
                attribute_names.append(attr_name)
            elif attr_type.endswith('[]'): #array attribute
                #doesn't handle composite type of array
                temp_values[attr_name] = ["{" + ",".join(values[attr_name]) + "}"]
                placeholders[attr_name] = '%s'
                attribute_names.append(attr_name)
            else:
                # Here we have a simple attribute, but the value could be a list
                temp_values[attr_name] = [values[attr_name]]
                placeholders[attr_name] = '%s'
                attribute_names.append(attr_name)

        elif '__' in attr_name:  # Check for flattened composite attributes
            parent, child = attr_name.split('__', 1)
            if parent in values and isinstance(values[parent], dict):
                if child in values[parent]:
                    temp_values[attr_name] = [values[parent][child]]
                    placeholders[attr_name] = '%s'
                    attribute_names.append(attr_name)

    assert temp_values

    if temp_values:
        columns = ', '.join(temp_values.keys())
        placeholders_str = ', '.join(placeholders.values())
        flat_values = [item for sublist in temp_values.values() for item in (sublist if isinstance(sublist, list) else [sublist])]

        insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders_str})"
        return attribute_names, columns, placeholders_str, (insert_sql, tuple(flat_values))
    else:
        return None


#multiple relationships can be folded in table - different attribute sets for each update by folded node - need to identify by folded relationship node
def generate_update_statement(values, index_mapping, table_name, attributes: List[Tuple[str, str]], custom_types: Dict[str, List[Tuple[str, str]]]):
    attribute_names = []
    table_index_mapping = [[],[]]#first [] for indices of attributes of folded relationship, second [] for indice/s of attribute/s which is/are pk of table

    pk_values = {}
    pk_placeholders = {}

    temp_values = {}
    placeholders = {}

    for attr_name, attr_type, attr_unique_name, attr_entity_unique_name in attributes:
        if attr_name in values["primary_keys"]:
            pk_values[attr_name] = [values["primary_keys"][attr_name]]
            pk_placeholders[attr_name] = '%s'
            attribute_names.append(attr_name)
            table_index_mapping[1].append(index_mapping[attr_name])#add index of relevant attrbute of node - node attributes are indexed
        elif attr_name in values["attributes"]:
            # Custom type without an array
            if attr_type in custom_types:#composite
                #flat_values, placeholder = flatten_composite(values["attributes"][attr_name], attr_type, custom_types)
                temp_values[attr_name] = [to_pg_composite(values["attributes"][attr_name])]
                placeholders[attr_name] = '%s'
                attribute_names.append(attr_name)
                table_index_mapping[0].append(index_mapping[attr_name])
            elif attr_type.endswith('[]'): #array attribute
                #doesn't handle composite type of array
                temp_values[attr_name] = ["{" + ",".join(values["attributes"][attr_name]) + "}"]
                placeholders[attr_name] = '%s'
                attribute_names.append(attr_name)
                table_index_mapping[0].append(index_mapping[attr_name])
            else:
                # Here we have a simple attribute, but the value could be a list
                val = values.get(attr_name)
                temp_values[attr_name] = [values["attributes"][attr_name]]
                placeholders[attr_name] = '%s'
                attribute_names.append(attr_name)
                table_index_mapping[0].append(index_mapping[attr_name])
        elif '__' in attr_name:  # Check for flattened composite attributes
            parent, child = attr_name.split('__', 1)
            if parent in values["attributes"] and isinstance(values["attributes"][parent], dict):
                if child in values["attributes"][parent]:
                    temp_values[attr_name] = [values[parent][child]]
                    placeholders[attr_name] = '%s'
                    attribute_names.append(attr_name)
                    table_index_mapping[0].append(index_mapping[attr_name])

    assert temp_values and attribute_names

    if temp_values and pk_values:
        columns = []
        for key in temp_values.keys():
            columns.append(key + "=" + placeholders[key])
        columns = ', '.join(columns)
        flat_values = [item for sublist in temp_values.values() for item in (sublist if isinstance(sublist, list) else [sublist])]

        pk_columns = []
        for key in pk_values.keys():
            pk_columns.append(key + "=" + pk_placeholders[key])
        pk_columns = ' and '.join(pk_columns)
        pk_flat_values = [item for sublist in pk_values.values() for item in (sublist if isinstance(sublist, list) else [sublist])]
        flat_values += pk_flat_values
        update_sql = f"UPDATE {table_name} SET {columns} WHERE {pk_columns}"
        return attribute_names, table_index_mapping, columns, pk_columns, (update_sql, tuple(flat_values))
    else:
        return None


def generate_update_statement_for_folded_weak_entity(values, index_mapping, table_name, primary_keys, attributes: List[Tuple[str, str]], custom_types: Dict[str, List[Tuple[str, str]]],
                                                     weak_entity, graph=None)-> List[str]:
    attribute_names = []
    table_index_mapping = [[],[]]#first [] for indices of attributes of folded weak entity, second [] for indice/s of attribute/s which is/are pk of table

    pk_values = {}
    pk_placeholders = {}

    temp_values = {}
    placeholders = {}

    for attr_name in values:
        if attr_name in [attr for attr, _, _, _ in attributes]:
            assert attr_name in primary_keys
            pk_values[attr_name] = [values[attr_name]]
            pk_placeholders[attr_name] = '%s'
            attribute_names.append(attr_name)
            table_index_mapping[1].append(index_mapping[attr_name])
        else:
            assert attr_name in [attribute.get("pk_name" if "pk_name" in attribute else "name") for attribute in weak_entity.attribute_list]
            for attribute in weak_entity.attribute_list:
                attribute_name = attribute.get("pk_name" if "pk_name" in attribute else "name")
                if attr_name != attribute_name:
                    continue
                else:
                    attr_type = attribute.get("pk_type" if "pk_type" in attribute else "type")#discriminator attributes and other attributes of weak entity
                    if attr_type in custom_types:#composite
                        #flat_values, placeholder = flatten_composite(values[attr_name], attr_type, custom_types)
                        temp_values[attr_name] = [to_pg_composite(values[attr_name])]
                        attribute_names.append(attr_name)
                        table_index_mapping[0].append(index_mapping[attr_name])
                    elif attr_type.endswith('[]'): #array attribute
                        #doesn't handle composite type of array
                        temp_values[attr_name] = ["{" + ",".join(values[attr_name]) + "}"]
                        attribute_names.append(attr_name)
                        table_index_mapping[0].append(index_mapping[attr_name])
                    else:# Here we have a simple attribute, but the value could be a list
                        temp_values[attr_name] = values[attr_name]
                        attribute_names.append(attr_name)
                        table_index_mapping[0].append(index_mapping[attr_name])
                    break
    placeholders[weak_entity.unique_name] = '%s'#single placeholder for all attributes of weak entity - aggregated to single column

    assert temp_values, pk_values
    if temp_values and pk_values:

        flat_values = []
        temp_values_json = json.dumps([temp_values])
        flat_values.append(temp_values_json)

        pk_columns = []
        for key in pk_values.keys():
            pk_columns.append(key + "=" + pk_placeholders[key])
        pk_columns = ' and '.join(pk_columns)
        pk_flat_values = [item for sublist in pk_values.values() for item in (sublist if isinstance(sublist, list) else [sublist])]
        flat_values += pk_flat_values
        update_sql = f"UPDATE {table_name} SET {weak_entity.unique_name} = COALESCE({weak_entity.unique_name}, '[]'::jsonb) || {placeholders[weak_entity.unique_name]}::JSONB WHERE {pk_columns} "
        return attribute_names, table_index_mapping, placeholders[weak_entity.unique_name], pk_columns, (update_sql, tuple(flat_values))
    else:
        return None

def execute_templatized_insert(graph, entity_or_relationship_node:Node, values, tables_insert_index_mapping, node_index_to_attribute_mapping,
                               tables: List[Tuple[str, List[Tuple[str, str, str]]]]):
    insert_statements = []
    for table_name, (table_indices_list, columns_str, placeholders_str, is_mvd_table) in tables_insert_index_mapping.items():

        if not is_mvd_table:
            if entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and entity_or_relationship_node.is_contained_in_parent:
                flat_values = []

                temp_values = {}#weak entity attributes
                weak_entity_attribute_indices = table_indices_list[0]
                for index_value in weak_entity_attribute_indices:
                    if isinstance(index_value, int):#index
                        attr_name = node_index_to_attribute_mapping.get(index_value)
                        value = values.get(attr_name)
                        if isinstance(value, (tuple)):
                            temp_values[attr_name] = to_pg_composite(value)
                        elif isinstance(value, (list)):
                            temp_values[attr_name] = "{" + ",".join(value) + "}"
                        else:
                            temp_values[attr_name] = value
                temp_values_json = json.dumps([temp_values])
                flat_values.append(temp_values_json)

                pk_values = []#table pk
                pk_attributes_indices = table_indices_list[1]
                for index_value in pk_attributes_indices:
                    if isinstance(index_value, int):#index
                        value = values.get(node_index_to_attribute_mapping.get(index_value))
                        if isinstance(value, (tuple)):
                            pk_values.append(to_pg_composite(value))
                        elif isinstance(value, (list)):
                            pk_values.append("{" + ",".join(value) + "}")
                        else:
                            pk_values.append(value)
                pk_flat_values = [item for sublist in pk_values for item in (sublist if isinstance(sublist, list) else [sublist])]
                flat_values += pk_flat_values

                insert_sql = (f"UPDATE {table_name} SET {entity_or_relationship_node.unique_name} = "
                              f"COALESCE({entity_or_relationship_node.unique_name}, '[]'::jsonb) || {columns_str}::JSONB WHERE {placeholders_str} ")

            elif entity_or_relationship_node.is_relationship() and graph.config[entity_or_relationship_node.unique_name] == "folded_to_many_side":
                temp_values = []#non-pk relationship attributes
                relationship_non_pk_attribute_indices = table_indices_list[0]
                for index_value in relationship_non_pk_attribute_indices:
                    if isinstance(index_value, int):#index
                        attr_name = node_index_to_attribute_mapping.get(index_value)
                        value = values.get(attr_name)
                        if isinstance(value, (tuple)):
                            temp_values.append(to_pg_composite(value))
                        elif isinstance(value, (list)):
                            temp_values.append("{" + ",".join(value) + "}")
                        else:
                            temp_values.append(value)
                flat_values = [item for sublist in temp_values for item in (sublist if isinstance(sublist, list) else [sublist])]

                pk_values = []#table pk
                pk_attributes_indices = table_indices_list[1]
                for index_value in pk_attributes_indices:
                    if isinstance(index_value, int):#index
                        value = values.get(node_index_to_attribute_mapping.get(index_value))
                        if isinstance(value, (tuple)):
                            pk_values.append(to_pg_composite(value))
                        elif isinstance(value, (list)):
                            pk_values.append("{" + ",".join(value) + "}")
                        else:
                            pk_values.append(value)
                pk_flat_values = [item for sublist in pk_values for item in (sublist if isinstance(sublist, list) else [sublist])]
                flat_values += pk_flat_values

                insert_sql = f"UPDATE {table_name} SET {columns_str} WHERE {placeholders_str}"

            else:
                temp_values = []
                for index_value in table_indices_list:
                    if isinstance(index_value, int):#index
                        value = values.get(node_index_to_attribute_mapping.get(index_value))
                        if isinstance(value, (tuple)):
                            temp_values.append(to_pg_composite(value))
                        elif isinstance(value, (list)):
                            temp_values.append("{" + ",".join(value) + "}")
                        else:
                            temp_values.append(value)
                    else:#role, none
                        temp_values.append(index_value)

                flat_values = [item for sublist in temp_values for item in (sublist if isinstance(sublist, list) else [sublist])]
                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders_str})"

            insert_statements.append((insert_sql, tuple(flat_values)))
        else:
            mvd_index = table_indices_list[-1]#last attribute
            mvd_list_size = len(values.get(node_index_to_attribute_mapping.get(mvd_index)))
            if mvd_list_size:
                for i in range(mvd_list_size):
                    temp_values = []
                    for index_value in table_indices_list[:-1]:#pks - except mvd
                        temp_values.append(values.get(node_index_to_attribute_mapping.get(index_value)))
                    temp_values.append(values.get(node_index_to_attribute_mapping.get(mvd_index))[i])
                    flat_values = [item for sublist in temp_values for item in (sublist if isinstance(sublist, list) else [sublist])]
                    insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders_str})"
                    insert_statements.append((insert_sql, tuple(flat_values)))

    return insert_statements


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










