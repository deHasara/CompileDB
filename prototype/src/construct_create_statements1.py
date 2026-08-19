import logging
from collections import deque
from enum import unique

from er_graph import NodeType, EdgeType, Graph, Edge, Node, Key
import json
from typing import List, Dict, Any, Tuple

## We could use a different modifier to create the internal primary keys
## For now, we will assume that each main entity has an "_id" attribute that we can use for this purpose
INTERNAL_MODIFIER = ""


##############################################################################################################
### This module will generate the create table statements for given ER graph and a set of connected subgraphs.
##############################################################################################################

def get_attribute_type(attr_type: str) -> str:
    if attr_type == 'INT' or attr_type == 'INTEGER':
        return 'INTEGER'
    elif attr_type == 'VARCHAR':
        return 'VARCHAR(255)'
    elif attr_type == 'COMPOSITE':
        return 'JSONB'
    else:
        return 'TEXT'

# Construct a CREATE TYPE statement for composite type that needs to be created. This is done recursively so that we might create composite types that contain other composite types.
#
# The return value here will be a list for each composite type
def create_composite_type(graph: Graph, node:Node, created_types_names, created_types):
    type_name = f"{node.unique_name.replace('.', '_')}_type"
    if type_name in created_types:
        return type_name

    sub_columns = []

    for sub_node in node.children:
        if sub_node.attr_type == 'COMPOSITE':
            sub_type_name = create_composite_type(graph, sub_node, created_types_names, created_types)
            sub_columns.append((sub_node.unique_name.split('.')[-1], sub_type_name))
        else:
            sub_columns.append((sub_node.unique_name.split('.')[-1], get_attribute_type(sub_node.attr_type)))

    created_types_names.add(type_name)
    created_types[type_name] = sub_columns

    return type_name

#defining node keys for nodes depends on the selected physical configuration

def get_top_class_in_table(table, parent):#return immediate top parent in the same table if exists
    if parent.parent_entity is None:#in the configuration - configuration.json -  sub class hierarchy should be put in an order, otherwise parent might not be initialized
        return parent
    elif parent.parent_entity.mapped_table==table:
        parent = parent.parent_entity
        return get_top_class_in_table(table, parent)
    return parent

def get_the_immediate_parent_if_exists_in_a_table(parent):#return immediate top parent in a different table if exists
    if parent.mapped_table is not None:
        return parent#return immediate parent
    elif parent.parent_entity is None:
        return None
    else:
        return get_the_immediate_parent_if_exists_in_a_table(parent.parent_entity)

#multiple 1_to_many folded in same table means - all share same many entity - 1 side may/may not be same entity. If 1-side is also same, need to uniquely identify each relationship within table since
#all folded in one table
def check_if_folded_1_to_many_relationships_in_same_table_has_same_1_side_for_more_than_1_relationship(graph, table_list, relationship_node, side_1_entity, side_many_entity):
    for unique_name in table_list:
        node = graph.get_node_by_name(unique_name)
        if node.is_relationship() and check_if_relationship_is_1_N(node):
            if node.rel_dict['entity1']['one']:
                side_1_node = node.entity1
                side_many_node = node.entity2
            else:
                side_1_node = node.entity2
                side_many_node = node.entity1
            if side_1_node == side_1_entity and side_many_node == side_many_entity:
                return True
    return False

def define_node_keys_for_subclass(node):
    parent_entity = node.parent_entity

    if node.mapped_table == parent_entity.mapped_table:
        top_parent_in_table = get_top_class_in_table(node.mapped_table, parent_entity)
        is_parent_in_table = True
        immediate_parent_in_a_different_table = None
    else:
        top_parent_in_table = None
        is_parent_in_table = False
        immediate_parent_in_a_different_table = get_the_immediate_parent_if_exists_in_a_table(parent_entity)

    pk = []
    fk = []
    fk_table = []
    fk_node_unique_name = []
    pk_entity = [node.unique_name]

    if top_parent_in_table is not None:
        pk = [(key, get_attribute_type(type), key_unique_name, node.unique_name.lower() + "_id")
              for key, type, key_unique_name, __ in top_parent_in_table.key.table_key ]#when top parent in table - e.g. Person and Student in same table - for Student - key is person_id and ERkey is student_id
        fk = top_parent_in_table.key.table_key
        fk_table = [top_parent_in_table.mapped_table[1]]
        fk_node_unique_name = [top_parent_in_table.unique_name]

    elif immediate_parent_in_a_different_table is not None:
        pk =  [(node.unique_name.lower() + "_id", "INTEGER", node.unique_name.lower() + "_id", node.unique_name.lower() + "_id")]#(key, key_type, key_unique_name, ER_key_name)
        fk = immediate_parent_in_a_different_table.key.table_key
        fk_table = [immediate_parent_in_a_different_table.mapped_table[1]]
        fk_node_unique_name = [immediate_parent_in_a_different_table.unique_name]

    else:#no parent exists
        pk =  [(node.unique_name.lower() + "_id", "INTEGER", node.unique_name.lower() + "_id", node.unique_name.lower() + "_id")]
        fk = None
        fk_table = None
        fk_node_unique_name = None

    node.is_parent_in_table=is_parent_in_table
    node.is_immediate_parent_in_a_different_table = True if immediate_parent_in_a_different_table is not None else False

    #node.is_contained_in_parent = node.is_parent_in_table #- no need to set is_contained_in_parent - this should be set by search algorithm - is_contained_in_parent and is_parent_in_table gives same info
    #node.is_partially_by_itself = not node.is_immediate_parent_in_a_different_table#for now let's say both same - but it is not - this should be set by search algorithm - todo
    #node.is_all_by_itself = not node.is_partially_by_itself#for now let's say both same - but it is not - this should be set by search algorithm - todo

    #todo - connected graph doesn't capture concrete table+parent table present case -> the representation gets mapped to partially by itself
    #partial -> [person], [student], [instructor]
    #all by itself - concrete table(no parent) -> [student], [instructor]
    #all by itself + parent -> this mapped to same partial representation

    return Key(pk, fk, fk_table, fk_node_unique_name, pk_entity)


#weak entity can have a strong entity parent or a weak entity parent as well
def define_node_keys_for_weak_entity(node):
    parent_entity = node.parent_entity
    is_parent_in_table = False
    pk = [[],[]]#to uniquely identify attributes came from strong entity - pk[0] - strong entity and pk[1] discriminator attributes from weak entity
    fk = [[],[]]#fk[1] will be empty since it is just added for completion
    fk_table = []
    fk_node_unique_name = []
    pk_entity = [[parent_entity.unique_name], [node.unique_name]]
    if node.mapped_table == parent_entity.mapped_table:
        is_parent_in_table = True
    else:
        is_parent_in_table = False
    if parent_entity.is_weak_entity:
        assert len(parent_entity.key.table_key)==2
        for key_set in parent_entity.key.table_key:
            for key, type, key_unique_name, ER_key_name in key_set:
                pk[0].extend([(key, get_attribute_type(type), key_unique_name, ER_key_name)])
                fk[0].extend([(key, get_attribute_type(type), key_unique_name)])
    else:
        pk[0].extend([(key, get_attribute_type(type), key_unique_name, ER_key_name) for key, type, key_unique_name, ER_key_name in parent_entity.key.table_key])
        fk[0].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in parent_entity.key.table_key])
    fk_table.append(parent_entity.mapped_table[1])#only parent entity mapped table is the fk_table
    fk_node_unique_name.append(parent_entity.unique_name)

    for attribute in node.attributes:
        if attribute.is_discriminator:
            unique_name = attribute.unique_name
            type = attribute.attr_type
            attribute_name = unique_name.split('.', 1)[-1].replace('.', '__')
            pk[1].append((attribute_name, get_attribute_type(type), attribute.unique_name, attribute_name))#pk list consists of owner entity pk + discriminator attributes

    node.is_parent_in_table=is_parent_in_table

    node.is_contained_in_parent = node.is_parent_in_table

    return Key(pk, fk, fk_table, fk_node_unique_name, pk_entity)

#for relationship key -> (key, type, key_unique_name, relevant_entity) -
# includes correponding participating entity - e.g. [Person,Student,Instructor], [Advisor] - pk  for Advisor [(person_id, integer, person_id, student)]
def define_node_keys_for_relationship(graph, node, table_mapping):
    pk = [[], []]
    fk = [[], []]
    fk_table = []#2 entries from each participating entity's mapped table
    fk_node_unique_name = []#just store an empty list - this is not defined for relationships for now
    pk_entity = [[], []]
    entity1 = node.entity1
    entity2 = node.entity2
    role_name = ""
    #identifier if multipe 1_to_many in same table and has same entity as 1_side
    identifier_1_to_many = ""# e.g. order_items between CustOrder(one total) and ProductVariant(many total), order_returns between CustOrder(one total) and ProductVariant(many total) - folded in same table",
    if entity1 == entity2:#recursive relationship
        role1, role2 = node.recursive_relationship_roles
        role_name += role2[:-3]+"_" #e.g. prereq - of the 2 entities, role_name is added to second entity - entity1 or entity2 can be second entity - depends on key order
                    #If relationship is M:1 and entity1 is M, role_name added to entity2, elif entity2 is M, it is added to entity1
                    #If relationship is M:N, role_name added to entity2
    if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:#1:M - for this only pk[0] is primary key

        #first check if multiple 1 to many folded in same table where all share same M side and same 1 side - but different relationships
        node_list_mapped_to_table = table_mapping.get(node.mapped_table[1])
        if check_if_folded_1_to_many_relationships_in_same_table_has_same_1_side_for_more_than_1_relationship(graph, node_list_mapped_to_table, node, entity1, entity2):
            identifier_1_to_many += node.unique_name + "_"

        entity2_flattened = [tup for item in entity2.key.table_key for tup in (item if isinstance(item, list) else [item])]
        if node.mapped_table != entity2.mapped_table:
            pk[0].extend([(ER_key_name, get_attribute_type(type), key_unique_name, ER_key_name) for key, type, key_unique_name, ER_key_name in entity2_flattened])
            fk[0].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity2_flattened])
            fk_table.append(entity2.mapped_table[1])
        else:
            pk[0].extend([(key, get_attribute_type(type), key_unique_name, ER_key_name) for key, type, key_unique_name, ER_key_name in entity2_flattened])
            fk[0].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity2_flattened])
            fk_table.append(entity2.mapped_table[1])

        entity1_flattened = [tup for item in entity1.key.table_key for tup in (item if isinstance(item, list) else [item])]#this is needed to get attribute completion for relationship - not for pk
        if node.mapped_table != entity1.mapped_table:
            pk[1].extend([(role_name+identifier_1_to_many+ER_key_name, get_attribute_type(type), key_unique_name, role_name+identifier_1_to_many+ER_key_name)
                          for key, type, key_unique_name, ER_key_name in entity1_flattened])
            fk[1].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity1_flattened])
            fk_table.append(entity1.mapped_table[1])
        else:
            pk[1].extend([(role_name+identifier_1_to_many+key, get_attribute_type(type), key_unique_name, role_name+identifier_1_to_many+ER_key_name)
                          for key, type, key_unique_name, ER_key_name in entity1_flattened])
            fk[1].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity1_flattened])
            fk_table.append(entity1.mapped_table[1])

        pk_entity = [[entity2.unique_name], [entity1.unique_name]]

    elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:#M:1 for this only pk[0] is primary key

        #first check if multiple 1 to many folded in same table where all share same M side and same 1 side - but different relationships
        node_list_mapped_to_table = table_mapping.get(node.mapped_table[1])
        if check_if_folded_1_to_many_relationships_in_same_table_has_same_1_side_for_more_than_1_relationship(graph, node_list_mapped_to_table, node, entity2, entity1):
            identifier_1_to_many += node.unique_name + "_"

        entity1_flattened = [tup for item in entity1.key.table_key for tup in (item if isinstance(item, list) else [item])]
        if node.mapped_table != entity1.mapped_table:
            pk[0].extend([(ER_key_name, get_attribute_type(type), key_unique_name, ER_key_name) for key, type, key_unique_name, ER_key_name in entity1_flattened])
            fk[0].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity1_flattened])
            fk_table.append(entity1.mapped_table[1])
        else:
            pk[0].extend([(key, get_attribute_type(type), key_unique_name, ER_key_name) for key, type, key_unique_name, ER_key_name in entity1_flattened])
            fk[0].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity1_flattened])
            fk_table.append(entity1.mapped_table[1])

        entity2_flattened = [tup for item in entity2.key.table_key for tup in (item if isinstance(item, list) else [item])]#this is needed to get attribute completion for relationship - not for pk
        if node.mapped_table != entity2.mapped_table:
            pk[1].extend([(role_name+identifier_1_to_many+ER_key_name, get_attribute_type(type), key_unique_name, role_name+identifier_1_to_many+ER_key_name)
                          for key, type, key_unique_name, ER_key_name in entity2_flattened])
            fk[1].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity2_flattened])
            fk_table.append(entity2.mapped_table[1])
        else:
            pk[1].extend([(role_name+identifier_1_to_many+key, get_attribute_type(type), key_unique_name, role_name+identifier_1_to_many+ER_key_name)
                          for key, type, key_unique_name, ER_key_name in entity2_flattened])
            fk[1].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity2_flattened])
            fk_table.append(entity2.mapped_table[1])

        pk_entity = [[entity1.unique_name], [entity2.unique_name]]

    elif not node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:#M:N for this both pk[0], pk[1] combination together is the primary key
        entity1_flattened = [tup for item in entity1.key.table_key for tup in (item if isinstance(item, list) else [item])]
        if node.mapped_table != entity1.mapped_table:
            pk[0].extend([(ER_key_name, get_attribute_type(type), key_unique_name, ER_key_name) for key, type, key_unique_name, ER_key_name in entity1_flattened])
            fk[0].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity1_flattened])
            fk_table.append(entity1.mapped_table[1])
        else:
            pk[0].extend([(key, get_attribute_type(type), key_unique_name, ER_key_name) for key, type, key_unique_name, ER_key_name in entity1_flattened])
            fk[0].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity1_flattened])
            fk_table.append(entity1.mapped_table[1])
        entity2_flattened = [tup for item in entity2.key.table_key for tup in (item if isinstance(item, list) else [item])]#this is needed to get attribute completion for relationship - not for pk
        if node.mapped_table != entity2.mapped_table:
            pk[1].extend([(role_name+ER_key_name, get_attribute_type(type), key_unique_name, role_name+ER_key_name) for key, type, key_unique_name, ER_key_name in entity2_flattened])
            fk[1].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity2_flattened])
            fk_table.append(entity2.mapped_table[1])
        else:
            pk[1].extend([(role_name+key, get_attribute_type(type), key_unique_name, role_name+ER_key_name) for key, type, key_unique_name, ER_key_name in entity2_flattened])
            fk[1].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity2_flattened])
            fk_table.append(entity2.mapped_table[1])

        pk_entity = [[entity1.unique_name], [entity2.unique_name]]

    return Key(pk, fk, fk_table, fk_node_unique_name, pk_entity)


def define_node_keys_for_mvd_relationship(node):#when mvd in separate table
    pk = [[],[]]#pk from entity and mvd attrtibute - if discriminator attribute(mvd attribute is not defined in er schema), then only pk from entity will be the key - 1:1 - 1 pk will have single mvd
    fk = [[],[]]##fk[1] will be empty - it is just added for completion when serializing the graph
    fk_table = []
    fk_node_unique_name = []
    entity = node.entity
    entity_flattened = [tup for item in entity.key.table_key for tup in (item if isinstance(item, list) else [item])]
    pk[0].extend([(key, get_attribute_type(type), key_unique_name, ER_key_name) for key, type, key_unique_name, ER_key_name in entity_flattened])
    fk[0].extend([(key, get_attribute_type(type), key_unique_name) for key, type, key_unique_name, __ in entity_flattened])
    fk_table.append(entity.mapped_table[1] if entity.mapped_table else None)
    fk_node_unique_name.append(entity.unique_name)

    attribute_name = node.unique_name.split('.', 1)[-1].replace('.', '__')
    attr_type = node.attr_type
    pk[1].extend([(attribute_name, get_attribute_type(attr_type), node.unique_name, attribute_name)])#mvd

    return Key(pk, fk, fk_table, fk_node_unique_name)

def initialize_node_keys(graph, node, table_mapping):

    if node.is_entity() and not node.is_subclass and not node.is_weak_entity:#regular entity
        key = Key([(node.unique_name.lower() + "_id", "INTEGER", node.unique_name.lower() + "_id", node.unique_name.lower() + "_id")],
                  None,
                  None, None, [node.unique_name])
        node.key = key
    elif node.is_entity() and node.is_subclass:
        key = define_node_keys_for_subclass(node)
        node.key = key
    elif node.is_entity() and node.is_weak_entity:
        key = define_node_keys_for_weak_entity(node)
        node.key = key
    elif node.is_relationship():
        key = define_node_keys_for_relationship(graph, node, table_mapping)
        node.key = key
    elif node.is_attribute() and node.is_multivalued:
        key = define_node_keys_for_mvd_relationship(node)
        node.key = key

def initialize_keys(graph: Graph, table_mapping: Dict[str, str]):
    for node in graph.nodes:
        if not node.is_attribute():
            #node.mapped_table = table_mapping.get(node.unique_name) - already set by executing search phase
            initialize_node_keys(graph, node, table_mapping)
        elif node.is_attribute() and node.is_multivalued:
            #node.mapped_table = table_mapping.get(node.unique_name)
            initialize_node_keys(graph, node, table_mapping)

def add_attributes_to_table(graph:Graph, node:Node, table_attributes, created_types_names:set(), created_types:dict, is_child_all_by_itself=None):
    #add attributes
    for attribute in node.attributes:
        if not attribute.is_primary_key and not attribute.is_discriminator:
            attribute_name = attribute.unique_name.split('.', 1)[-1].replace('.', '__')
            attr_type = get_attribute_type(attribute.attr_type)
            if attribute.is_composite:#assume - 1 level of composite
                if attribute.is_flattened:
                    for subattribute in attribute.children:
                        subattribute_name = subattribute.unique_name.split('.', 1)[-1].replace('.', '__')
                        subattribute_type = get_attribute_type(subattribute.attr_type)
                        table_attributes.append((subattribute_name, subattribute_type, subattribute.unique_name, node.unique_name))
                else:
                    type_name = create_composite_type(graph, attribute, created_types_names, created_types)
                    table_attributes.append((attribute_name, type_name, attribute.unique_name, node.unique_name))
            elif attribute.is_multivalued:#todo - need to do when an attribute is an array of composite type - both mvd and composite
                if node.mapped_table is not None:
                    if node.mapped_table==attribute.mapped_table:#store mvd as array attribute
                        attribute_name = attribute.unique_name.split('.', 1)[-1].replace('.', '__')
                        attr_type = get_attribute_type(attribute.attr_type)
                        table_attributes.append((attribute_name, attr_type+"[]", attribute.unique_name, node.unique_name))
            else:
               table_attributes.append((attribute_name, attr_type, attribute.unique_name, node.unique_name))


def add_parent_attributes_to_table(graph:Graph, node:Node, table_attributes, created_types_names:set(), created_types:dict, is_child_all_by_itself:bool):
    if node.parent_entity is not None:
        add_parent_attributes_to_table(graph, node.parent_entity, table_attributes, created_types_names, created_types, is_child_all_by_itself)

    return add_attributes_to_table(graph, node, table_attributes, created_types_names, created_types, is_child_all_by_itself)

def check_if_relationship_is_1_N(node):
    if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:
        return True
    elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:
        return True
    else:
        return False

#sort the tables from the least to the most dependent
#todo - since pk/fk constraints are not set for tables(since non-leaf all by itself cannot maintain pk-fk constraints when distributed in many tables) sorting
# the tables in the order of dependencies is not required. Also because of no pk-fk constraints set on table, a no_table node in hierarchy can have mvds to be in separate tables
def sort_dependencies(table_dependencies):
    sorted_tables = []
    """
    in_degree = {key:0 for key in table_dependencies}
    adj_list = {key:[] for key in table_dependencies}

    for key, dependencies in table_dependencies.items():
        for dep in dependencies:
            adj_list[dep].append(key)
            in_degree[key]+=1

    sorted_tables = []
    queue = deque([key for key in in_degree if in_degree[key]==0])
    while queue:
        key = queue.popleft()
        sorted_tables.append(key)
        for neighbor in adj_list[key]:
            in_degree[neighbor] -=1
            if in_degree[neighbor]==0:
                queue.append(neighbor)

    #assert len(sorted_tables)==len(table_dependencies) todo - need to fix dependencies - since with all by itself option, pk/fk constraints ignored - can insert to tables without sorting dpendencies
    """
    return sorted_tables


def create_table_statements(graph: Graph, table_mapping: Dict[str, List[str]]):
    tables_to_be_created = []
    created_types_names = set()
    created_types = {}

    initialize_keys(graph, table_mapping)

    schemas_without_foreign_key_statements = []#add - table name, [(attribute name, type),...], primary_key_stmts
    all_foreign_key_statements = []

    table_dependencies = {}#need for inserts to be done in order when pk/fk constraints are enforced

    for i, (table_name, table_list) in enumerate(table_mapping.items()):
        table = table_name
        table_attributes = []#add [(attribute_name, attr_type, attribute.unique_name), (), (),...]
        is_entity_in_table = False
        is_relationship_in_table = False
        primary_keys = [] # [{pk_name:ER_name}, {},...]
        foreign_keys = []
        table_dependencies[table_name]= set()#dependent tables for each table - use set to avoid adding duplicate dependencies - tables on which table is dependent on

        table_list_copy = table_list.copy()
        for n in table_list_copy:
            x = graph.get_node_by_name(n)
            assert x

        for unique_name in table_list:
            node = graph.get_node_by_name(unique_name)
            if node.is_entity() and not node.is_subclass and not node.is_weak_entity:#Regular Entity
                is_entity_in_table = True
                for key, type, key_unique_name, ER_key_name in node.key.table_key:
                    if key not in primary_keys:
                        table_attributes.append((key, type, key_unique_name, node.unique_name))#(attr, type, attr_unique_name, attr_entity_relationship_node.unique_name)
                        primary_keys.append(key)

                #add attributes
                add_attributes_to_table(graph, node, table_attributes, created_types_names, created_types)

            #sub class
            elif node.is_entity() and node.is_subclass and not node.is_weak_entity:
                is_entity_in_table = True
                for i in range(len(node.key.table_key)):
                    if node.key.table_key[i][0] not in primary_keys:
                        table_attributes.append((node.key.table_key[i][0], node.key.table_key[i][1], node.key.table_key[i][2], node.unique_name))
                        primary_keys.append(node.key.table_key[i][0])
                    if node.key.reference_key is not None:#need to add only if a parent exists in the other tables(the existing immediate parent)
                        if table != node.key.reference_table[i]:
                            table_dependencies[table_name].add(node.key.reference_table[i])
                            if node.key.reference_key[i] is not None:
                                if node.key.table_key[i][0] not in foreign_keys:
                                    all_foreign_key_statements.append(
                                        f"ALTER TABLE {table} ADD FOREIGN KEY ({node.key.table_key[i][0]}) REFERENCES "
                                        f"{node.key.reference_table[i]}({node.key.reference_key[i][0]})")
                                    foreign_keys.append(node.key.table_key[i][0])

                if not node.is_contained_in_parent:
                    if node.is_contained_all_descendants or node.is_all_by_itself:#need to add all attributes from all parents in hierarchy - parent table may/may not exist - checking if immediate parent exists in a different table doesn't capture this
                        add_parent_attributes_to_table(graph, node.parent_entity, table_attributes, created_types_names, created_types,
                                                       node.is_contained_all_descendants or node.is_all_by_itself)#order of adding attributes matter - that's why parent attributes are added before own

                #add attributes
                add_attributes_to_table(graph, node, table_attributes, created_types_names, created_types)

                if node.is_parent_in_table:
                    if not any(name == "role" for name, __, __, __ in table_attributes):
                        table_attributes.append(("role", "VARCHAR(255)", "role", node.unique_name))

            elif node.is_entity() and not node.is_subclass and node.is_weak_entity:
                is_entity_in_table = True
                if node.is_parent_in_table:#store weak entity as array
                    node_name = node.unique_name.split('.', 1)[-1].replace('.', '__')
                    table_attributes.append((node_name, "JSONB DEFAULT '[]'::jsonb", node.unique_name, node.unique_name))
                else:#add attributes for - depending entity, weak entity discriminator attribute, weak entity other attributes
                    #strong entity - this depending entity can be a weak entity too
                    for i in range(len(node.key.table_key[0])):
                        if node.key.table_key[0][i][0] not in primary_keys:
                            table_attributes.append((node.key.table_key[0][i][0], node.key.table_key[0][i][1], node.key.table_key[0][i][2], node.unique_name))
                            primary_keys.append(node.key.table_key[0][i][0])
                        #if table != node.key.reference_table[0][0]:
                        #    if node.key.table_key[0][i][0] not in foreign_keys:
                        #        all_foreign_key_statements.append(
                        #            f"ALTER TABLE {table} ADD FOREIGN KEY ({node.key.table_key[0][i][0]}) REFERENCES "
                        #            f"{node.key.reference_table[0]}({node.key.reference_key[0][i][0]})")
                        #        foreign_keys.append(node.key.table_key[0][i][0])
                    assert table != node.key.reference_table[0]
                    if table != node.key.reference_table[0]:
                        table_dependencies[table_name].add(node.key.reference_table[0])
                        entity_foreign_keys_for_pks = []
                        entity_foreign_keys_for_pks.extend(node.key.reference_key[0][j][0] for j in range(len(node.key.reference_key[0])))
                        if all(primary_key not in foreign_keys for primary_key in primary_keys):
                            all_foreign_key_statements.append(
                                f"ALTER TABLE {table} ADD FOREIGN KEY ({", ".join(primary_keys)}) REFERENCES "
                                f"{node.key.reference_table[0]}({", ".join(entity_foreign_keys_for_pks)})")
                            foreign_keys.extend(primary_keys)
                    if len(node.parent_entity.node_cover)>1:
                        for node_name in node.parent_entity.node_cover:
                            node_cover_node = graph.get_node_by_name(node_name)
                            table_dependencies[table_name].add(node_cover_node.mapped_table[1])#add dependencies when parent entity is distributed across many tables
                    #weak entity - discriminator attributes
                    for i in range(len(node.key.table_key[1])):
                        if node.key.table_key[1][i][0] not in primary_keys:
                            table_attributes.append((node.key.table_key[1][i][0], node.key.table_key[1][i][1], node.key.table_key[1][i][2], node.unique_name))
                            primary_keys.append(node.key.table_key[1][i][0])

                    #add attributes
                    add_attributes_to_table(graph, node, table_attributes, created_types_names, created_types)

            elif node.is_relationship():
                is_relationship_in_table = True
                if not node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:#M:N
                    for i in range(len(node.key.table_key)):#i=0,1 - for 2 participating entities
                        for j in range(len(node.key.table_key[i])):
                            if node.key.table_key[i][j][0] not in primary_keys:
                                table_attributes.append((node.key.table_key[i][j][0], node.key.table_key[i][j][1], node.key.table_key[i][j][2], node.unique_name))
                                primary_keys.append(node.key.table_key[i][j][0])
                        if table != node.key.reference_table[i]:#add foreign keys
                            table_dependencies[table_name].add(node.key.reference_table[i])
                            entity_pks = []
                            entity_pks.extend(node.key.table_key[i][j][0] for j in range(len(node.key.table_key[i])))
                            entity_foreign_keys_for_pks = []
                            entity_foreign_keys_for_pks.extend(node.key.reference_key[i][j][0] for j in range(len(node.key.reference_key[i])))
                            if entity_pks not in foreign_keys:
                                all_foreign_key_statements.append(
                                    f"ALTER TABLE {table} ADD FOREIGN KEY ({", ".join(entity_pks)}) REFERENCES "
                                    f"{node.key.reference_table[i]}({", ".join(entity_foreign_keys_for_pks)})")
                                foreign_keys.append(entity_pks)


                    #add attributes
                    #add_attributes_to_table(graph, node, table_attributes, created_types_names, created_types)
                else:
                    many_side_node = node.entity1 if not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one'] else node.entity2
                    #no need to add pk to table for relationship when it is folded, since pk is already added from entity itself
                    #need to explicitly add the pk only when relationship is in separate table
                    if graph.config[node.unique_name] != "folded_to_many_side":
                        for i in range(len(node.key.table_key[0])):#only add N side keys as pk keys
                            if node.key.table_key[0][i][0] not in primary_keys:
                                table_attributes.append((node.key.table_key[0][i][0], node.key.table_key[0][i][1], node.key.table_key[0][i][2], node.unique_name))
                                primary_keys.append(node.key.table_key[0][i][0])

                    for i in range(len(node.key.table_key[1])):#add attributes from 1 side as attributes for relationship
                        if node.key.table_key[1][i][0] not in primary_keys:
                            table_attributes.append((node.key.table_key[1][i][0], node.key.table_key[1][i][1], node.key.table_key[1][i][2], node.unique_name))

                    #add foreign keys - for each participating entity if many-to-1 relationship in a separate table
                    if graph.config[node.unique_name] != "folded_to_many_side":
                        for i in range(len(node.key.table_key)):#add foreign keys - for each participating entity
                            if table != node.key.reference_table[i]:#add foreign keys
                                table_dependencies[table_name].add(node.key.reference_table[i])
                                entity_pks = []
                                entity_pks.extend(node.key.table_key[i][j][0] for j in range(len(node.key.table_key[i])))
                                entity_foreign_keys_for_pks = []
                                entity_foreign_keys_for_pks.extend(node.key.reference_key[i][j][0] for j in range(len(node.key.reference_key[i])))
                                if entity_pks not in foreign_keys:
                                    all_foreign_key_statements.append(
                                        f"ALTER TABLE {table} ADD FOREIGN KEY ({", ".join(entity_pks)}) REFERENCES "
                                        f"{node.key.reference_table[i]}({", ".join(entity_foreign_keys_for_pks)})")
                                    foreign_keys.append(entity_pks)
                    else:#add foreign keys for one side only when relationship is folded in many side - since foreign key constraints for many side will be already added from many side entity
                        if table != node.key.reference_table[1]:#add foreign keys
                            table_dependencies[table_name].add(node.key.reference_table[1])
                            entity_pks = []
                            entity_pks.extend(node.key.table_key[1][j][0] for j in range(len(node.key.table_key[1])))
                            entity_foreign_keys_for_pks = []
                            entity_foreign_keys_for_pks.extend(node.key.reference_key[1][j][0] for j in range(len(node.key.reference_key[1])))
                            if entity_pks not in foreign_keys:
                                all_foreign_key_statements.append(
                                    f"ALTER TABLE {table} ADD FOREIGN KEY ({", ".join(entity_pks)}) REFERENCES "
                                    f"{node.key.reference_table[1]}({", ".join(entity_foreign_keys_for_pks)})")
                                foreign_keys.append(entity_pks)


                    #add attributes
                    #add_attributes_to_table(graph, node, table_attributes, created_types_names, created_types)

                #handle when participating entities of relationships are subclasses and when all with a parent class in a single table - e.g. [Person, Student, Instructor, advisor] in a single table
                entity1 = node.entity1
                entity2 = node.entity2
                if entity1.is_subclass and entity2.is_subclass:
                    if entity1.mapped_table == node.mapped_table and entity2.mapped_table == node.mapped_table:
                        if entity1.is_parent_in_table and entity2.is_parent_in_table:
                            if entity1.key.table_key[0][0] == entity2.key.table_key[0][0]:#same pk - which means subclasses from same hierarchy - this doesn't have to be that both have same immediate parent
                                assert check_if_relationship_is_1_N(node)#for this to happen - relationship has to be not M:N
                                one_side_key = list(node.key.table_key[1][0])
                                one_side_key[0] = node.name.lower()+"_id"#update key name
                                one_side_key[2] = node.name.lower()+"_id"#update unique name
                                updated_1_side_key = tuple(one_side_key)
                                node.key.table_key[1] = [updated_1_side_key]
                                table_attributes.append((node.name.lower()+"_id", "INTEGER", node.name.lower()+"_id", node.unique_name))
                                if node.name.lower()+"_id" not in foreign_keys:
                                    all_foreign_key_statements.append(
                                        f"ALTER TABLE {table} ADD FOREIGN KEY ({node.name.lower()+"_id"}) REFERENCES "
                                        f"{entity1.key.reference_table[0]}({entity1.key.table_key[0][0]})")
                                    foreign_keys.append(node.name.lower()+"_id")


                #add attributes
                add_attributes_to_table(graph, node, table_attributes, created_types_names, created_types)

                if len(node.entity1.node_cover)>1 or len(node.entity2.node_cover)>1:
                    if len(node.entity1.node_cover)>1:
                        for node_name in node.entity1.node_cover:
                            node_cover_node = graph.get_node_by_name(node_name)
                            table_dependencies[table_name].add(node_cover_node.mapped_table[1])#add dependencies when parent entity is distributed across many tables
                    if len(node.entity2.node_cover)>1:
                        for node_name in node.entity2.node_cover:
                            node_cover_node = graph.get_node_by_name(node_name)
                            table_dependencies[table_name].add(node_cover_node.mapped_table[1])#add dependencies when parent entity is distributed across many tables


            elif node.is_attribute() and node.is_multivalued:
                if node.is_in_separate_table:#this has set by search algorithm
                    #if node.mapped_table is not None and node.entity.mapped_table is not None:#parent entity has to exist in a table
                    #since pk/fk constraints are not checked with all_by_itself option for hierarchy nodes - relaxed the above constraint to parent entity to be no_table and mvd
                    #still be in separate table
                    if node.mapped_table is not None:
                        if len(table_list)==1:#mvd as a separate table - this check is not required since it is covered by node.is_in_separate_table
                            for i in range(len(node.key.table_key[0])):#except mvd
                                if node.key.table_key[0][i][0] not in primary_keys:
                                    table_attributes.append((node.key.table_key[0][i][0], node.key.table_key[0][i][1], node.key.table_key[0][i][2], node.unique_name))
                                    primary_keys.append(node.key.table_key[0][i][0])

                            if table != node.key.reference_table[0]:#add foreign keys for pk - if pk is a list of keys(entity's pk is a list - e.g. storing weak entity's mvd in a separate table) - all keys need to be added together in foreign key statement
                                table_dependencies[table_name].add(node.key.reference_table[0])
                                entity_pks = []
                                entity_pks.extend(node.key.table_key[0][i][0] for i in range(len(node.key.table_key[0])))
                                entity_foreign_keys_for_pks = []
                                entity_foreign_keys_for_pks.extend(node.key.reference_key[0][i][0] for i in range(len(node.key.reference_key[0])))
                                if entity_pks not in foreign_keys:
                                    all_foreign_key_statements.append(
                                        f"ALTER TABLE {table} ADD FOREIGN KEY ({", ".join(entity_pks)}) REFERENCES "
                                        f"{node.key.reference_table[0]}({", ".join(entity_foreign_keys_for_pks)})")
                                    foreign_keys.append(entity_pks)

                            #add mvd to primary key
                            if node.key.table_key[1][0] not in primary_keys:
                                table_attributes.append((node.key.table_key[1][0][0], node.key.table_key[1][0][1], node.key.table_key[1][0][2], node.unique_name))
                                primary_keys.append(node.key.table_key[1][0][0])

                            #add attributes
                            add_attributes_to_table(graph, node, table_attributes, created_types_names, created_types)

                else:
                    #attribute already added as array
                    pass

        primary_key_stmt = f"PRIMARY KEY ({', '.join(primary_keys)})" if primary_keys else ""

        if len(table_attributes)>0:
            is_both_entity_relationship_in_table = is_entity_in_table and is_relationship_in_table#folded table - needed to combine inserts from entity and relationship
            schemas_without_foreign_key_statements.append((table, table_attributes, is_both_entity_relationship_in_table, primary_keys,
                                                           primary_key_stmt))
    sorted_table_dependencies = sort_dependencies(table_dependencies)#sort the tables in the order of the least dependent table to the most dependent table
                                                #this sorting is required since inserting into tables should happen first into the least dependent tables

    return schemas_without_foreign_key_statements, all_foreign_key_statements, created_types, sorted_table_dependencies

def generate_table_mappings(graph):
    table_mappings = {}
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship() or (node.is_attribute() and node.is_multivalued):
            if node.mapped_table or node.mapped_tables_list:
                if node.mapped_table:
                    table = node.mapped_table[1]
                    if table_mappings.get(table) is not None:
                        if node.unique_name not in table_mappings[table]:
                            table_mappings[table].append(node.unique_name)
                    else:
                        table_mappings[table] = []
                        table_mappings[table].append(node.unique_name)
                if node.mapped_tables_list:
                    assert len(node.mapped_tables_list) > 0#distributed across multiple tables - for folded 1:N relationship or folded weak entity with hierarchical participating entity having len(node_cover) > 1
                    for mapped_table in node.mapped_tables_list:
                        table = mapped_table[1]
                        if table_mappings.get(table) is not None:
                            if node.unique_name not in table_mappings[table]:
                                table_mappings[table].append(node.unique_name)
                        else:
                            table_mappings[table] = []
                            table_mappings[table].append(node.unique_name)
    return table_mappings










