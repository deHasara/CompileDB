#for strong entity(which doesn't belong to a hierarchy) - its pk + its own attributes
#for strong subclass - its pk + all attributes inherited from parent/s in hierarchy + its own attributes
#for relationship - select * attributes include all atttributes from node itself and two participating entites
#for weak entity - it is all attributes from parent + node itself - if parent is also a weak entity, need to get all attributes until a strong parent found


#node_tables account for insert cost, select_all_tables account for select * cost

#for a hierarchy node, "contained_all_descendants" option makes sure its mapped table contain all relevant tuples - own tuples and its all descendants' tuples - only that option
#cause duplication of tuple attributes
#any other option - ABI, PBI, CIP - makes sure only pk of the tuple will be duplicated

#if node is not contained_all_descendants or a leaf node with all by itself, node.mapped_table may not fully represent all tuples from node
#need to define the node_cover to union all relevant tuples distributed in child mapped_tables
#node_cover for a node will contain node itself(to consider tuples coming from itself - which are in its mapped_table) and minimum children required to cover node

#mapped_tables_list defined for weak entities/1:N folded relationships with participating entity with len(node_cover)>1 - which means node itself is not sufficient
#need to get union across all mapped tables(in mapped_tables_list) to create full weak entity/1:N folded relationship

#for a folded relationship/weak entity distributed across many tables, a single tuple is inserted into one and only one table of all distributed tables where
#matching id found for join

#for a folded weak entity or 1:N relationship - mapped_table is the mapped_table of entity in which weak_entity/relationship is folded
#If entity's node_cover size is > 1, mapped_table itself doesn't fully represent the weak entity or 1:N relationship
#since it is distributed across many tables defined in mapped_tables_list(including the mapped_table)
#this is handled correctly since inserts to folded weak entity or relationship happen with an update from a temp table generated
#in table mapping - for each table in mapped_tables_list of folded weak entity or relationship node, the node is added to table's mapping nodes
#so when doing the update - temp table created for folded weak entity/1:N relationship is joined with all tables in mapped_tables_list

#if node is partially_by_itself/contained_in_parent, joins may happen to gather ancestor attributes. These joins are relevant to tuples from strictly node itself. If node has children
#with all_by_itself or contained_all_descendants, those tuples contain all attributes, just need to filter relevant attributes for node.
#e.g. node n(partially_by_itself) has parent p1(all_by_itself) and children c1(all_by_itself), c2(all_by_itself) - to gather all tuples of n, n joins with p1 to formulate full tuples
#coming from n, then union with tuples(filtered for attributes of n) coming from c1 and c2

import random
from itertools import product
from math import prod

from partition_rules import check_conditions_for_abstract_table
from cost_model import insert_cost, search_cost, scan_cost, union_all_cost, sort_merge_join_cost, \
    scan_folded_weak_entity, scan_folded_weak_entity_modified, insert_cost_for_workload_queries
from check_config_valid import check_config_is_valid
from construct_create_statements1 import generate_table_mappings, initialize_keys

#for no_table -> node.is_no_table is True
#all_by_itself - for nodes in hierarchy including root(which is not a subclass) - contain only its tuples and any children tuples propagated
#No inserts propagated from contained_all_descendants or all_by_itself node to its parent/s in top of hierarchy

#for strong entity(not belonging to a hierarchy) can be all_by_itself only
#no_table is not possible for strong entity which doesn't belong to hierarchy since child cover can be defined only for an entity from hierarchy
#for strong entity beloning to a hierarchy,
# 1. if root - can be contained_all_descendants, all_by_itself, no_table
# 2. if subclass - can be contained_all_descendants, all_by_itself, partially_by_itself, contained_in_parent, no_table
#if subclass is a leaf, all_by_itself still fully defines the node
"""
partitioning_options = {
    "entity": {1: "all_by_itself", 2: "contained_all_descendants", 3: "no_table"},
    #regular strong entity/root of hierarchy
    "weak_entity": {1: "all_by_itself", 2: "contained_in_parent"},
    "sub_class": {1: "contained_all_descendants", 2: "all_by_itself", 3: "partially_by_itself", 4: "contained_in_parent"},
    "1_N_relationship": {1: "folded_to_many_side", 2: "all_by_itself"},
    "M_N_relationship": {1: "all_by_itself"},
    "composite_attribute": {1: "flattened", 2: "unflattened"},
    "multi_valued_attribute": {1: "all_by_itself", 2: "contained_in_parent"}
}
"""
partitioning_options = {
    "entity": {1: "all_by_itself", 3: "no_table"},
    #regular strong entity/root of hierarchy
    "weak_entity": {1: "all_by_itself", 2: "contained_in_parent"},
    "sub_class": {2: "all_by_itself", 3: "partially_by_itself", 4: "contained_in_parent"},
    "1_N_relationship": {1: "folded_to_many_side", 2: "all_by_itself"},
    "M_N_relationship": {1: "all_by_itself"},
    "composite_attribute": {1: "flattened", 2: "unflattened"},
    "multi_valued_attribute": {1: "all_by_itself", 2: "contained_in_parent"}
}


# Set of options that produce a physical table
materialized_options = {
    "entity": ["all_by_itself", "contained_all_descendants"],
    #regular strong entity(only all_by_itself) or root of hierarchy(can have both options)
    "weak_entity": ["all_by_itself"],
    "sub_class": ["contained_all_descendants", "all_by_itself", "partially_by_itself"],
    "1_N_relationship": ["all_by_itself"],
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["all_by_itself"]
}

#default options for node_type
default_options = {
    "entity": ["all_by_itself"],
    "weak_entity": ["all_by_itself"],
    "sub_class": ["all_by_itself"],  #["contained_in_parent"],
    "1_N_relationship": ["folded_to_many_side"],#folded_to_many_side
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["contained_in_parent"],  #["all_by_itself"]
}

table_cover_for_nodes = {}
node_cost = {}


def heuristic_default_option(node_type_for_partitioning_options):
    if node_type_for_partitioning_options == "entity":
        return default_options.get("entity")[0]
    elif node_type_for_partitioning_options == "weak_entity":
        return default_options.get("weak_entity")[0]
    elif node_type_for_partitioning_options == "sub_class":
        return default_options.get("sub_class")[0]
    elif node_type_for_partitioning_options == "1_N_relationship":
        return default_options.get("1_N_relationship")[0]
    elif node_type_for_partitioning_options == "M_N_relationship":
        return default_options.get("M_N_relationship")[0]
    elif node_type_for_partitioning_options == "multi_valued_attribute":
        return default_options.get("multi_valued_attribute")[0]
    else:
        return


def check_if_relationship_is_1_N(node):
    if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:
        return True
    elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:
        return True
    else:
        return False


def reset_partitioning_options_for_node(graph):
    for node in graph.nodes:
        node.partitioning_options = []


def check_if_entity_participates_in_a_relationship(graph, node):
    for iter_node in graph.nodes:
        if iter_node.is_relationship():
            if iter_node.entity1.unique_name == node.unique_name:
                return True
            elif iter_node.entity2.unique_name == node.unique_name:
                return True
    return False


def check_if_entity_participates_as_a_parent_for_a_weak_entity(graph, node):
    for iter_node in graph.nodes:
        if iter_node.is_entity() and iter_node.is_weak_entity:
            if iter_node.parent_entity.unique_name == node.unique_name:
                return True
    return False


def check_if_a_parent_entity_be_no_table(graph,
                                         node):  #check if parent entity can have option to have no physical table
    #for this to happen parent entity insert frequency should be 0, all immediate children should have total participation, and it shouldn't participate in a relationship, and
    #shouldn't be a parent entity for a weak entity
    if node.insert_frequency == 0:
        if not (check_if_entity_participates_in_a_relationship(graph, node) or
                check_if_entity_participates_as_a_parent_for_a_weak_entity(graph, node)):
            for child in node.children:
                if child.is_total:
                    continue
                else:
                    node.is_option_to_be_abstract = False
                    break
            node.is_option_to_be_abstract = True
        else:
            node.is_option_to_be_abstract = False
    else:
        node.is_option_to_be_abstract = False


def add_abstract_option_for_possible_nodes(graph, node):
    if node.is_entity() and len(
            node.children) != 0:  #check if the node is a parent entity not a regular entity or leaf entity in hierarchy(regular and leaf entity has no children)
        check_if_a_parent_entity_be_no_table(graph, node)
        if node.is_option_to_be_abstract:
            node.partitioning_options.append(partitioning_options['entity'].get(3))


#if there is another weak entity, depends on this weak entity, this weak entity cannot be folded
def check_if_weak_entity_is_parent_to_another_weak_entity(graph, node):
    for _node in graph.nodes:
        if _node.is_entity() and _node.is_weak_entity and _node.parent_entity == node:
            return True
        else:
            continue
    return False


def initialize_partitioning_options_for_node_helper(node, node_type):
    node.partitioning_options.extend(partitioning_options[node_type].values())


def initialize_partitioning_options_for_node(graph):
    for node in graph.nodes:
        add_abstract_option_for_possible_nodes(graph, node)
        if node.is_entity() and not node.is_subclass and not node.is_weak_entity:
            node.node_type_for_partitioning_options = 'entity'
            node.partitioning_options.append(partitioning_options['entity'].get(1))
            #if len(node.children) > 0:  #strong root - at the top of hierarchy - root is not considered a subclass - for an entity to be subclass it has to have atleast one top parent
            #    node.partitioning_options.append(partitioning_options['entity'].get(2))# entity belonging to a hierarchy have option to be contained_all_descendants
        elif node.is_entity() and node.is_subclass:
            node.node_type_for_partitioning_options = 'sub_class'
            initialize_partitioning_options_for_node_helper(node, "sub_class")
        elif node.is_entity() and node.is_weak_entity:
            node.node_type_for_partitioning_options = 'weak_entity'
            initialize_partitioning_options_for_node_helper(node, "weak_entity")
            if (check_if_weak_entity_is_parent_to_another_weak_entity(graph,
                                                                      node) or check_if_entity_participates_in_a_relationship(
                graph, node)):
                #remove the folded option since this weak entity has dependent weak entity or participates in a relationship
                node.partitioning_options.remove(partitioning_options['weak_entity'].get(2))
        elif node.is_relationship():
            if check_if_relationship_is_1_N(node):
                node.node_type_for_partitioning_options = '1_N_relationship'
                initialize_partitioning_options_for_node_helper(node, "1_N_relationship")
            else:
                node.node_type_for_partitioning_options = 'M_N_relationship'
                initialize_partitioning_options_for_node_helper(node, "M_N_relationship")
        elif node.is_attribute() and node.is_multivalued:
            node.node_type_for_partitioning_options = 'multi_valued_attribute'
            initialize_partitioning_options_for_node_helper(node, "multi_valued_attribute")


def reset_table_cover_for_nodes():
    table_cover_for_nodes.clear()
    node_cost.clear()

#node_cover is defined for all hierarchy entity nodes
def reset_node_cover(graph):
    for node in graph.nodes:
        node.node_cover = []


def reset_keys(graph):
    for node in graph.nodes:
        if not node.is_attribute():
            node.key = None
        elif node.is_attribute() and node.is_multivalued:
            node.key = None


#In hierarchy, except for node with contained_all_descendants and leaf-node with all_by_itself, node.mapped_table may not fully cover the node
#If node's node_cover size > 1 - that indicates node is distributed in multiple nodes and node.mapped_table doesn't fully cover the node
#mapped_tables_list is initialized for folded weak entities/1:M relationships with parent entity/many side entity having len(entity.node_cover) > 1
#mapped_tables_list for such folded weak_entity/relationship define the tables list in which it is distributed
def reset_mapped_table_for_nodes(graph):
    for node in graph.nodes:
        node.mapped_table = None
        node.mapped_tables_list = []


def reset_node_tables(graph):
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            node.node_tables = set()


def reset_node_options(graph):
    for node in graph.nodes:
        if node.is_entity():
            node.is_no_table = False
            node.is_contained_in_parent = False
            node.is_partially_by_itself = False
            node.is_all_by_itself = False
            node.is_contained_all_descendants = False
            node.immediate_parent_with_all_by_itself_unique_name = None
        elif node.is_attribute():
            node.is_in_separate_table = False


#node_tables are initialized for the purpose of inserts
def get_all_relevant_mvd_tables_for_node_in_hierarchy(graph, node, mvd_tables_set):
    if node.parent_entity:
        for attribute in node.parent_entity.attributes:
            if attribute.is_multivalued and attribute.is_in_separate_table:
                mvd_tables_set.add(attribute.mapped_table)
        return get_all_relevant_mvd_tables_for_node_in_hierarchy(graph, node.parent_entity, mvd_tables_set)


#initializing node_tables - which requires for mapping inserts to nodes
#for a tuple in entity, the tuple is inserted into all node_tables defined for entity
#e.g. if immediate parent is all_by_itself and a child is partially_by_itself, there should an entry into parent for each entry tuple into child
#hence child's node_tables include parent's mapped table/s for this example
def figure_out_mappings(graph, config):
    for node in graph.nodes:  #node_tables -> {(sort_key, mapped_table), .....}
        if node.is_entity():
            node.node_tables = set()  #avoid duplicates
            if node.mapped_table:
                node.node_tables.add(node.mapped_table)

            for attribute in node.attributes:
                if attribute.is_multivalued and attribute.is_in_separate_table:#own mvd tables
                    node.node_tables.add(attribute.mapped_table)

            if node.is_subclass:  #for this to work, tables should be added by iterating through nodes from top to bottom in class hierarchy
                mvd_tables_set = set()
                get_all_relevant_mvd_tables_for_node_in_hierarchy(graph, node, mvd_tables_set)#all relevant mvd tables which come from top parents
                node.node_tables |= mvd_tables_set
                if node.is_contained_in_parent:  #contained in parent - single table inheritance
                    node.node_tables |= node.parent_entity.node_tables
                elif node.is_partially_by_itself:  #partially by itself - class table inheritance
                    node.node_tables |= node.parent_entity.node_tables
                elif node.is_all_by_itself:#no inserts to node.parent_entity if exist
                    continue
                elif node.is_contained_all_descendants:#no inserts to node.parent_entity if exist
                    continue
                else:#no_table
                    continue
            #print(node.unique_name, node.node_tables)

        elif node.is_relationship():  #for this to work, all entities node_tables should be added before adding node_tables for relationships
            node.node_tables = set()  #avoid duplicates
            if node.mapped_table:
                node.node_tables.add(node.mapped_table)

            for attribute in node.attributes:
                if attribute.is_multivalued and attribute.is_in_separate_table:
                    node.node_tables.add(attribute.mapped_table)

            #print(node.unique_name, node.node_tables)

    #after mapping all nodes - set node_tables for contained_all_descendants nodes - since all descendants tuples should be included
    #this has to be done after mapping all nodes - otherwise inserts will be propagated and duplicated to all nodes upwards
    for node in graph.nodes[
                ::-1]:  #this should be updated in reverse order - bottom to top - start with bottom most parent, add that table, then find next top parent with all by itself
        if node.is_entity() and node.is_subclass:
            node_tables_set = set()
            parent_entity = node.parent_entity
            while parent_entity is not None:
                if parent_entity.is_contained_all_descendants:
                    node_tables_set |= parent_entity.node_tables#child tuples need to be inserted to contained_all_descendants parent tables
                parent_entity = parent_entity.parent_entity

            node.node_tables |= node_tables_set


    #after mapping - check for nodes which didn't get mapped to tables - these are parent entities in inheritance hierarchy - this happen when no table option is chosen
    for node in graph.nodes[
                ::-1]:  #this should be updated in reverse order - bottom to top - start with bottom most parent, update it, then go up
        #since this is done bottom to top, no table parents in hierarchy are correctly updated with all by itself children tables and effect is propagated to top no table parents from bottom
        if node.is_entity():
            if not node.mapped_table:  #node doesn't map to any table - e.g. if person table doesn't exist-> need to map person queries to union of subclasses
                #this happens within class hierarchies only
                continue  #since node_tables is defined for purpose of inserts - no need to define for no table nodes


#mapped_tables_list is required for folded weak entities/1:M relationships with parent entity/many side entity as a hierarchy node which has a node_cover of size greater than 1
#mapped_tables_list for such folded weak_entity/relationship define the tables list in which it is distributed
#when creating table_mapping(generate_table_mappings) for inserts, for each table in the mapped_tables_list folded weak_entity/relationship node will be inserted into mapping
def initialize_mapped_tables_for_weak_entity_or_1_N_relationship_connecting_to_hierarchy_node_with_node_cover(
        graph, node):
    if node.is_entity() and node.is_weak_entity:
        assert len(node.parent_entity.node_cover)>1#parent node tuples distributed in multiple entities
        for node_name in node.parent_entity.node_cover:
            node_in_node_cover = graph.get_node_by_name(node_name)
            node.mapped_tables_list.append(node_in_node_cover.mapped_table)
    else:
        assert node.is_relationship() and check_if_relationship_is_1_N(node)
        many_side_entity = node.entity2 if not node.rel_dict['entity2']['one'] else node.entity1
        assert len(many_side_entity.node_cover)>1#folded many side tuples distributed in multiple entities
        for node_name in many_side_entity.node_cover:
            node_in_node_cover = graph.get_node_by_name(node_name)
            node.mapped_tables_list.append(node_in_node_cover.mapped_table)


def initialize_mapped_table_for_non_materialized_nodes(graph, config):
    for node in graph.nodes:
        if node.is_entity() and not node.is_subclass and not node.is_weak_entity:  #abstract parent class
            if config[node.unique_name] not in materialized_options["entity"]:
                node.mapped_table = None
                node.is_no_table = True
        elif node.is_entity() and node.is_subclass:
            if config[node.unique_name] not in materialized_options["sub_class"]:
                if config[node.unique_name] == "contained_in_parent":
                    node.mapped_table = node.parent_entity.mapped_table
                    node.is_contained_in_parent = True
                    node.is_no_table = False
                    node.is_partially_by_itself = False
                    node.is_all_by_itself = False
                    node.is_contained_all_descendants = False
                else:  #no table
                    node.mapped_table = None
                    node.is_no_table = True
        elif node.is_entity() and node.is_weak_entity:
            if config[node.unique_name] not in materialized_options["weak_entity"]:
                if len(node.parent_entity.node_cover)>1:#need to get table cover for folded weak entity - since full table is not just parent node mapped table
                    node.mapped_table = node.parent_entity.mapped_table  #map to parent table - but doesn't fully represent all parent tuples - need to get union all from parent node cover
                                                #setting mapped_table to the parent table important to get the table name when doing inserts
                    initialize_mapped_tables_for_weak_entity_or_1_N_relationship_connecting_to_hierarchy_node_with_node_cover(graph, node)
                else:
                    node.mapped_table = node.parent_entity.mapped_table
                node.is_contained_in_parent = True
                node.is_no_table = False
                node.is_partially_by_itself = False
                node.is_all_by_itself = False
                node.is_contained_all_descendants = False
        elif node.is_relationship() and check_if_relationship_is_1_N(node):
            if config[node.unique_name] not in materialized_options["1_N_relationship"]:
                many_side_entity = node.entity2 if not node.rel_dict['entity2']['one'] else node.entity1
                if len(many_side_entity.node_cover)>1:
                    node.mapped_table = many_side_entity.mapped_table  #map to parent table - but doesn't fully represent all many side tuples - need to get union all from many side node cover
                                #setting mapped_table to the parent table important to get the table name when doing inserts
                    initialize_mapped_tables_for_weak_entity_or_1_N_relationship_connecting_to_hierarchy_node_with_node_cover(graph, node)
                else:
                    node.mapped_table = many_side_entity.mapped_table
        elif node.is_attribute() and node.is_multivalued:
            if config[node.unique_name] not in materialized_options["multi_valued_attribute"]:
                node.is_in_separate_table = False
                node.mapped_table = node.entity.mapped_table

def check_if_contained_in_parent_node_links_to_contained_all_descendants_parent_without_all_or_partially_by_itself_intermediate_nodes(node, config):
    if config[node.parent_entity.unique_name] == "contained_all_descendants":
        return True
    elif config[node.parent_entity.unique_name] == "contained_in_parent":
        return check_if_contained_in_parent_node_links_to_contained_all_descendants_parent_without_all_or_partially_by_itself_intermediate_nodes(node.parent_entity, config)
    else:
        return False

#for a node in hierarchy - if node is not no_table - node_cover consists of node_itself, and contained_all_descendants/all_by_itself child nodes
#if node is no_table - node_cover consists contained_all_descendants/all_by_itself child nodes - doesn't include node itself since it is no_table
def find_minimum_node_cover_for_hierarchy_node(node, node_cover_list, config):
    for child in node.children:
        if config[child.unique_name]=="contained_all_descendants":#if node is contained_all_descendants, no need to explore further down the branch - that branch is covered
            node_cover_list.append(child.unique_name)
        elif config[child.unique_name]=="all_by_itself":#for all other options(all, contained in parent, partial, no_table) - need to explore down the branch
            node_cover_list.append(child.unique_name)
            find_minimum_node_cover_for_hierarchy_node(child, node_cover_list, config)
        elif config[child.unique_name]=="contained_in_parent" or config[child.unique_name]=="partially_by_itself":
            find_minimum_node_cover_for_hierarchy_node(child, node_cover_list, config)
        else:
            assert config[child.unique_name]=="no_table"
            find_minimum_node_cover_for_hierarchy_node(child, node_cover_list, config)


#node_cover is required for nodes in a hierarchy only - for non hierarchy nodes it is set to empty list, hence cover size is 0
#defined for all nodes in hierarchy
#tuples could be in full/sub set of attributes
#nodes which don't have tuples distributed in multiple nodes have len(node_cover)==0(for non-hierarchy nodes with all by itself) or len(node_cover)==1(itself is added -
#for hierarchy nodes with contained_all_descendants, leaf nodes with all by itself, and root with contained_all_descendants - guaranteed that node cover size is 1)
#if len(node.node_cover) is > 1 then it is mapped to multiple nodes - which means node.mapped_table doesn't fully contain all relevant tuples
#tuples are distributed across entities in node_cover
#except for contained_all_descendants option, all other 3 options(all, contained in, partially) can induce a node_cover
#except for node itself - all other nodes in cover for the node are contained_all_descendants or all by itself
#if node is no_table - then all nodes in cover are contained_all_descendants or all by itself since node itself is not added for cover for no_table node
#for leaf nodes only, all_by_itself guaranteed to not need a node_cover since for leaf node, node.mapped_table fully cover all tuples
def initialize_minimum_node_cover_for_hierarchy_nodes(graph, config):
    for node in graph.nodes[::-1]:  #this should be updated in reverse order - bottom to top - for children done first - then go up to parents
        if node.is_entity() and ((not node.is_subclass and len(node.children)>0) or node.is_subclass):#root or subclass in hierarchy
            node_cover_list = []
            if config[node.unique_name]=="contained_all_descendants" or (config[node.unique_name]=="all_by_itself" and len(node.children)==0):#contained_all_descendants nodes or all_by_itself leaf nodes
                node_cover_list.append(node.unique_name)#node itself contains all relevant tuples
            elif (config[node.unique_name]=="contained_in_parent" and
                  check_if_contained_in_parent_node_links_to_contained_all_descendants_parent_without_all_or_partially_by_itself_intermediate_nodes(node, config)):
                #e.g. user - CAD, employee - CIP, even though employee might have subclasses with ABI or CAD, user's table is sufficient to derive all employee tuples
                node_cover_list.append(node.unique_name)#node mapped table itself contains all relevant tuples
            elif config[node.unique_name]=="no_table":#for no table node - immediate children can be only contained_all_descendants, all by itself or no table
                find_minimum_node_cover_for_hierarchy_node(node, node_cover_list, config)
            else:
                node_cover_list.append(node.unique_name) #append node itself - to consider its mapped table - first entry in node_cover is itself - this matters since attributes names are all taken from node itself for union query
                find_minimum_node_cover_for_hierarchy_node(node, node_cover_list, config)
            assert len(node_cover_list) == len(set(node_cover_list))  #make sure no duplicates in node_cover_list
            node.node_cover = node_cover_list

#for a node - mapped_table_size is the (node.relation_size - all contained_all_descendants nodes relation_size - all all_by_itself nodes relation_size)
#thses contained_all_descendants/all_by_itself nodes will be in the subtree rooted at node
#if a contained_all_descendants/all_by_itself node found in a branch, no need to explore further down the the branch - that branch is covered
def find_mapped_table_size_for_materialized_node(graph, config, node, mapped_table_size_for_materialized_node):
    for child in node.children:
        if config[child.unique_name]=="contained_all_descendants":#since no inserts are propagated upwards from a child with CAD
            mapped_table_size_for_materialized_node -= child.relation_size
        elif config[child.unique_name]=="all_by_itself":#since no inserts are propagated upwards from a child with ABI
            mapped_table_size_for_materialized_node -= child.relation_size
        else:
            mapped_table_size_for_materialized_node = find_mapped_table_size_for_materialized_node(graph, config, child, mapped_table_size_for_materialized_node)
    return mapped_table_size_for_materialized_node

def define_the_generated_physical_schema(graph, config):
    reset_mapped_table_for_nodes(graph)
    reset_node_tables(graph)
    reset_node_options(graph)
    reset_keys(graph)
    reset_node_cover(graph)

    tables = []
    tables_dict = {}  #table_name:cardinality
    rel_name = "relation_"
    i = 0
    for node in graph.nodes:
        if node.is_entity() and not node.is_subclass and not node.is_weak_entity:  #if the entity is root of hieraarchy, then table size cannot be determined at this step
            if config[node.unique_name] in materialized_options["entity"]:
                tables.append(rel_name + str(i))
                node.mapped_table = (node.sort_key, rel_name + str(i))
                if config[node.unique_name] == "contained_all_descendants":#if root is contained_all_descendants
                    tables_dict[node.mapped_table[1]] = (
                        node.relation_size, node.relation_size)  #(relation_size, entity_distinct_keys)
                else:
                    assert config[node.unique_name] == "all_by_itself"
                    if len(node.children)>0:#all by itself root
                        mapped_table_size_for_materialized_node = node.relation_size
                        mapped_table_size_for_materialized_node = find_mapped_table_size_for_materialized_node(graph, config, node, mapped_table_size_for_materialized_node)
                        tables_dict[node.mapped_table[1]] = (mapped_table_size_for_materialized_node, mapped_table_size_for_materialized_node)
                    else: #regular strong entity
                        tables_dict[node.mapped_table[1]] = (
                            node.relation_size, node.relation_size)  #(relation_size, entity_distinct_keys)
                i += 1
                node.is_all_by_itself = True if config[node.unique_name] == "all_by_itself" else False#for regular strong entity or root
                node.is_contained_all_descendants = True if config[node.unique_name] == "contained_all_descendants" else False  #for root
        elif node.is_entity() and node.is_subclass:
            if config[node.unique_name] in materialized_options["sub_class"]:
                tables.append(rel_name + str(i))
                node.mapped_table = (node.sort_key, rel_name + str(i))
                if config[node.unique_name] == "contained_all_descendants":
                    tables_dict[node.mapped_table[1]] = (node.relation_size, node.relation_size)  #(relation_size, entity_distinct_keys)
                else:#other materialized options - all/partially_by_itself
                    mapped_table_size_for_materialized_node = node.relation_size
                    mapped_table_size_for_materialized_node = find_mapped_table_size_for_materialized_node(graph, config, node, mapped_table_size_for_materialized_node)
                    tables_dict[node.mapped_table[1]] = (mapped_table_size_for_materialized_node, mapped_table_size_for_materialized_node)
                i += 1
                node.is_partially_by_itself = True if config[node.unique_name] == "partially_by_itself" else False
                node.is_all_by_itself = True if config[node.unique_name] == "all_by_itself" else False
                node.is_contained_all_descendants = True if config[node.unique_name] == "contained_all_descendants" else False
                node.is_contained_in_parent = False
        elif node.is_entity() and node.is_weak_entity:
            if config[node.unique_name] in materialized_options["weak_entity"]:
                tables.append(rel_name + str(i))
                node.mapped_table = (node.sort_key, rel_name + str(i))
                tables_dict[node.mapped_table[1]] = (
                    node.relation_size, node.relation_size)  #(relation_size, entity_distinct_keys)
                i += 1
                node.is_contained_in_parent = False
                node.is_partially_by_itself = False
                node.is_contained_all_descendants = False
                node.is_all_by_itself = True
        elif node.is_relationship():
            if check_if_relationship_is_1_N(node):
                if config[node.unique_name] in materialized_options["1_N_relationship"]:
                    tables.append(rel_name + str(i))
                    node.mapped_table = (node.sort_key, rel_name + str(i))
                    tables_dict[node.mapped_table[1]] = (node.relation_size, node.entity1.relation_size,
                                                         node.entity2.relation_size)  #(relation_size, entity1_distinct_keys, entity2_distinct_keys) - here relation size equal many side relation size if many side is total participation
                    i += 1
            else:
                if config[node.unique_name] in materialized_options["M_N_relationship"]:
                    tables.append(rel_name + str(i))
                    node.mapped_table = (node.sort_key, rel_name + str(i))
                    tables_dict[node.mapped_table[1]] = (node.relation_size, node.entity1.relation_size,
                                                         node.entity2.relation_size)  #(relation_size, entity1_distinct_keys, entity2_distinct_keys)
                    i += 1
        elif node.is_attribute() and node.is_multivalued:
            if config[node.unique_name] in materialized_options["multi_valued_attribute"]:
                tables.append(rel_name + str(i))
                node.mapped_table = (node.sort_key, rel_name + str(i))
                tables_dict[node.mapped_table[1]] = (
                    node.relation_size, node.entity.relation_size)  #(relation_size, entity_distinct_keys)
                i += 1
                node.is_in_separate_table = True

    initialize_minimum_node_cover_for_hierarchy_nodes(graph, config)

    initialize_mapped_table_for_non_materialized_nodes(graph, config)

    figure_out_mappings(graph, config)

    return tables_dict


#including its own mvd tables - defined for nodes with contained_all_descendants, all by itself
#for contained_all_descendants node, and leaf all by itself node - own mapped_table and mvd tables fully define node
#for non-leaf all by itself node - own mapped_table and mvd tables may not fully define node if its node cover > 1 - however full coverage is acheived by considering all nodes in node_cover
def get_table_list_unique_to_node(graph, node, tables_list: list):
    assert node is not None
    assert node.is_contained_all_descendants == True or node.is_all_by_itself == True
    if node.is_contained_all_descendants or node.is_all_by_itself:
        tables_list.append(node.mapped_table)
        add_mvd_tables_for_node(graph, node, tables_list)
        return tables_list


def add_mvd_tables_for_node(graph, node, tables_list):
    for attribute in node.attribute_list:
        if "pk_name" not in attribute and "name" in attribute:#filter for non-pk attributes
            attribute_node = graph.get_node_by_name(attribute["unique_name"])
            if attribute_node.is_multivalued and attribute_node.is_in_separate_table:#cannot check is_in_separate_table value in attribute_list without deriving attribute_node
                          #doing attribute.get("is_in_separate_table", False) is incorrect since those values in list are not yet set for config. Still in finding config phase
                tables_list.append(attribute_node.mapped_table)#all separate mvd tables - either coming from top parents or itself

#immediate parent of contained_all_descendants or all by itself
def get_table_list_unique_to_immediate_parent_node_with_all_by_itself(graph, config, node,
                                                                      tables_list):  #immediate parent to node
    assert node is not None
    if config[node.unique_name] == "contained_all_descendants" or config[node.unique_name] == "all_by_itself":
        tables_list.append(node.mapped_table)
        add_mvd_tables_for_node(graph, node, tables_list)
        return tables_list, node.unique_name
    elif config[node.unique_name] == "partially_by_itself":
        return get_table_list_unique_to_immediate_parent_node_with_all_by_itself(graph, config, node.parent_entity,
                                                                                 tables_list)
    elif config[node.unique_name] == "contained_in_parent":
        return get_table_list_unique_to_immediate_parent_node_with_all_by_itself(graph, config, node.parent_entity,
                                                                                 tables_list)


def get_table_list_unique_to_immediate_parent_node_with_all_by_itself_without_mvd_tables(graph, config, node,
                                                                                         tables_list):  #immediate parent to node
    assert node is not None
    if config[node.unique_name] == "contained_all_descendants" or config[node.unique_name] == "all_by_itself":
        tables_list.append(node.mapped_table)
        return tables_list, node.unique_name
    elif config[node.unique_name] == "partially_by_itself":
        return get_table_list_unique_to_immediate_parent_node_with_all_by_itself_without_mvd_tables(graph, config,
                                                                                                    node.parent_entity,
                                                                                                    tables_list)
    elif config[node.unique_name] == "contained_in_parent":
        return get_table_list_unique_to_immediate_parent_node_with_all_by_itself_without_mvd_tables(graph, config,
                                                                                                    node.parent_entity,
                                                                                                    tables_list)


#if node's len(node.node_cover) > 1 - node itself(node.mapped_table) cannot fully cover all tuples
#node_cover for a node contains node itself, and child nodes of contained_all_descendants/all_by_itself in the subtree rooted by the node
#after relevant tables coming from node itself is added, add relevant tables for child nodes in node_cover
#for each child node(of contained_all_descendants/all_by_itself) - only its mapped table added - no mvd tables added since for parent node, child mvd tables are irrelevant
def complete_table_set_to_cover_entity_with_node_cover(graph, node, tables_set):
    assert node is not None
    assert len(node.node_cover) > 1  #if more than 1 - entity.mapped_table cannot cover all tuples
    for node_name in node.node_cover:#apart from node itself each node in node_cover should be contained_all_descendants, all by itself only, since no table nodes are already represented by nodes in node_cover
        node_cover_node = graph.get_node_by_name(node_name)
        assert node_cover_node.mapped_table is not None
        if node_cover_node.unique_name == node.unique_name:#node itself - skip since relevant tables from node itself are already added for node table_cover
            continue
        elif node_cover_node.is_contained_all_descendants:
            tables_set.add(node_cover_node.mapped_table) #mapped_table
        else:
            assert node_cover_node.is_all_by_itself
            tables_set.add(node_cover_node.mapped_table) #mapped_table - even though node_cover_node may not be fully defined by its mapped_table if it is a non-leaf,
            #since all children of contained_all_descendants/all in the subtree rooted by node is included in node_cover, overall full coverage is guaranteed when all "all_by_itself" children are iterated



def get_dependent_entities_for_weak_entity(graph, weak_entity, depending_entities):
    depending_entities.append(weak_entity.parent_entity.unique_name)
    if weak_entity.parent_entity.is_weak_entity:  #if parent is also a weak entity, need to iterate until a strong depending entity found
        get_dependent_entities_for_weak_entity(graph, weak_entity.parent_entity, depending_entities)

#if hierarchical node has children and its node cover is 1, then for such nodes, it can be contained_all_descendants node or any other options
#if node is having other options(all/partially/contained) then there should not be any child with contained_all_descendants/all by itself option in the subtree rooted under the node
#second condition checked here
def assert_no_contained_all_descendants_or_all_by_itself_child_nodes_in_the_subtree_rooted_by_node(node):
    for child in node.children:
        if not child.is_contained_all_descendants or not child.is_all_by_itself:
            is_assert = assert_no_contained_all_descendants_or_all_by_itself_child_nodes_in_the_subtree_rooted_by_node(child)
            if not is_assert:
                return False
            else:
                continue
        else:
            return False
    return True

#For a strong entity(hierarchy or non-hierarchy) - this method defines the tables coming from the entity itself only - own mapped_table and mvd tables
#For entities with len(entity.node_cover)>1 - hence this doesn't fully define table_cover - to fully build the table_cover for entity, the tables from
#contained_all_descendants/all_by_itself child nodes in node_cover is considered with complete_table_set_to_cover_entity_with_node_cover method
#For weak_entity/relationship having a connection to an entity distributed in node_cover - full view of the entity is included in the table_cover as the view fully covers the entity
def initialize_table_cover_for_nodes_helper(graph, config, entity_or_relationship_node):
    if entity_or_relationship_node.mapped_table or entity_or_relationship_node.mapped_tables_list:  #set table cover for non- no_table nodes
        if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_all_by_itself  and
                not entity_or_relationship_node.is_subclass and not entity_or_relationship_node.is_weak_entity and len(entity_or_relationship_node.children)==0):#excluding root
            #fully include all tuples
            return entity_or_relationship_node.node_tables.copy()  #for strong entity(non-hierarchical), node_tables contain only its mapped_table and own mvd_tables
        elif (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_contained_all_descendants  and not entity_or_relationship_node.is_subclass):#root
            #fully include all tuples
            return entity_or_relationship_node.node_tables.copy()  #for contained_all_descendants root, its node_tables contain only its mapped_table and own mvd_tables
        elif (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_all_by_itself and
              not entity_or_relationship_node.is_subclass and not entity_or_relationship_node.is_weak_entity):#root with all by itself
            #may not fully include all tuples
            #if the node_cover > 1, then entity_or_relationship_node has contained_all_descendants/all children in the subtree rooted by entity_or_relationship_node
            #the mapped_table of the entity_or_relationship_node doesn't include tuples from those children
            #first get tuples coming by coverage of itself - this does that - then add tuples from contained_all_descendants/all children if exists to get full cover - complete_table_set_to_cover_entity_with_node_cover does that
            assert len(entity_or_relationship_node.children) > 0
            tables_list_unique_to_node = []
            #mapped_table and all mvd_tables coming from parents or itself
            return set(get_table_list_unique_to_node(graph, entity_or_relationship_node, tables_list_unique_to_node))
        elif entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_subclass:
            if entity_or_relationship_node.is_contained_in_parent:#may not fully include all tuples if len(entity_or_relationship_node.node_cover) > 1
                #if the node_cover > 1, then entity_or_relationship_node has contained_all_descendants/all children in the subtree rooted by entity_or_relationship_node
                #the mapped_table of the entity_or_relationship_node doesn't includes tuples from those children
                #first get tuples coming by coverage of itself - this does that - then add tuples from contained_all_descendants/all children to get full cover - complete_table_set_to_cover_entity_with_node_cover does that
                tables_set = set()
                tables_list = []
                add_mvd_tables_for_node(graph, entity_or_relationship_node,
                                        tables_list)  #if own mvds are still in separate tables
                tables_set |= set(tables_list)
                tables_set |= initialize_table_cover_for_nodes_helper(graph, config,
                                                                      entity_or_relationship_node.parent_entity)
                return tables_set
            elif entity_or_relationship_node.is_partially_by_itself:#may not fully include all tuples if len(entity_or_relationship_node.node_cover) > 1
                #if the node_cover > 1, then entity_or_relationship_node has contained_all_descendants/all children in the subtree rooted by entity_or_relationship_node
                #the mapped_table of the entity_or_relationship_node doesn't includes tuples from those children
                #first get tuples coming by coverage of  itself - this does that - then add tuples from contained_all_descendants/all children to get full cover - complete_table_set_to_cover_entity_with_node_cover does that
                tables_list_unique_to_immediate_parent_with_all_by_itself = []
                tables_list_unique_to_immediate_parent_with_all_by_itself, immediate_parent_unique_name = (
                    get_table_list_unique_to_immediate_parent_node_with_all_by_itself(graph, config,
                                                                                      entity_or_relationship_node.parent_entity,
                                                                                      tables_list_unique_to_immediate_parent_with_all_by_itself))
                immediate_parent_with_all_by_itself = graph.get_node_by_name(immediate_parent_unique_name)
                assert immediate_parent_with_all_by_itself is not None
                table_set = (set(tables_list_unique_to_immediate_parent_with_all_by_itself) |
                             entity_or_relationship_node.node_tables.difference(
                                 immediate_parent_with_all_by_itself.node_tables))
                return table_set
            elif entity_or_relationship_node.is_all_by_itself:
                if len(entity_or_relationship_node.node_cover) > 1:#need to get cover from itself and all its children
                    #if the node_cover > 1, then entity_or_relationship_node has contained_all_descendants/all children in the subtree rooted by entity_or_relationship_node
                    #the mapped_table of the entity_or_relationship_node doesn't include tuples from those children
                    #first get tuples coming from itself - this does that - then add tuples from contained_all_descendants/all children to get full cover - complete_table_set_to_cover_entity_with_node_cover does that
                    tables_list_unique_to_node = []
                    #mapped_table and all mvd_tables coming from parents or itself
                    return set(get_table_list_unique_to_node(graph, entity_or_relationship_node, tables_list_unique_to_node))
                else:#node's own mapped_table and mvd tables sufficient to fully define node
                    #if all by itself node's node_cover is 1, either it has to be a leaf node, or there shouldn't be any contained_all_descendants/all child nodes in the subtree rooted by the node
                    assert len(entity_or_relationship_node.node_cover) == 1
                    assert (len(entity_or_relationship_node.children) == 0 or
                            assert_no_contained_all_descendants_or_all_by_itself_child_nodes_in_the_subtree_rooted_by_node(entity_or_relationship_node))
                    tables_list_unique_to_node = []
                    return set(get_table_list_unique_to_node(graph, entity_or_relationship_node, tables_list_unique_to_node))
            elif entity_or_relationship_node.is_contained_all_descendants: #node's own mapped_table and mvd tables sufficient to fully define node
                tables_list_unique_to_node = []
                return set(get_table_list_unique_to_node(graph, entity_or_relationship_node, tables_list_unique_to_node))
        elif entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity:  #added for weak entity since according to assumption, select * from weak entity
            depending_entities = []  #should get all parent attributes + weak entity attributes (not just pks + weak entity)
            table_set = set()  #this definition is an assumption
            get_dependent_entities_for_weak_entity(graph, entity_or_relationship_node, depending_entities)
            for parent_entity in depending_entities:
                parent_node = graph.get_node_by_name(parent_entity)
                assert len(table_cover_for_nodes[parent_node.unique_name][parent_node.unique_name]) > 0
                #a node is incomplete in its own mapped_table only if len(node.node_cover) > 1
                if len(parent_node.node_cover)>1:  #if weak entity has a depending parent disributed in node_cover - parent's full table view is added
                    #this is added as a representation for full table generated for parent_node by doing union across its node_cover - all required coverage(including mvd s) is in the full union table itself
                    parent_entity_full_table_view_name = "temp_" + parent_node.unique_name
                    parent_entity_table_cover = [(parent_node.sort_key, parent_entity_full_table_view_name)]
                else:
                    parent_entity_table_cover = table_cover_for_nodes[parent_node.unique_name][parent_node.unique_name]
                table_set |= set(
                    parent_entity_table_cover)  #table cover for all parent_nodes need to be initialized before weak entity
            if entity_or_relationship_node.is_all_by_itself:
                table_set |= entity_or_relationship_node.node_tables  #for weak entity with all by itself - node_tables contain only mapped table and mvd tables if mvds in separate tables
            #if weak entity is folded and it has mvds - mvds assumed to be included in folded attributes as well - assumed mvds from folded weak entity cannot exist in separate tables
            #for folded weak entities with parent distributed in node_cover, no need to do sum with mapped_tables_list since when answering the query - the aggregated parent entity by unions is generated
            return table_set
        elif entity_or_relationship_node.is_relationship():
            table_set = set()
            #if relationship has a participating entity distributed in node_cover - only participating entity's full table view is added
            #this is added as a representation for full table generated for participating entity by doing union across its node_cover - all required coverage is in the full union table itself
            if len(entity_or_relationship_node.entity1.node_cover) > 1:
                #a view is needed only when mapped_table doesn't cover - that happens when its len(node.node_cover) > 1
                entity1_full_table_view_name = "temp_" + entity_or_relationship_node.entity1.unique_name
                entity1_table_cover = [(entity_or_relationship_node.entity1.sort_key, entity1_full_table_view_name)]
            else:
                entity1_table_cover = table_cover_for_nodes[entity_or_relationship_node.entity1.unique_name][
                    entity_or_relationship_node.entity1.unique_name]

            if len(entity_or_relationship_node.entity2.node_cover) > 1:
                entity2_full_table_view_name = "temp_" + entity_or_relationship_node.entity2.unique_name
                entity2_table_cover = [(entity_or_relationship_node.entity2.sort_key, entity2_full_table_view_name)]
            else:
                entity2_table_cover = table_cover_for_nodes[entity_or_relationship_node.entity2.unique_name][
                    entity_or_relationship_node.entity2.unique_name]

            if config[entity_or_relationship_node.unique_name] == "folded_to_many_side":  #1:N relationship
                many_side = entity_or_relationship_node.entity1 if (not entity_or_relationship_node.rel_dict['entity1']['one'] and
                                                                    entity_or_relationship_node.rel_dict['entity2']['one']) \
                    else entity_or_relationship_node.entity2
                if len(many_side.node_cover) > 1:  #a node is incomplete in its own mapped_table only its len(node.node_cover) > 1
                    relationship_node_mvd_tables_set = set()
                    add_mvd_tables_for_node(graph, entity_or_relationship_node, relationship_node_mvd_tables_set)
                    many_side_full_table_view_name = "temp_" + many_side.unique_name
                    relationship_node_table_cover = {(many_side.sort_key,
                                                      many_side_full_table_view_name)}  #mapped table is the complete table view of the many side
                    relationship_node_table_cover |= relationship_node_mvd_tables_set
                else:
                    relationship_node_table_cover = entity_or_relationship_node.node_tables  #for relationship - node_tables contain only mapped table and mvd tables if mvds in separate tables
            else:
                relationship_node_table_cover = entity_or_relationship_node.node_tables.copy()  #for relationship - node_tables contain only mapped table and mvd tables if mvds in separate tables

            table_set |= set(entity1_table_cover)
            table_set |= set(entity2_table_cover)
            table_set |= relationship_node_table_cover
            table_cover_for_nodes[entity_or_relationship_node.unique_name] = {
                entity_or_relationship_node.entity1.unique_name: entity1_table_cover,
                entity_or_relationship_node.entity2.unique_name: entity2_table_cover,
                entity_or_relationship_node.unique_name: list(relationship_node_table_cover)}
            return table_set
    else:  #no table - return empty set
        return set()


#for strong entity(or subclass with node cover == 1) - table cover is just its mapped table and own mvd tables
#for root or subclass with node_cover - table cover is the table view generated for node from mapped_table and mvd tables of nodes in its node_cover(node_cover
#includes node itself to consider coverage from its own mapped_table and mvd tables, and all contained_all_descendants/all_by_itself child nodes in the subtree rooted by the node)
#for weak entity - table cover is its mapped table, all dependent parents(upto a strong parent), its own mvd tables
#for relationship - its own mapped table including its mvd tables, table cover from two participating entites
#e.g. Assume all nodes in hierarchy are all by itself - if Person's node cover is Graduate_Student, Student, Person -> Person's table cover is
#mapped_table and own mvd tables from Graduate Student, mapped_table and own mvd tables from Student, and mapped_table and own mvd tables from Person. Even though Person's
#mapped_table doesn't fully define Person, through node cover of Person, table cover is achieved.
def initialize_table_cover_for_nodes(graph, config):
    reset_table_cover_for_nodes()

    for node in graph.nodes:
        if node.is_entity():
            tables_set = initialize_table_cover_for_nodes_helper(graph, config, node)#add relevant tables from node itself
            #complete_table_set_to_cover_entity_with_node_cover is not executed since tuple cover for cost calculation is achieved by the node cover for node
            #all nodes except for node itself in its node cover are child nodes with contained_all_descendants/all option in the subtree rooted by node
            #in cost calculation, all nodes except for node itself in nodecover are handled separately and table_cover_for_nodes is used for node itself only
            #hence tables added to table_cover_for_nodes relevant to node will be considering only node - hence complete_table_set_to_cover_entity_with_node_cover not executed
            #this will work correctly for -> table_list = table_cover_for_nodes.get(node.unique_name).get(node.unique_name) and sorting - table_list.sort(key=lambda x: x[0], reverse=True)
            #if len(node.node_cover) > 1:#add relevant tables to cover all tuples - tables coming from contained_all_descendants/all child nodes in node.node_cover
            #    complete_table_set_to_cover_entity_with_node_cover(graph, node, tables_set)
            table_list = list(tables_set)
            table_cover_for_nodes[node.unique_name] = {node.unique_name: table_list}
        elif node.is_relationship():
            initialize_table_cover_for_nodes_helper(graph, config, node)


def calculate_db_initialization_insert_cost_for_tables(tables_dict):
    insert_cost_for_all_tables = 0

    for table in tables_dict:
        table_size = tables_dict.get(table)[0]
        insert_cost_for_all_tables += insert_cost(table_size, num_indexes=1)#assume each table has index for primary key - each tuple incurs an insert + index update cost
    #print("db initialization insert cost: ",insert_cost_for_all_tables)
    node_cost["db_initialization_insert_cost"] = insert_cost_for_all_tables#set insert cost for chosen config
    return insert_cost_for_all_tables

#insert cost to generate temp tables and update cost to update schema tables for folded relationships or weak entities by joining with temp tables
def calculate_db_initialization_insert_cost_for_folded_weak_entities_and_relationships(graph, config, tables_dict, table_widths):
    update_cost_for_all_tables = 0
    for node in graph.nodes:
        if node.is_entity() and node.is_weak_entity and config[node.unique_name] == "contained_in_parent":#folded weak entity
            #in temp table, weak entity tuples are aggregated by parent's key
            #temp table has no of tuples equal to no_of_parent_entity_tuples_with_atleast_one_weak_entity_tuple
            assert node.mapped_table == node.parent_entity.mapped_table#node folded in parent entity
            avg_no_of_parent_entity_tuples_with_atleast_one_weak_entity_tuple = (node.parent_entity.relation_size *
                                                                                 (1 - (1 - 1.0/node.parent_entity.relation_size)**node.relation_size))
            temp_table_no_of_tuples = avg_no_of_parent_entity_tuples_with_atleast_one_weak_entity_tuple
            #cost to generate the update-temp table
            update_cost_for_all_tables += insert_cost(temp_table_no_of_tuples, num_indexes=1)#temp_table_no_of_tuples
            #join cost with tables for update-temp table
            if len(node.parent_entity.node_cover) > 1:
                for node_cover_node_name in node.parent_entity.node_cover:
                    node_cover_node = graph.get_node_by_name(node_cover_node_name)
                    if node_cover_node.unique_name != node.parent_entity.unique_name:
                        assert node_cover_node.is_contained_all_descendants or node_cover_node.is_all_by_itself
                        node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                        update_cost_for_all_tables += sort_merge_join_cost(node_cover_node_table_size, temp_table_no_of_tuples)
                        update_cost_for_all_tables += insert_cost(temp_table_no_of_tuples, num_indexes=1)
                    else:#node.parent_entity itself
                        assert node_cover_node.unique_name == node.parent_entity.unique_name#node.parent_entity itself - node could be all/contained/partial
                        if config[node_cover_node.unique_name] == "all_by_itself" or config[node_cover_node.unique_name] == "partially_by_itself":
                            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            update_cost_for_all_tables += sort_merge_join_cost(node_cover_node_table_size, temp_table_no_of_tuples)
                        else:
                            assert config[node_cover_node.unique_name] == "contained_in_parent"
                            relevant_node_cover_node_tuples_in_mapped_table = node_cover_node.relation_size
                            relevant_node_cover_node_tuples_in_mapped_table = find_mapped_table_size_for_materialized_node(graph, config, node_cover_node,
                                                                                                                           relevant_node_cover_node_tuples_in_mapped_table)#modify node size to remove tuples from
                            #contained_all_descendants or all children in subtree rooted by node
                            #filter for node tuples - hence left size is (node.relation_size - all tuples from contained_all_descendants/all child in subtree rooted by node(not tables_dict.get(node.mapped_table[1])[0]))
                            node_mapped_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            update_cost_for_all_tables += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - considered # of tuples instead of area
                            update_cost_for_all_tables += sort_merge_join_cost(relevant_node_cover_node_tuples_in_mapped_table, temp_table_no_of_tuples)
            elif node.parent_entity.is_subclass and config[node.parent_entity.unique_name] == "contained_in_parent":
                assert len(node.parent_entity.node_cover) == 1 #not distributed in node cover
                relevant_node_tuples_in_mapped_table = node.parent_entity.relation_size
                node_mapped_table_size = tables_dict.get(node.parent_entity.mapped_table[1])[0]
                update_cost_for_all_tables += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - considered # of tuples instead of area
                update_cost_for_all_tables += sort_merge_join_cost(relevant_node_tuples_in_mapped_table, temp_table_no_of_tuples)
            else:#regular entities or parent entity is also ABI weak entity or hierarch entities not CIP and not distributed in node cover
                assert len(node.parent_entity.node_cover) <= 1 #not distributed in node cover
                assert (config[node.parent_entity.unique_name] == "all_by_itself" or config[node.parent_entity.unique_name] == "partially_by_itself" or
                        config[node.parent_entity.unique_name] == "contained_all_descendants")
                update_cost_for_all_tables += sort_merge_join_cost(node.parent_entity.relation_size, temp_table_no_of_tuples)

            update_cost_for_all_tables += insert_cost(node.relation_size, num_indexes=0)#after joins with temp table, cost to insert weak entity tuples, no indexes are updated
                                                                                        #since weak entity is a folded column

        elif node.is_relationship() and config[node.unique_name] == "folded_to_many_side":
            #temp table for folded relationship has folded_node.relation_size no of tuples
            temp_table_no_of_tuples = node.relation_size
            #cost to generate the update-temp table
            update_cost_for_all_tables += insert_cost(temp_table_no_of_tuples, num_indexes=1)#temp_table_no_of_tuples
            #join cost with tables for update-temp table
            many_side_entity = node.entity2 if (node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']) else node.entity1
            if len(many_side_entity.node_cover) > 1:
                for node_cover_node_name in many_side_entity.node_cover:
                    node_cover_node = graph.get_node_by_name(node_cover_node_name)
                    if node_cover_node.unique_name != many_side_entity.unique_name:
                        assert node_cover_node.is_contained_all_descendants or node_cover_node.is_all_by_itself
                        node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                        update_cost_for_all_tables += sort_merge_join_cost(node_cover_node_table_size, temp_table_no_of_tuples)
                    else:#many_side node itself
                        assert node_cover_node.unique_name == many_side_entity.unique_name#many side node itself - node could be all/contained/partial
                        if config[node_cover_node.unique_name] == "all_by_itself" or config[node_cover_node.unique_name] == "partially_by_itself":
                            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            update_cost_for_all_tables += sort_merge_join_cost(node_cover_node_table_size, temp_table_no_of_tuples)
                        else:
                            assert config[node_cover_node.unique_name] == "contained_in_parent"
                            relevant_node_cover_node_tuples_in_mapped_table = node_cover_node.relation_size
                            relevant_node_cover_node_tuples_in_mapped_table = find_mapped_table_size_for_materialized_node(graph, config, node_cover_node,
                                                                                                               relevant_node_cover_node_tuples_in_mapped_table)#modify node size to remove tuples from
                            #contained_all_descendants or all children in subtree rooted by node
                            #filter for node tuples - hence left size is (node.relation_size - all tuples from contained_all_descendants/all child in subtree rooted by node(not tables_dict.get(node.mapped_table[1])[0]))
                            node_mapped_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            update_cost_for_all_tables += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - considered # of tuples instead of area
                            update_cost_for_all_tables += sort_merge_join_cost(relevant_node_cover_node_tuples_in_mapped_table, temp_table_no_of_tuples)
            elif many_side_entity.is_subclass and config[many_side_entity.unique_name] == "contained_in_parent":
                assert len(many_side_entity.node_cover) == 1 #not distributed in node cover
                relevant_node_tuples_in_mapped_table = many_side_entity.relation_size
                node_mapped_table_size = tables_dict.get(many_side_entity.mapped_table[1])[0]
                update_cost_for_all_tables += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - considered # of tuples instead of area
                update_cost_for_all_tables += sort_merge_join_cost(relevant_node_tuples_in_mapped_table, temp_table_no_of_tuples)
            else:#regular entities, or hierarch entities not CIP and not distributed in node cover
                assert len(many_side_entity.node_cover) <= 1 #not distributed in node cover
                update_cost_for_all_tables += sort_merge_join_cost(many_side_entity.relation_size, temp_table_no_of_tuples)

            update_cost_for_all_tables += insert_cost(node.relation_size, num_indexes=0)#after joins with temp table, cost to insert relationship tuples, no indexes are updated
                                                                                        #since relationship is a folded column

    #print("db initialization folded_weak_entity_relationship_insert_cost: ",update_cost_for_all_tables)
    node_cost["db_initialization_folded_weak_entity_relationship_insert_cost"] = update_cost_for_all_tables#set update cost for chosen config
    return update_cost_for_all_tables

def calculate_mvd_table_cost_helper(left_size, aggregated_mvd_table_size, mvd_table_size, parent_sorted, is_mvd_aggregated_table_built=False):
    cost = 0
    if not is_mvd_aggregated_table_built:#cost to aggregate the mvd table by pk
        cost += scan_cost(mvd_table_size)#aggregate cost for mvd
    cost += sort_merge_join_cost(left_size, aggregated_mvd_table_size) if not parent_sorted else (
        sort_merge_join_cost(left_size, aggregated_mvd_table_size, left_sorted=parent_sorted))#assume after first join left is sorted
    return cost

#calculate all relevant mvd tables join cost for node
#mvd tables could be from node itself or a parent if node is in hierarchy
def calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, node, left_size, node_sorted, is_mvd_aggregated_table_built=False):#node - from which mvd s coming from, left_size - left relation of join size
    total_mvd_join_cost = 0
    node_relevant_mvd_attributes_in_separate_tables = []#mvds can come from itself or from parents if node belongs to a hierarchy
    for attribute in node.attribute_list:
        if "pk_name" in attribute:
            continue
        else:
            assert "name" in attribute
            attribute_node = graph.get_node_by_name(attribute["unique_name"])
            if attribute_node.is_multivalued and attribute_node.is_in_separate_table:#cannot check is_in_separate_table value in attribute_list without deriving attribute_node
                                                                            #since those values in list are not yet set for config. Still in finding config phase
                node_relevant_mvd_attributes_in_separate_tables.append(attribute["unique_name"])
    for attr_unique_name in node_relevant_mvd_attributes_in_separate_tables:
        attribute_node = graph.get_node_by_name(attr_unique_name)
        assert attribute_node.is_multivalued and attribute_node.is_in_separate_table
        mvd_table_size = tables_dict.get(attribute_node.mapped_table[1])[0]
        mvd_table_width = table_widths.get(attribute_node.mapped_table[1])
        mvd_table_width = 1#modified back to consider only # of tuples not area
        mvd_table_size *= mvd_table_width
        mvd_entity_size = attribute_node.entity.relation_size#mvd entity size is required since this is equal to aggregated mvd table size(mvd table is aggregated by mvd entity's pk s)
                                                                #assuming each entity tuple has a mvd - total participation
        aggregated_by_pk_mvd_table_size = mvd_entity_size * 2#only two columns - width is 2 - pk and mvd array aggregated
        aggregated_by_pk_mvd_table_size = mvd_entity_size #re-modified to consider only # of tuples not area
        total_mvd_join_cost += calculate_mvd_table_cost_helper(left_size, aggregated_by_pk_mvd_table_size, mvd_table_size,
                                                                                                    node_sorted, is_mvd_aggregated_table_built)
        node_sorted = True#after first join of a mvd table, if there are more mvd tables to join, now left side is sorted already
    return total_mvd_join_cost

#calculate one mvd table join cost
def calculate_mvd_table_cost(tables_dict, table_widths, mvd_attribute_node, left_size, node_sorted, is_mvd_aggregated_table_built=False):#node - from which mvd s coming from, left_size - left relation of join size
    total_mvd_join_cost = 0
    assert mvd_attribute_node.is_multivalued and mvd_attribute_node.is_in_separate_table
    mvd_table_size = tables_dict.get(mvd_attribute_node.mapped_table[1])[0]
    mvd_table_width = table_widths.get(mvd_attribute_node.mapped_table[1])
    mvd_table_width = 1#modified to consider only # of tuples not area
    mvd_table_size *= mvd_table_width
    mvd_attribute_node_entity_relation_size = mvd_attribute_node.entity.relation_size#entity node size is required since this is equal to aggregated mvd table size(mvd table is aggregated by its entity node's pk s)
                                                                            #assuming each entity tuple has a mvd - total participation
    aggregated_by_pk_mvd_table_size = mvd_attribute_node_entity_relation_size * 2#only two columns - width is 2 - pk and mvd array aggregated
    aggregated_by_pk_mvd_table_size = mvd_attribute_node_entity_relation_size #modified to consider only # of tuples not area
    total_mvd_join_cost += calculate_mvd_table_cost_helper(left_size, aggregated_by_pk_mvd_table_size, mvd_table_size,
                                                                                            node_sorted, is_mvd_aggregated_table_built)
    return total_mvd_join_cost

def get_union_table_view_size_for_node_distributed_in_node_cover(graph, node, tables_dict, table_widths):

    table_view_size = node.relation_size#all tuples after doing union across node cover
    table_view_width = table_widths.get(node.mapped_table[1])#get width from node's original mapped_table(accounts for any folded
                                                             # weak entity/relationship columns as well)
    #the view will have this many columns plus all mvd columns added from relevant separate mvd tables - need to add separate mvd columns that get added
    for attribute in node.attribute_list:
        if "pk_name" not in attribute and "name" in attribute:#filter for non-pk attributes
            attribute_node = graph.get_node_by_name(attribute["unique_name"])
            if attribute_node.is_multivalued and attribute_node.is_in_separate_table:
                table_view_width += 1#for each relevant mvd in separate table(either coming from node itself or parents), a column is added
    #table_view_size *= table_view_width#for cost calculation - area = # of tuple * table width is considered
    table_view_size *= 1#modified back to only consider # of tuples not area
    return table_view_size

#required for entities which participate in relationships or for an entity in which a weak entity is folded
#defined for entities only - full width for select * definition of entity
#for strong entity - its own attributes(if entity belongs to hierarchy - any attributes inherited from top parents as well)
#for weak entity - its own attributes + attributes from depending parents until a strong parent entity found
def get_full_width_of_table_after_building_full_entity_node(graph, node):
    assert node.is_entity()
    table_list = table_cover_for_nodes.get(node.unique_name).get(node.unique_name)
    full_table_width = 0
    full_table_width += len(node.attribute_list)#width from node itself
    #for strong entity, attribute_list contains all its own attributes including mvd attributes and attributes inherited from parent if entity is a subclass in hierarchy.
    #for strong entity, its attribute_list fully define the entity

    #For weak entity only, additional attributes added from depending parents until a strong parent found - so far only weak entity's own attributes including mvds only added - need to
    #add attributes from depending parents
    if node.is_weak_entity:
        assert node.is_all_by_itself#since weak entity is a participating entity in the relationship
                                    #or a parent to another weak entity which is folded in the parent, it has to be all by itself
        depending_entities = []
        get_dependent_entities_for_weak_entity(graph, node, depending_entities)
        for depending_node_name in depending_entities:
            depending_node = graph.get_node_by_name(depending_node_name)
            for attribute in depending_node.attribute_list:
                if "pk_name" in attribute:#pk columns from dependeing entity are already added in node to define node's pk
                    continue
                else:
                    assert "name" in attribute#add the no of additionally added columns - which have to be non-pk columns
                    full_table_width += 1#for each additionally added attribute, a column is added

    return full_table_width

#find the minimum cover to represent the no_table node - minimum cover consists of immediate contained_all_descendants/all_by_itself children - these children may not be at the same level in hierarchy because
#some immediate children may be no table as well, then have to traverse down until child node cover is found to cover that branch
#for no table node - immediate children can be only contained_all_descendants, all by itself or no table
def find_all_by_itself_children_for_no_table_node(node, children_list):
    for child in node.children:
        if child.is_contained_all_descendants:
            children_list.append(child.unique_name)
        elif child.is_all_by_itself:#simply add the child for all by itself and stop exploring down the branch
                                            #later handle for non-leaf(view required for full tuple coverage) vs leaf(view not required)
            children_list.append(child.unique_name)
        else:# then it has to be a no_table as well - can't be partially by itself or contained in parent
            #if child is a no_table, add the children list(all_by_itself) representing that child
            assert child.is_no_table  #no table
            assert child.mapped_table is None
            find_all_by_itself_children_for_no_table_node(child, children_list)


#folded_node could be a folded relationship or weak entity
#entity_node is the entity in which relationship or weak entity is folded. For relationship, that is the many side entity.
#join cost to build entity in which relationship is folded starting from left table as the entity's mapped table, but table size is only relationship size
#join cost to build entity in which weak entity is folded starting from left table as the entity's mapped table, but table size is only tuples with non-zero array length for
#folded weak entity
#entity_node is distributed in node cover
#cost to generate each union table in the view - mvd joins and other joins if a node in node cover is PBI or CIP - scan cost not included since each union table will be scanned later
#when joining with one side for folded relationship/when unfolding weak entity
def calculate_cost_for_folded_node_associated_with_node_distributed_in_node_cover_helper(graph, folded_node, entity_node, config, tables_dict, table_widths,
                                                                                         folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15):
    total_join_cost = 0
    no_of_unions = 0
    if folded_node.is_relationship():
        #probability that many_side_entity tuple participates in relationship
        #Folded relationship is many-to-one. Each entity tuple(many side) can participate at most once per relationship tuple. Hence no of entity tuples which participate in
        #relationship is equal to relationship size - means no duplicated entity tuples
        no_of_entity_node_tuple_participates = folded_node.relation_size
        probability_that_entity_node_tuple_participates = no_of_entity_node_tuple_participates / entity_node.relation_size#assume uniform participation rate
        assert probability_that_entity_node_tuple_participates <= 1 #since relationship_node.relation_size can be only entity_node.relation_size at most
        #since only single tuple from relationship per many side entity tuple at most
    else:
        assert folded_node.is_entity() and folded_node.is_weak_entity
        avg_no_of_entity_tuples_with_atleast_one_weak_entity_tuple = entity_node.relation_size * (1 - (1 - 1.0/entity_node.relation_size)**folded_node.relation_size)
        #probability that entity tuple has non-zero length array for folded weak entity
        probability_that_entity_node_tuple_participates = avg_no_of_entity_tuples_with_atleast_one_weak_entity_tuple / entity_node.relation_size#assume uniform participation rate

    node_relevant_attributes = [attribute["pk_name"] if "pk_name" in attribute else attribute["name"] for attribute in entity_node.attribute_list]
    created_mvd_tables_attribute_name = []
    for node_cover_node_name in entity_node.node_cover:#node_cover contains node itself and any contained_all_descendants/all child nodes in the subtree rooted at node
        node_cover_node = graph.get_node_by_name(node_cover_node_name)
        if node_cover_node.unique_name != entity_node.unique_name:
            #if node_cover_node is not node itself, per node_cover_node cost in node_cover is the cost to join node_cover_node.mapped_table with all relevant mvd tables
            assert node_cover_node.is_contained_all_descendants or node_cover_node.is_all_by_itself
            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
            participating_tuples_from_node_cover_node = probability_that_entity_node_tuple_participates * node_cover_node_table_size
            node_cover_node_table_width = table_widths.get(node_cover_node.mapped_table[1])
            node_cover_node_table_width = 1#table width not required, modified back to consider only tuple count with added weight for folded weak entity/relationship
            node_cover_node_table_size *= node_cover_node_table_width
            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
            node_cover_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
            participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
            node_cover_node_sorted = False

            for attribute in node_cover_node.attribute_list:
                if "pk_name" in attribute:
                    continue
                else:
                    assert "name" in attribute
                    attr_name = attribute["name"]
                    attr_unique_name = attribute["unique_name"]
                    attribute_node = graph.get_node_by_name(attr_unique_name)
                    #child node contains own mvds and all top parent mvds - need to filter mvds relevant to node(which is a parent)
                    if attribute_node.is_multivalued and attribute_node.is_in_separate_table and attr_name in node_relevant_attributes:#get relevant mvds in separate tables
                        if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                            #with clause for aggrgated mvd table is required to build only once
                            is_mvd_aggregated_table_built = True
                        else:#need to create aggregated mvd table by pk
                            is_mvd_aggregated_table_built = False
                            created_mvd_tables_attribute_name.append(attr_name)
                        #left size is node_cover_node_table_size
                        #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                        total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, participating_tuples_from_node_cover_node,
                                                                    node_cover_node_sorted, is_mvd_aggregated_table_built)
                        node_cover_node_sorted = True
            no_of_unions += 1
        else:
            assert node_cover_node.unique_name == entity_node.unique_name#node itself - node could be all/contained/partial
            assert not node_cover_node.is_contained_all_descendants#cannot be contained_all_descendants since its len(node_cover)>1
            #if node_cover_node is node itself, per node_cover_node cost in node_cover is the cost to join node_cover_node.mapped_table with all relevant mvd tables and other joins
            #based on node is CIP or PBI
            if config[node_cover_node.unique_name] == "all_by_itself":
                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                participating_tuples_from_node_cover_node = probability_that_entity_node_tuple_participates * node_cover_node_table_size
                node_cover_node_table_width = table_widths.get(node_cover_node.mapped_table[1])
                node_cover_node_table_width = 1
                node_cover_node_table_size *= node_cover_node_table_width
                node_cover_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                node_cover_node_sorted = False
                for attribute in node_cover_node.attribute_list:
                    if "pk_name" in attribute:
                        continue
                    else:
                        assert "name" in attribute
                        attr_name = attribute["name"]
                        attr_unique_name = attribute["unique_name"]
                        attribute_node = graph.get_node_by_name(attr_unique_name)
                        #no need to filter mvds since it is the node itself - all mvds relevant
                        if attribute_node.is_multivalued and attribute_node.is_in_separate_table:
                            assert attr_name in node_relevant_attributes
                            if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                                #with clause for aggrgated mvd table is required to build only once
                                is_mvd_aggregated_table_built = True
                            else:#need to create aggregated mvd table by pk
                                is_mvd_aggregated_table_built = False
                                created_mvd_tables_attribute_name.append(attr_name)
                            #left size is node_cover_node_table_size
                            #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                            total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, participating_tuples_from_node_cover_node,
                                                                        node_cover_node_sorted, is_mvd_aggregated_table_built)
                            node_cover_node_sorted = True
                            node_cover_node_table_width += 1#for each joined mvd, a column is added
                assert tables_dict.get(node_cover_node.mapped_table[1])[0] < node_cover_node.relation_size#due to contained_all_descendants or all_by_itself children
                #in the subtree rooted under node_cover_node
                no_of_unions += 1
            elif config[node_cover_node.unique_name] == "contained_in_parent":#parent of node also can be contained_all_descendants, all_by_itself, partially_by_itself, or contained_in_parent
                #first filter for node tuples before all joins
                table_list = table_cover_for_nodes.get(node_cover_node.unique_name).get(node_cover_node.unique_name)
                table_list.sort(key=lambda x: x[0], reverse=True)
                relevant_node_cover_node_tuples_in_mapped_table = node_cover_node.relation_size
                relevant_node_cover_node_tuples_in_mapped_table = find_mapped_table_size_for_materialized_node(graph, config, node_cover_node,
                                                                                                               relevant_node_cover_node_tuples_in_mapped_table)#modify node size to remove tuples from
                #contained_all_descendants or all children in subtree rooted by node
                #filter for node tuples - hence left size is (node.relation_size - all tuples from contained_all_descendants/all child in subtree rooted by node(not tables_dict.get(node.mapped_table[1])[0]))
                participating_tuples_from_node_cover_node = probability_that_entity_node_tuple_participates * relevant_node_cover_node_tuples_in_mapped_table
                node_mapped_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                node_mapped_table_width = table_widths.get(node_cover_node.mapped_table[1])
                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                node_mapped_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                total_join_cost += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - considered # of tuples instead of area
                node_mapped_table_width = 1
                relevant_node_cover_node_tuples_in_mapped_table *= node_mapped_table_width
                relevant_node_cover_node_tuples_in_mapped_table *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                node_cover_node_sorted = False
                #mvd joins of node - mvds(from itself or from parents) can be in separate tables even if node is contained in parent
                for attribute in node_cover_node.attribute_list:
                    if "pk_name" in attribute:
                        continue
                    else:
                        assert "name" in attribute
                        attr_name = attribute["name"]
                        attr_unique_name = attribute["unique_name"]
                        attribute_node = graph.get_node_by_name(attr_unique_name)
                        #no need to filter mvds since it is the node itself - all mvds relevant
                        if attribute_node.is_multivalued and attribute_node.is_in_separate_table:
                            assert attr_name in node_relevant_attributes
                            if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                                #with clause for aggrgated mvd table is required to build only once
                                is_mvd_aggregated_table_built = True
                            else:#need to create aggregated mvd table by pk
                                is_mvd_aggregated_table_built = False
                                created_mvd_tables_attribute_name.append(attr_name)
                            #left size is node_cover_node_table_size
                            #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                            total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, participating_tuples_from_node_cover_node,
                                                                        node_cover_node_sorted, is_mvd_aggregated_table_built)
                            node_cover_node_sorted = True
                            node_mapped_table_width += 1#for each joined mvd, a column is added
                if len(table_list) > 1:
                    no_of_joins = 0
                    for i in range(len(table_list)):
                        table_node = graph.get_node_by_sort_key(table_list[i][0])
                        assert table_node.unique_name != node_cover_node.unique_name#since node is contained in parent, any table's sort key shouldn't be equal to entity - non-materialized option for entity
                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                            #calculate_total_mvd_table_cost_for_node
                            assert table_node.mapped_table == table_list[i]
                            continue
                        elif table_list[i] == node_cover_node.mapped_table:#table in which node is contained is skipped
                            continue
                        else:
                            table_size = tables_dict.get(table_list[i][1])[0]
                            table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                            assert table_size==table_distinct_keys
                            table_width = 1#table_widths.get(table_list[i][1])
                            table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            total_join_cost += sort_merge_join_cost(participating_tuples_from_node_cover_node, table_size) if (no_of_joins < 1 and not node_cover_node_sorted) else \
                                (sort_merge_join_cost(relevant_node_cover_node_tuples_in_mapped_table, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                            #doesn't consider the increased table width after join - left_table_size assumed to be remained same - actually only # of tuples remains the same - width increases
                            #node mapped table can be coming from a parent(may not be immediate parent since parents also can be contained in parent) - contained_all_descendants/all by itself/partially by itself,
                            no_of_joins += 1
                            node_mapped_table_width += (table_width - 1) #for each joined table, except for key columns are added
                no_of_unions += 1
            else:
                assert config[node_cover_node.unique_name] == "partially_by_itself"#parent of node also can be contained_all_descendants, all_by_itself, partially_by_itself, or contained_in_parent
                table_list = table_cover_for_nodes.get(node_cover_node.unique_name).get(node_cover_node.unique_name)
                table_list.sort(key=lambda x: x[0], reverse=True)
                node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]#start from node itself
                participating_tuples_from_node_cover_node = probability_that_entity_node_tuple_participates * node_cover_node_table_size
                node_cover_node_table_width = table_widths.get(node_cover_node.mapped_table[1])
                node_cover_node_table_width = 1
                node_cover_node_table_size *= node_cover_node_table_width #for cost estimation - consider area as the table size
                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                node_cover_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                node_cover_node_sorted = False#assume node is not sorted
                #if node has mvds in separate tables - aggregation, pk-fk join
                for attribute in node_cover_node.attribute_list:
                    if "pk_name" in attribute:
                        continue
                    else:
                        assert "name" in attribute
                        attr_name = attribute["name"]
                        attr_unique_name = attribute["unique_name"]
                        attribute_node = graph.get_node_by_name(attr_unique_name)
                        #no need to filter mvds since it is the node itself - all mvds relevant
                        if attribute_node.is_multivalued and attribute_node.is_in_separate_table:
                            assert attr_name in node_relevant_attributes
                            if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                                #with clause for aggrgated mvd table is required to build only once
                                is_mvd_aggregated_table_built = True
                            else:#need to create aggregated mvd table by pk
                                is_mvd_aggregated_table_built = False
                                created_mvd_tables_attribute_name.append(attr_name)
                            #left size is node_cover_node_table_size
                            #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                            total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, participating_tuples_from_node_cover_node,
                                                                        node_cover_node_sorted, is_mvd_aggregated_table_built)
                            node_cover_node_sorted = True
                            node_cover_node_table_width += 1#for each joined mvd, a column is added
                assert len(table_list) > 1#for partially by itself node - joins are mandatory - irrespective of mvds present or not - atleast should join with 1 parent table
                if len(table_list) > 1:
                    no_of_joins = 0
                    for i in range(len(table_list)):
                        table_node = graph.get_node_by_sort_key(table_list[i][0])
                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                            #calculate_total_mvd_table_cost_for_node
                            assert table_node.mapped_table == table_list[i]
                            continue
                        elif table_node.unique_name == node_cover_node.unique_name:#table of node itself is skipped
                            continue
                        else:
                            #joins with tables - coming from parent nodes(parent nodes could be contained_in_parent/partially_by_itself) until immediate all by itself parent in cover for node
                            #no need to consider mvd join cost since all relevant mvd tables cost is already included
                            table_size = tables_dict.get(table_list[i][1])[0]
                            table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                            assert table_size==table_distinct_keys
                            table_width = 1#table_widths.get(table_list[i][1])
                            table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            #if mvd joins happened for left or after first join with a node(after first join with a node in table_list) - left is sorted
                            total_join_cost += sort_merge_join_cost(participating_tuples_from_node_cover_node, table_distinct_keys) if (no_of_joins < 1 and not node_cover_node_sorted) else \
                                (sort_merge_join_cost(node_cover_node_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                            no_of_joins += 1
                            node_cover_node_table_width += (table_width - 1) #for each joined table, except for key columns are added
                assert tables_dict.get(node_cover_node.mapped_table[1])[0] < node_cover_node.relation_size#due to contained_all_descendants or all_by_itself children
                no_of_unions += 1
    assert no_of_unions == len(entity_node.node_cover)
    return total_join_cost


#folded_node is a folded weak entity or relationship.
#entity_node is the entity in which weak entity or relationship is folded
#join cost to build entity in which weak entity/relationship is folded starting from left table as the entity's mapped table,
#but left table size is only relationship size(that is no of entity tuples in the table with not null value for relationship) or
#for folded weak entity, left table size is the no of entity tuples having non-zero length for folded weak entity array
#entity_node is the entity in which relationship/weak entity is folded
#no node cover for entity_node
#cost to generate the table - mvd joins and other joins if the node is PBI or CIP - scan cost not included since each union table will be scanned later when joining with one side for relationship
def calculate_cost_for_folded_node_associated_with_node_not_distributed_in_node_cover_helper(graph, folded_node, entity_node, left_table_size, config, tables_dict, table_widths,
                                                                                             folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15):
    total_join_cost = 0
    if ((entity_node.is_entity() and config[entity_node.unique_name]=="all_by_itself" and not entity_node.is_weak_entity and len(entity_node.children)==0) or#strong entity - non-hierarchy with all by itself
            (entity_node.is_entity() and config[entity_node.unique_name]=="all_by_itself" and len(entity_node.node_cover)==1) or #hierarchy node with node cover of only itself- node.mapped_table and mvd tables fully define node
            (entity_node.is_entity() and config[entity_node.unique_name]=="contained_all_descendants")):#hierarchy node with contained_all_descendants - node.mapped_table and mvd tables fully define node
        total_join_cost = 0
        #mvd joins of node - mvds(from itself or from parents)
        total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, entity_node, left_table_size, True)
    elif entity_node.is_entity() and len(entity_node.node_cover)>0:#defined for all nodes in inheritance hierarchy
        assert len(entity_node.children)>0 or entity_node.is_subclass#root or subclass
        if len(entity_node.node_cover)==1:#only node itself - node itself contains all tuples - node is not distributed in node_cover - no contained_all_descendants/all child nodes in subtree rooted at node - no unions
            #contained_all_descendants node with no node_cover and leaf all_by_itself node with no node_cover is already handled
            #node can be partial/contained in parent/non-leaf all by itself - if all by itself only mvd joins happening
            assert config[entity_node.unique_name] == "partially_by_itself" or config[entity_node.unique_name] == "contained_in_parent" or config[entity_node.unique_name] == "all_by_itself"
            if config[entity_node.unique_name] == "contained_in_parent":#parent of node also can be all_by_itself, partially_by_itself, contained_in_parent, or contained_all_descendants
                #first filter for node tuples before all joins
                table_list = table_cover_for_nodes.get(entity_node.unique_name).get(entity_node.unique_name)
                table_list.sort(key=lambda x: x[0], reverse=True)
                total_join_cost = 0
                node_sorted = False
                #mvd joins of node - mvds(from itself or from parents) can be in separate tables even if node is contained in parent
                total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, entity_node, left_table_size, node_sorted)
                if len(table_list) > 1:
                    no_of_joins = 0
                    for i in range(len(table_list)):
                        table_node = graph.get_node_by_sort_key(table_list[i][0])
                        assert table_node.unique_name != entity_node.unique_name#since node is contained in parent, any table's sort key shouldn't be equal to entity - non-materialized option for entity
                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                            #calculate_total_mvd_table_cost_for_node
                            assert table_node.mapped_table == table_list[i]
                            continue
                        elif table_list[i] == entity_node.mapped_table:#table in which node is contained is skipped
                            continue
                        else:
                            table_size = tables_dict.get(table_list[i][1])[0]
                            table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                            assert table_size==table_distinct_keys
                            table_width = 1#table_widths.get(table_list[i][1])
                            table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            total_join_cost += sort_merge_join_cost(left_table_size, table_size) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                            #doesn't consider the increased table width after join - left_table_size assumed to be remained same - actually only # of tuples remains the same - width increases
                            #node mapped table can be coming from a parent(may not be immediate parent since parents also can be contained in parent) - all by itself or partially by itself,
                            no_of_joins += 1
            elif config[entity_node.unique_name] == "partially_by_itself":
                table_list = table_cover_for_nodes.get(entity_node.unique_name).get(entity_node.unique_name)
                table_list.sort(key=lambda x: x[0], reverse=True)
                assert tables_dict.get(entity_node.mapped_table[1])[0] == entity_node.relation_size
                total_join_cost = 0
                node_sorted = False#assume node is not sorted
                #if node has mvds in separate tables - aggregation, pk-fk join
                total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, entity_node, left_table_size, node_sorted)
                assert len(table_list) > 1#for partially by itself node - joins are mandatory - irrespective of mvds present or not - atleast should join with 1 parent table
                if len(table_list) > 1:
                    no_of_joins = 0
                    for i in range(len(table_list)):
                        table_node = graph.get_node_by_sort_key(table_list[i][0])
                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                            #calculate_total_mvd_table_cost_for_node
                            assert table_node.mapped_table == table_list[i]
                            continue
                        elif table_node.unique_name == entity_node.unique_name:#table of node itself is skipped
                            continue
                        else:
                            #joins with tables - coming from parent nodes(parent nodes could be contained_in_parent/partially_by_itself) until immediate all by itself parent in cover for node
                            #no need to consider mvd join cost since all relevant mvd tables cost is already included
                            table_size = tables_dict.get(table_list[i][1])[0]
                            table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                            assert table_size==table_distinct_keys
                            table_width = 1#table_widths.get(table_list[i][1])
                            table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            #if mvd joins happened for left or after first join with a node(after first join with a node in table_list) - left is sorted
                            total_join_cost += sort_merge_join_cost(left_table_size, table_distinct_keys) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                            no_of_joins += 1
            #all by itself already covered with in the very first condition
    else:
        assert entity_node.is_weak_entity and config[entity_node.unique_name] == "all_by_itself"
        depending_entities = []
        get_dependent_entities_for_weak_entity(graph, entity_node, depending_entities)
        table_list = table_cover_for_nodes.get(entity_node.unique_name).get(entity_node.unique_name)
        table_list.sort(key=lambda x: x[0], reverse=True) #list is sorted to join from the lowest to top by node sort key
        total_join_cost = 0
        node_sorted = False#assume node is not sorted
        #if leftmost table has mvds in separate tables - aggregation, pk-fk join
        total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, entity_node, left_table_size, node_sorted)
        assert len(table_list) > 1#have to join with a depending entity
        if len(table_list) > 1:#if tables exist to join apart from own mapped table
            no_of_joins = 0

            assert depending_entities[0] == entity_node.parent_entity.unique_name
            for depending_node_name in depending_entities:#depending_entities in the list order first node's immediate parent, then parent's parent if parent also weak
                #until a strong parent is reached - only 1 strong entity can exist in depending_entities list
                depending_node = graph.get_node_by_name(depending_node_name)
                if len(depending_node.children)>0 or depending_node.is_subclass:#root or subclass - depending_node belonging to an inheritance hierarchy
                    if len(depending_node.node_cover) > 1:#depending_node distributed in node_cover - need table view for full representation
                        #all mvds are aggregated in view - view contains full representations
                        depending_node_view_name = "temp_" + depending_node.unique_name
                        assert depending_node_view_name in [table_list[i][1] for i in range(len(table_list))]
                        """
                        assert depending_node.unique_name in node_cost
                        total_join_cost += node_cost[depending_node.unique_name]#cost to build the table view
                        table_view_size = get_union_table_view_size_for_node_distributed_in_node_cover(graph, depending_node, tables_dict, table_widths)
                        #for cost calculation - area = # of tuple * table width is considered
                        #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                        total_join_cost += sort_merge_join_cost(left_table_size, table_view_size) if (no_of_joins < 1 and not node_sorted) else \
                            (sort_merge_join_cost(left_table_size, table_view_size, left_sorted=True))#assume after first join left is sorted
                        """
                        #taking weak entity mapped table filtered for relationship tuples as the left table, each union table from node cover of depending node
                        #gets inl join cost with left table
                        total_join_cost += calculate_cost_for_node_associated_with_node_distributed_in_node_cover_helper(graph, depending_node, left_table_size,
                                                                                                                         config, tables_dict, table_widths, folded_weak_entity_relationship_count,
                                                                                                                         per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
                        no_of_joins += 1
                    else:#depending node not distributed in node_cover - mapped table contains all relevant tuples for depending_node
                        assert len(depending_node.node_cover)==1
                        if config[depending_node.unique_name] == "all_by_itself" or config[depending_node.unique_name]=="contained_all_descendants":
                            depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                            depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                            depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                            depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                            total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                            #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                            #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                            #after previous join with left, assume sorted
                            #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                            total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                            no_of_joins += 1
                        elif config[depending_node.unique_name] == "partially_by_itself":
                            assert tables_dict.get(depending_node.mapped_table[1])[0] == depending_node.relation_size
                            depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                            depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                            depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                            depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                            total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                            #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                            #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                            #after previous join with left, assume sorted
                            #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                            total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                            no_of_joins += 1
                            #since depending node is partially by itself need to gather full attribute list for depending node from parent tables
                            depending_node_table_list = table_cover_for_nodes.get(depending_node.unique_name).get(depending_node.unique_name)
                            depending_node_table_list.sort(key=lambda x: x[0], reverse=True)
                            assert len(depending_node_table_list) > 1#for partially by itself depending_node - joins are mandatory - irrespective of mvds present or not - atleast should join with 1 parent table
                            if len(depending_node_table_list) > 1:
                                for i in range(len(depending_node_table_list)):
                                    table_node = graph.get_node_by_sort_key(depending_node_table_list[i][0])
                                    if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                                        #calculate_total_mvd_table_cost_for_node
                                        assert table_node.mapped_table == depending_node_table_list[i]
                                        continue
                                    elif table_node.unique_name == depending_node.unique_name:#table of depending_node itself is skipped
                                        continue
                                    else:
                                        #joins with tables - coming from parent nodes(parent nodes could be contained_in_parent/partially_by_itself) until immediate all by itself parent in cover for depending node
                                        #no need to consider mvd join cost since all relevant mvd tables cost is already included
                                        table_size = tables_dict.get(depending_node_table_list[i][1])[0]
                                        table_distinct_keys = tables_dict.get(depending_node_table_list[i][1])[1]
                                        assert table_size==table_distinct_keys
                                        table_width = table_widths.get(depending_node_table_list[i][1])
                                        table_size *= 1#table_width #for cost calculation - area = # of tuple * table width is considered
                                        no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node_table_list[i][1], 0)
                                        table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                        #if mvd joins happened for left or after first join with a node(after first join with a node in table_list) - left is sorted
                                        total_join_cost += sort_merge_join_cost(left_table_size, table_size) if (no_of_joins < 1 and not node_sorted) else \
                                            (sort_merge_join_cost(left_table_size, table_size, left_sorted=True))#assume after first join left is sorted
                                        no_of_joins += 1
                        else:
                            assert config[depending_node.unique_name] == "contained_in_parent"
                            depending_node_mapped_table_size = tables_dict.get(depending_node.mapped_table[1])[0]
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                            depending_node_mapped_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            total_join_cost += scan_cost(depending_node_mapped_table_size)#scan cost to filter for depending node tuples - considered # of tuples instead of area
                            depending_node_table_size = depending_node.relation_size#filter for depending_node tuples - hence left size is depending_node.relation_size not tables_dict.get(depending_node.mapped_table[1])[0]
                            depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                            depending_node_table_size *= 1#depending_node_table_width
                            depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                            total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                            #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                            #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                            #after previous join with left, assume sorted
                            #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                            total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                            no_of_joins += 1
                            #depending_node is contained in parent - might have joins with top anscestor tables
                            depending_node_table_list = table_cover_for_nodes.get(depending_node.unique_name).get(depending_node.unique_name)
                            depending_node_table_list.sort(key=lambda x: x[0], reverse=True)
                            if len(depending_node_table_list) > 1:
                                for i in range(len(depending_node_table_list)):
                                    table_node = graph.get_node_by_sort_key(depending_node_table_list[i][0])
                                    assert table_node.unique_name != depending_node.unique_name#since node is contained in parent, any table's sort key shouldn't be equal to entity - non-materialized option for entity
                                    if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                                        #calculate_total_mvd_table_cost_for_node
                                        assert table_node.mapped_table == depending_node_table_list[i]
                                        continue
                                    elif depending_node_table_list[i] == depending_node.mapped_table:#table in which depending_node is contained is skipped
                                        continue
                                    else:
                                        table_size = tables_dict.get(depending_node_table_list[i][1])[0]
                                        table_distinct_keys = tables_dict.get(depending_node_table_list[i][1])[1]
                                        assert table_size==table_distinct_keys
                                        table_width = table_widths.get(depending_node_table_list[i][1])
                                        table_size *= 1#table_width #for cost calculation - area = # of tuple * table width is considered
                                        no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node_table_list[i][1], 0)
                                        table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                        total_join_cost += sort_merge_join_cost(left_table_size, table_size) if (no_of_joins < 1 and not node_sorted) else \
                                            (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                                        #doesn't consider the increased table width after join - left_table_size assumed to be remained same - actually only # of tuples remains the same - width increases
                                        #node mapped table can be coming from a parent(may not be immediate parent since parents also can be contained in parent) - all by itself or partially by itself,
                                        no_of_joins += 1
                elif depending_node.is_weak_entity:
                    assert config[depending_node.unique_name] == "all_by_itself"#if a depending parent is also a weak entity - that parent has to all by itself not folded
                    depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                    depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                    depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                    no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                    depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                    #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                    total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                        (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                    #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                    #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                    #after previous join with left, assume sorted
                    #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                    total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                    no_of_joins += 1
                else:
                    assert depending_node.is_entity and not (len(depending_node.children) > 0 or depending_node.is_subclass)#depending node is a regular entity not belonging to a hierarchy
                    assert config[depending_node.unique_name] == "all_by_itself"#regular strong entity
                    depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                    depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                    depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                    no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                    depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                    #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                    total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                        (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                    #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                    #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                    #after previous join with left, assume sorted
                    #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                    total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                    no_of_joins += 1

    return total_join_cost

#relationship is all_by_itself
#join cost for each participating two entities starting with left table as the relationship mapped table
#entity_node is a participating entity for relationship - entity node could be a hierarchy entity not distributed in node cover, regular entity, or weak entity
def calculate_cost_for_relationship_associated_with_node_not_distributed_in_node_cover_helper(graph, relationship_node, entity_node, left_table_size,
                                           config, tables_dict, table_widths,
                                           folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15):
    #when associated entity_node not distributed in node_cover, left_table which is the relationship's mapped table is taken as the starting point for joins, resultant
    #of all joins are only size of left_table
    total_join_cost = 0
    if ((entity_node.is_entity() and config[entity_node.unique_name]=="all_by_itself" and not entity_node.is_weak_entity and len(entity_node.children)==0) or#strong entity - non-hierarchy with all by itself
       (entity_node.is_entity() and config[entity_node.unique_name]=="all_by_itself" and len(entity_node.node_cover)==1) or #hierarchy node with node cover of only itself- node.mapped_table and mvd tables fully define node
       (entity_node.is_entity() and config[entity_node.unique_name]=="contained_all_descendants")):#hierarchy node with contained_all_descendants - node.mapped_table and mvd tables fully define node
        table_list = table_cover_for_nodes.get(relationship_node.unique_name).get(entity_node.unique_name)
        table_list.sort(key=lambda x: x[0], reverse=True) #list is sorted to join from the lowest to top by node sort key
        entity_node_table_size = tables_dict.get(entity_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the relationshio node itself - doesn't consider
        entity_node_table_width = table_widths.get(entity_node.mapped_table[1])    #the table width that gets increased at each join step - assume left table size(tuples * width) remains the same
        entity_node_table_width = 1#table width not required, modified back to consider only tuple count with added weight for folded weak entity/relationship
        entity_node_table_size *= entity_node_table_width #for cost estimation - consider area as the table size
        #add weight for every folded weak entity/relationship contained in the table - a tuple weighs additionally
        #no of folded weak entity/relationships times the set weight for per tuple
        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(entity_node.mapped_table[1], 0)#defaults to 0
        entity_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
        total_join_cost = 0
        total_join_cost += sort_merge_join_cost(left_table_size, entity_node_table_size)
        total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, entity_node, left_table_size, True)
    elif entity_node.is_entity() and len(entity_node.node_cover)>0:#defined for all nodes in inheritance hierarchy
        assert len(entity_node.children)>0 or entity_node.is_subclass#root or subclass
        if len(entity_node.node_cover)==1:#only node itself - node itself contains all tuples - node is not distributed in node_cover - no contained_all_descendants/all child nodes in subtree rooted at node - no unions
        #contained_all_descendants node with no node_cover and leaf all_by_itself node with no node_cover is already handled
        #node can be partial/contained in parent/non-leaf all by itself - if all by itself only mvd joins happening
            assert config[entity_node.unique_name] == "partially_by_itself" or config[entity_node.unique_name] == "contained_in_parent" or config[entity_node.unique_name] == "all_by_itself"
            if config[entity_node.unique_name] == "contained_in_parent":#parent of node also can be all_by_itself, partially_by_itself, contained_in_parent, or contained_all_descendants
                #first filter for node tuples before all joins
                table_list = table_cover_for_nodes.get(relationship_node.unique_name).get(entity_node.unique_name)
                table_list.sort(key=lambda x: x[0], reverse=True)
                entity_node_table_size = entity_node.relation_size#filter for node tuples - hence left size is node.relation_size not tables_dict.get(node.mapped_table[1])[0]
                node_mapped_table_size = tables_dict.get(entity_node.mapped_table[1])[0]
                node_mapped_table_width = table_widths.get(entity_node.mapped_table[1])
                node_mapped_table_width = 1
                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(entity_node.mapped_table[1], 0)
                node_mapped_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                total_join_cost = 0
                node_sorted = False
                total_join_cost += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - considered # of tuples instead of area
                entity_node_table_size *= node_mapped_table_width
                entity_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                total_join_cost += sort_merge_join_cost(left_table_size, entity_node_table_size)
                #mvd joins of node - mvds(from itself or from parents) can be in separate tables even if node is contained in parent
                total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, entity_node, left_table_size, node_sorted)
                if len(table_list) > 1:
                    no_of_joins = 0
                    for i in range(len(table_list)):
                        table_node = graph.get_node_by_sort_key(table_list[i][0])
                        assert table_node.unique_name != entity_node.unique_name#since node is contained in parent, any table's sort key shouldn't be equal to entity - non-materialized option for entity
                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                            #calculate_total_mvd_table_cost_for_node
                            assert table_node.mapped_table == table_list[i]
                            continue
                        elif table_list[i] == entity_node.mapped_table:#table in which node is contained is skipped
                            continue
                        else:
                            table_size = tables_dict.get(table_list[i][1])[0]
                            table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                            assert table_size==table_distinct_keys
                            table_width = 1#table_widths.get(table_list[i][1])
                            table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            total_join_cost += sort_merge_join_cost(left_table_size, table_size) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                            #doesn't consider the increased table width after join - left_table_size assumed to be remained same - actually only # of tuples remains the same - width increases
                            #node mapped table can be coming from a parent(may not be immediate parent since parents also can be contained in parent) - all by itself or partially by itself,
                            no_of_joins += 1
            elif config[entity_node.unique_name] == "partially_by_itself":
                table_list = table_cover_for_nodes.get(relationship_node.unique_name).get(entity_node.unique_name)
                table_list.sort(key=lambda x: x[0], reverse=True)
                assert tables_dict.get(entity_node.mapped_table[1])[0] == entity_node.relation_size
                entity_node_table_size = tables_dict.get(entity_node.mapped_table[1])[0]#start from node itself
                entity_node_table_width = 1#table_widths.get(node.mapped_table[1])
                entity_node_table_size *= entity_node_table_width #for cost estimation - consider area as the table size
                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(entity_node.mapped_table[1], 0)
                entity_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                total_join_cost = 0
                node_sorted = False#assume node is not sorted
                total_join_cost += sort_merge_join_cost(left_table_size, entity_node_table_size)
                #if node has mvds in separate tables - aggregation, pk-fk join
                total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, entity_node, left_table_size, node_sorted)
                assert len(table_list) > 1#for partially by itself node - joins are mandatory - irrespective of mvds present or not - atleast should join with 1 parent table
                if len(table_list) > 1:
                    no_of_joins = 0
                    for i in range(len(table_list)):
                        table_node = graph.get_node_by_sort_key(table_list[i][0])
                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                            #calculate_total_mvd_table_cost_for_node
                            assert table_node.mapped_table == table_list[i]
                            continue
                        elif table_node.unique_name == entity_node.unique_name:#table of node itself is skipped
                            continue
                        else:
                            #joins with tables - coming from parent nodes(parent nodes could be contained_in_parent/partially_by_itself) until immediate all by itself parent in cover for node
                            #no need to consider mvd join cost since all relevant mvd tables cost is already included
                            table_size = tables_dict.get(table_list[i][1])[0]
                            table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                            assert table_size==table_distinct_keys
                            table_width = 1#table_widths.get(table_list[i][1])
                            table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            #if mvd joins happened for left or after first join with a node(after first join with a node in table_list) - left is sorted
                            total_join_cost += sort_merge_join_cost(left_table_size, table_distinct_keys) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                            no_of_joins += 1
            #all by itself already covered with in the very first condition
    else:
        assert entity_node.is_weak_entity and config[entity_node.unique_name] == "all_by_itself"
        depending_entities = []
        get_dependent_entities_for_weak_entity(graph, entity_node, depending_entities)
        table_list = table_cover_for_nodes.get(relationship_node.unique_name).get(entity_node.unique_name)
        table_list.sort(key=lambda x: x[0], reverse=True) #list is sorted to join from the lowest to top by node sort key
        entity_node_table_size = tables_dict.get(entity_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself - doesn't consider
        entity_node_table_width = table_widths.get(entity_node.mapped_table[1])    #the table width that gets increased at each join step - assume left table size(tuples * width) remains the same
        entity_node_table_size *= 1#left_table_width #for cost estimation - consider area as the table size
        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(entity_node.mapped_table[1], 0)
        entity_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
        total_join_cost = 0
        node_sorted = False#assume node is not sorted
        total_join_cost += sort_merge_join_cost(left_table_size, entity_node_table_size)
        #if leftmost table has mvds in separate tables - aggregation, pk-fk join
        total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, entity_node, left_table_size, node_sorted)
        assert len(table_list) > 1#have to join with a depending entity
        if len(table_list) > 1:#if tables exist to join apart from own mapped table
            no_of_joins = 0

            assert depending_entities[0] == entity_node.parent_entity.unique_name
            for depending_node_name in depending_entities:#depending_entities in the list order first node's immediate parent, then parent's parent if parent also weak
                #until a strong parent is reached - only 1 strong entity can exist in depending_entities list
                depending_node = graph.get_node_by_name(depending_node_name)
                if len(depending_node.children)>0 or depending_node.is_subclass:#root or subclass - depending_node belonging to an inheritance hierarchy
                    if len(depending_node.node_cover) > 1:#depending_node distributed in node_cover - need table view for full representation
                        #all mvds are aggregated in view - view contains full representations
                        depending_node_view_name = "temp_" + depending_node.unique_name
                        assert depending_node_view_name in [table_list[i][1] for i in range(len(table_list))]
                        """
                        assert depending_node.unique_name in node_cost
                        total_join_cost += node_cost[depending_node.unique_name]#cost to build the table view
                        table_view_size = get_union_table_view_size_for_node_distributed_in_node_cover(graph, depending_node, tables_dict, table_widths)
                        #for cost calculation - area = # of tuple * table width is considered
                        #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                        total_join_cost += sort_merge_join_cost(left_table_size, table_view_size) if (no_of_joins < 1 and not node_sorted) else \
                            (sort_merge_join_cost(left_table_size, table_view_size, left_sorted=True))#assume after first join left is sorted
                        """
                        #each union table from node cover of depending_node gets inl(index nested loop) join cost with left table
                        total_join_cost += calculate_cost_for_node_associated_with_node_distributed_in_node_cover_helper(graph, depending_node, left_table_size,
                                                                                                                         config, tables_dict, table_widths, folded_weak_entity_relationship_count,
                                                                                                                         per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
                        no_of_joins += 1
                    else:#depending node not distributed in node_cover - mapped table contains all relevant tuples for depending_node
                        assert len(depending_node.node_cover)==1
                        if config[depending_node.unique_name] == "all_by_itself" or config[depending_node.unique_name]=="contained_all_descendants":
                            depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                            depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                            depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                            depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                            total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                            #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                            #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                            #after previous join with left, assume sorted
                            #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                            total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                            no_of_joins += 1
                        elif config[depending_node.unique_name] == "partially_by_itself":
                            assert tables_dict.get(depending_node.mapped_table[1])[0] == depending_node.relation_size
                            depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                            depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                            depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                            depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                            total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                            #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                            #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                            #after previous join with left, assume sorted
                            #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                            total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                            no_of_joins += 1
                            #since depending node is partially by itself need to gather full attribute list for depending node from parent tables
                            depending_node_table_list = table_cover_for_nodes.get(depending_node.unique_name).get(depending_node.unique_name)
                            depending_node_table_list.sort(key=lambda x: x[0], reverse=True)
                            assert len(depending_node_table_list) > 1#for partially by itself depending_node - joins are mandatory - irrespective of mvds present or not - atleast should join with 1 parent table
                            if len(depending_node_table_list) > 1:
                                for i in range(len(depending_node_table_list)):
                                    table_node = graph.get_node_by_sort_key(depending_node_table_list[i][0])
                                    if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                                        #calculate_total_mvd_table_cost_for_node
                                        assert table_node.mapped_table == depending_node_table_list[i]
                                        continue
                                    elif table_node.unique_name == depending_node.unique_name:#table of depending_node itself is skipped
                                        continue
                                    else:
                                        #joins with tables - coming from parent nodes(parent nodes could be contained_in_parent/partially_by_itself) until immediate all by itself parent in cover for depending node
                                        #no need to consider mvd join cost since all relevant mvd tables cost is already included
                                        table_size = tables_dict.get(depending_node_table_list[i][1])[0]
                                        table_distinct_keys = tables_dict.get(depending_node_table_list[i][1])[1]
                                        assert table_size==table_distinct_keys
                                        table_width = table_widths.get(depending_node_table_list[i][1])
                                        table_size *= 1#table_width #for cost calculation - area = # of tuple * table width is considered
                                        no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node_table_list[i][1], 0)
                                        table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                        #if mvd joins happened for left or after first join with a node(after first join with a node in table_list) - left is sorted
                                        total_join_cost += sort_merge_join_cost(left_table_size, table_size) if (no_of_joins < 1 and not node_sorted) else \
                                            (sort_merge_join_cost(left_table_size, table_size, left_sorted=True))#assume after first join left is sorted
                                        no_of_joins += 1
                        else:
                            assert config[depending_node.unique_name] == "contained_in_parent"
                            depending_node_mapped_table_size = tables_dict.get(depending_node.mapped_table[1])[0]
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                            depending_node_mapped_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            total_join_cost += scan_cost(depending_node_mapped_table_size)#scan cost to filter for depending node tuples - considered # of tuples instead of area
                            depending_node_table_size = depending_node.relation_size#filter for depending_node tuples - hence left size is depending_node.relation_size not tables_dict.get(depending_node.mapped_table[1])[0]
                            depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                            depending_node_table_size *= 1#depending_node_table_width
                            depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                            total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                            #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                            #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                            #after previous join with left, assume sorted
                            #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                            total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                            no_of_joins += 1
                            #depending_node is contained in parent - might have joins with top anscestor tables
                            depending_node_table_list = table_cover_for_nodes.get(depending_node.unique_name).get(depending_node.unique_name)
                            depending_node_table_list.sort(key=lambda x: x[0], reverse=True)
                            if len(depending_node_table_list) > 1:
                                for i in range(len(depending_node_table_list)):
                                    table_node = graph.get_node_by_sort_key(depending_node_table_list[i][0])
                                    assert table_node.unique_name != depending_node.unique_name#since node is contained in parent, any table's sort key shouldn't be equal to entity - non-materialized option for entity
                                    if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                                        #calculate_total_mvd_table_cost_for_node
                                        assert table_node.mapped_table == depending_node_table_list[i]
                                        continue
                                    elif depending_node_table_list[i] == depending_node.mapped_table:#table in which depending_node is contained is skipped
                                        continue
                                    else:
                                        table_size = tables_dict.get(depending_node_table_list[i][1])[0]
                                        table_distinct_keys = tables_dict.get(depending_node_table_list[i][1])[1]
                                        assert table_size==table_distinct_keys
                                        table_width = table_widths.get(depending_node_table_list[i][1])
                                        table_size *= 1#table_width #for cost calculation - area = # of tuple * table width is considered
                                        no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node_table_list[i][1], 0)
                                        table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                        total_join_cost += sort_merge_join_cost(left_table_size, table_size) if (no_of_joins < 1 and not node_sorted) else \
                                            (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                                        #doesn't consider the increased table width after join - left_table_size assumed to be remained same - actually only # of tuples remains the same - width increases
                                        #node mapped table can be coming from a parent(may not be immediate parent since parents also can be contained in parent) - all by itself or partially by itself,
                                        no_of_joins += 1
                elif depending_node.is_weak_entity:
                    assert config[depending_node.unique_name] == "all_by_itself"#if a depending parent is also a weak entity - that parent has to all by itself not folded
                    depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                    depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                    depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                    no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                    depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                    #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                    total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                        (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                    #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                    #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                    #after previous join with left, assume sorted
                    #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                    total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                    no_of_joins += 1
                else:
                    assert depending_node.is_entity and not (len(depending_node.children) > 0 or depending_node.is_subclass)#depending node is a regular entity not belonging to a hierarchy
                    assert config[depending_node.unique_name] == "all_by_itself"#regular strong entity
                    depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                    depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                    depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                    no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                    depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                    #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                    total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                        (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                    #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                    #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                    #after previous join with left, assume sorted
                    #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                    total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                    no_of_joins += 1

    return total_join_cost

#Looking at Postgres query plan for a query, helps writing an approximate cost model
#e.g. When a view is generated for a node with cover, each table in the union is considered a separate table when joining with other tables

#when a node is distributed in a node cover, each union table from node's node cover nodes does only mvd joins, and node itself may involve with other joins based on node
#is PBI/CIP. Then each such union table is considered a separate table when joining with other nodes.
#e.g. if union tables are size of 100,200,300 and they join with a left_table of size 10 - inl join cost is 10+10*log(100) + 10+10*log(200) + 10+10*log(300)
#if left table is taken as the node distributed in node cover - inl join cost is join cost is 100+100*log(10) + 200+200*log(10) + 300+300*log(10)

#for all_by_itself weak entity with a depending parent entity distributed in a node cover(hierarchy_node) or
#all_by_itself  relationship with participating entity as a node distributed in a node cover(hierarchy_node)
#left_table_size is the weak entity or relationship mapped table size
def calculate_cost_for_node_associated_with_node_distributed_in_node_cover_helper(graph, hierarchy_node, left_table_size, config, tables_dict, table_widths,
                                folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15):
    #when associated hierarchy_node distributed in node_cover, first calculate cost for each union table, then left_table joins with each union table
    total_join_cost = 0
    no_of_unions = 0
    node_relevant_attributes = [attribute["pk_name"] if "pk_name" in attribute else attribute["name"] for attribute in hierarchy_node.attribute_list]
    created_mvd_tables_attribute_name = []
    for node_cover_node_name in hierarchy_node.node_cover:#node_cover contains node itself and any contained_all_descendants/all child nodes in the subtree rooted at node
        node_cover_node = graph.get_node_by_name(node_cover_node_name)
        if node_cover_node.unique_name != hierarchy_node.unique_name:
            #if node_cover_node is not node itself, per node_cover_node cost in node_cover is the cost to join node_cover_node.mapped_table with all relevant mvd tables
            assert node_cover_node.is_contained_all_descendants or node_cover_node.is_all_by_itself
            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
            node_cover_node_table_width = table_widths.get(node_cover_node.mapped_table[1])
            node_cover_node_table_width = 1#table width not required, modified back to consider only tuple count with added weight for folded weak entity/relationship
            node_cover_node_table_size *= node_cover_node_table_width
            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
            node_cover_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
            node_cover_node_sorted = False
            for attribute in node_cover_node.attribute_list:
                if "pk_name" in attribute:
                    continue
                else:
                    assert "name" in attribute
                    attr_name = attribute["name"]
                    attr_unique_name = attribute["unique_name"]
                    attribute_node = graph.get_node_by_name(attr_unique_name)
                    #child node contains own mvds and all top parent mvds - need to filter mvds relevant to node(which is a parent)
                    if attribute_node.is_multivalued and attribute_node.is_in_separate_table and attr_name in node_relevant_attributes:#get relevant mvds in separate tables
                        if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                            #with clause for aggrgated mvd table is required to build only once
                            is_mvd_aggregated_table_built = True
                        else:#need to create aggregated mvd table by pk
                            is_mvd_aggregated_table_built = False
                            created_mvd_tables_attribute_name.append(attr_name)
                        #left size is node_cover_node_table_size
                        #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                        total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, node_cover_node_table_size,
                                                                    node_cover_node_sorted, is_mvd_aggregated_table_built)
                        node_cover_node_sorted = True
            node_cover_node_table_size =  (tables_dict.get(node_cover_node.mapped_table[1])[0] *
                                           (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship))
            total_join_cost += sort_merge_join_cost(left_table_size, node_cover_node_table_size)#left_table joins with each union table from node cover
            no_of_unions += 1
        else:
            assert node_cover_node.unique_name == hierarchy_node.unique_name#node itself - node could be all/contained/partial
            assert not node_cover_node.is_contained_all_descendants#cannot be contained_all_descendants since its len(node_cover)>1
            if config[node_cover_node.unique_name] == "all_by_itself":
                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                node_cover_node_table_width = table_widths.get(node_cover_node.mapped_table[1])
                node_cover_node_table_width = 1
                node_cover_node_table_size *= node_cover_node_table_width
                node_cover_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                node_cover_node_sorted = False
                for attribute in node_cover_node.attribute_list:
                    if "pk_name" in attribute:
                        continue
                    else:
                        assert "name" in attribute
                        attr_name = attribute["name"]
                        attr_unique_name = attribute["unique_name"]
                        attribute_node = graph.get_node_by_name(attr_unique_name)
                        #no need to filter mvds since it is the node itself - all mvds relevant
                        if attribute_node.is_multivalued and attribute_node.is_in_separate_table:
                            assert attr_name in node_relevant_attributes
                            if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                                #with clause for aggrgated mvd table is required to build only once
                                is_mvd_aggregated_table_built = True
                            else:#need to create aggregated mvd table by pk
                                is_mvd_aggregated_table_built = False
                                created_mvd_tables_attribute_name.append(attr_name)
                            #left size is node_cover_node_table_size
                            #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                            total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, node_cover_node_table_size,
                                                                        node_cover_node_sorted, is_mvd_aggregated_table_built)
                            node_cover_node_sorted = True
                            node_cover_node_table_width += 1#for each joined mvd, a column is added
                assert tables_dict.get(node_cover_node.mapped_table[1])[0] < node_cover_node.relation_size#due to contained_all_descendants or all_by_itself children
                #in the subtree rooted under node_cover_node
                node_cover_node_table_size =  tables_dict.get(node_cover_node.mapped_table[1])[0] * 1#node_cover_node_table_width
                node_cover_node_table_size =  (tables_dict.get(node_cover_node.mapped_table[1])[0] *
                                               (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship))
                total_join_cost += sort_merge_join_cost(left_table_size, node_cover_node_table_size)#left_table joins with each union table from node cover
                no_of_unions += 1
            elif config[node_cover_node.unique_name] == "contained_in_parent":#parent of node also can be contained_all_descendants, all_by_itself, partially_by_itself, or contained_in_parent
                #first filter for node tuples before all joins
                table_list = table_cover_for_nodes.get(node_cover_node.unique_name).get(node_cover_node.unique_name)
                table_list.sort(key=lambda x: x[0], reverse=True)
                relevant_node_cover_node_tuples_in_mapped_table = node_cover_node.relation_size
                relevant_node_cover_node_tuples_in_mapped_table = find_mapped_table_size_for_materialized_node(graph, config, node_cover_node,
                                                                                                               relevant_node_cover_node_tuples_in_mapped_table)#modify node size to remove tuples from
                #contained_all_descendants or all children in subtree rooted by node
                #filter for node tuples - hence left size is (node.relation_size - all tuples from contained_all_descendants/all child in subtree rooted by node(not tables_dict.get(node.mapped_table[1])[0]))
                node_mapped_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                node_mapped_table_width = table_widths.get(node_cover_node.mapped_table[1])
                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                node_mapped_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                total_join_cost += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - considered # of tuples instead of area
                node_mapped_table_width = 1
                relevant_node_cover_node_tuples_in_mapped_table *= node_mapped_table_width
                relevant_node_cover_node_tuples_in_mapped_table *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                node_cover_node_sorted = False
                #mvd joins of node - mvds(from itself or from parents) can be in separate tables even if node is contained in parent
                for attribute in node_cover_node.attribute_list:
                    if "pk_name" in attribute:
                        continue
                    else:
                        assert "name" in attribute
                        attr_name = attribute["name"]
                        attr_unique_name = attribute["unique_name"]
                        attribute_node = graph.get_node_by_name(attr_unique_name)
                        #no need to filter mvds since it is the node itself - all mvds relevant
                        if attribute_node.is_multivalued and attribute_node.is_in_separate_table:
                            assert attr_name in node_relevant_attributes
                            if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                                #with clause for aggrgated mvd table is required to build only once
                                is_mvd_aggregated_table_built = True
                            else:#need to create aggregated mvd table by pk
                                is_mvd_aggregated_table_built = False
                                created_mvd_tables_attribute_name.append(attr_name)
                            #left size is node_cover_node_table_size
                            #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                            total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, relevant_node_cover_node_tuples_in_mapped_table,
                                                                        node_cover_node_sorted, is_mvd_aggregated_table_built)
                            node_cover_node_sorted = True
                            node_mapped_table_width += 1#for each joined mvd, a column is added
                if len(table_list) > 1:
                    no_of_joins = 0
                    for i in range(len(table_list)):
                        table_node = graph.get_node_by_sort_key(table_list[i][0])
                        assert table_node.unique_name != node_cover_node.unique_name#since node is contained in parent, any table's sort key shouldn't be equal to entity - non-materialized option for entity
                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                            #calculate_total_mvd_table_cost_for_node
                            assert table_node.mapped_table == table_list[i]
                            continue
                        elif table_list[i] == node_cover_node.mapped_table:#table in which node is contained is skipped
                            continue
                        else:
                            table_size = tables_dict.get(table_list[i][1])[0]
                            table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                            assert table_size==table_distinct_keys
                            table_width = 1#table_widths.get(table_list[i][1])
                            table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            total_join_cost += sort_merge_join_cost(relevant_node_cover_node_tuples_in_mapped_table, table_size) if (no_of_joins < 1 and not node_cover_node_sorted) else \
                                (sort_merge_join_cost(relevant_node_cover_node_tuples_in_mapped_table, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                            #doesn't consider the increased table width after join - left_table_size assumed to be remained same - actually only # of tuples remains the same - width increases
                            #node mapped table can be coming from a parent(may not be immediate parent since parents also can be contained in parent) - contained_all_descendants/all by itself/partially by itself,
                            no_of_joins += 1
                            node_mapped_table_width += (table_width - 1) #for each joined table, except for key columns are added
                full_table_width = node_mapped_table_width#len(node_cover_node.attribute_list)
                relevant_node_cover_node_tuples_in_mapped_table = node_cover_node.relation_size
                relevant_node_cover_node_tuples_in_mapped_table = find_mapped_table_size_for_materialized_node(graph, config, node_cover_node,
                                                                                                               relevant_node_cover_node_tuples_in_mapped_table)#to get
                #node_cover_node tuples in table - requires deducting contained_all_descendants or all children in
                #subtree rooted by node_cover_node from node_cover_node.relation_size
                relevant_node_cover_node_tuples_in_mapped_table *=  1#full_table_width
                relevant_node_cover_node_tuples_in_mapped_table *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                total_join_cost += sort_merge_join_cost(left_table_size, relevant_node_cover_node_tuples_in_mapped_table)#left_table joins with each union table from node cover
                no_of_unions += 1
            else:
                assert config[node_cover_node.unique_name] == "partially_by_itself"#parent of node also can be contained_all_descendants, all_by_itself, partially_by_itself, or contained_in_parent
                table_list = table_cover_for_nodes.get(node_cover_node.unique_name).get(node_cover_node.unique_name)
                table_list.sort(key=lambda x: x[0], reverse=True)
                node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]#start from node itself
                node_cover_node_table_width = table_widths.get(node_cover_node.mapped_table[1])
                node_cover_node_table_width = 1
                node_cover_node_table_size *= node_cover_node_table_width #for cost estimation - consider area as the table size
                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                node_cover_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                node_cover_node_sorted = False#assume node is not sorted
                #if node has mvds in separate tables - aggregation, pk-fk join
                for attribute in node_cover_node.attribute_list:
                    if "pk_name" in attribute:
                        continue
                    else:
                        assert "name" in attribute
                        attr_name = attribute["name"]
                        attr_unique_name = attribute["unique_name"]
                        attribute_node = graph.get_node_by_name(attr_unique_name)
                        #no need to filter mvds since it is the node itself - all mvds relevant
                        if attribute_node.is_multivalued and attribute_node.is_in_separate_table:
                            assert attr_name in node_relevant_attributes
                            if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                                #with clause for aggrgated mvd table is required to build only once
                                is_mvd_aggregated_table_built = True
                            else:#need to create aggregated mvd table by pk
                                is_mvd_aggregated_table_built = False
                                created_mvd_tables_attribute_name.append(attr_name)
                            #left size is node_cover_node_table_size
                            #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                            total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, node_cover_node_table_size,
                                                                        node_cover_node_sorted, is_mvd_aggregated_table_built)
                            node_cover_node_sorted = True
                            node_cover_node_table_width += 1#for each joined mvd, a column is added
                assert len(table_list) > 1#for partially by itself node - joins are mandatory - irrespective of mvds present or not - atleast should join with 1 parent table
                if len(table_list) > 1:
                    no_of_joins = 0
                    for i in range(len(table_list)):
                        table_node = graph.get_node_by_sort_key(table_list[i][0])
                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                            #calculate_total_mvd_table_cost_for_node
                            assert table_node.mapped_table == table_list[i]
                            continue
                        elif table_node.unique_name == node_cover_node.unique_name:#table of node itself is skipped
                            continue
                        else:
                            #joins with tables - coming from parent nodes(parent nodes could be contained_in_parent/partially_by_itself) until immediate all by itself parent in cover for node
                            #no need to consider mvd join cost since all relevant mvd tables cost is already included
                            table_size = tables_dict.get(table_list[i][1])[0]
                            table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                            assert table_size==table_distinct_keys
                            table_width = 1#table_widths.get(table_list[i][1])
                            table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            #if mvd joins happened for left or after first join with a node(after first join with a node in table_list) - left is sorted
                            total_join_cost += sort_merge_join_cost(node_cover_node_table_size, table_distinct_keys) if (no_of_joins < 1 and not node_cover_node_sorted) else \
                                (sort_merge_join_cost(node_cover_node_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                            no_of_joins += 1
                            node_cover_node_table_width += (table_width - 1) #for each joined table, except for key columns are added
                full_table_width = node_cover_node_table_width#len(node_cover_node.attribute_list)
                assert tables_dict.get(node_cover_node.mapped_table[1])[0] < node_cover_node.relation_size#due to contained_all_descendants or all_by_itself children
                #in the subtree rooted under node_cover_node
                node_cover_node_table_size =  tables_dict.get(node_cover_node.mapped_table[1])[0] * 1#full_table_width
                node_cover_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                total_join_cost += sort_merge_join_cost(left_table_size, node_cover_node_table_size)#left_table joins with each union table from node cover
                no_of_unions += 1
    assert no_of_unions == len(hierarchy_node.node_cover)
    return total_join_cost

#single select * statement cost for entity or relationship
def calculate_select_cost_for_single_entity_or_relationship_for_single_query(graph, node, config, tables_dict, table_widths,
                        folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15):
    if node.unique_name in node_cost:
        return node_cost[node.unique_name]

    cost = 0

    if node.is_entity() and config[node.unique_name] == "no_table":
        total_join_cost = 0
        assert len(node.node_cover) > 0
        all_by_itself_children_for_union = []
        find_all_by_itself_children_for_no_table_node(node, all_by_itself_children_for_union)
        #minimum set to cover the entity - these children can be at any level in hierarchy depending on if immediate children are contained_all_descendants, all by itself or no table
        for child_node_name in all_by_itself_children_for_union:
            child_node = graph.get_node_by_name(child_node_name)
            assert child_node.is_contained_all_descendants or child_node.is_all_by_itself
            total_join_cost += calculate_select_cost_for_single_entity_or_relationship_for_single_query(graph,
                                                                                                        child_node, config, tables_dict, table_widths)
        cost += total_join_cost
        node_cost[node.unique_name] = cost
    elif ((node.is_entity() and config[node.unique_name]=="all_by_itself" and not node.is_weak_entity and len(node.children)==0) or#strong entity - non-hierarchy with all by itself -- or leaf hierarchy entity with all by itself
          (node.is_entity() and config[node.unique_name]=="all_by_itself" and len(node.node_cover)==1) or #hierarchy node with node cover of only itself- node.mapped_table and mvd tables fully define node
          (node.is_entity() and config[node.unique_name]=="contained_all_descendants")):#hierarchy node with contained_all_descendants - node.mapped_table and mvd tables fully define node
        table_list = table_cover_for_nodes.get(node.unique_name).get(node.unique_name)
        table_list.sort(key=lambda x: x[0], reverse=True) #list is sorted to join from the lowest to top by node sort key
        left_table_size = tables_dict.get(node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself - doesn't consider
        left_table_width = table_widths.get(node.mapped_table[1])    #the table width that gets increased at each join step - assume left table size(tuples * width) remains the same
        left_table_width = 1#table width not required, modified back to consider only tuple count with added weight for folded weak entity/relationship
        left_table_size *= left_table_width #for cost estimation - consider area as the table size
        #add weight for every folded weak entity/relationship contained in the table - a tuple weighs additionally
        #no of folded weak entity/relationships times the set weight for per tuple
        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node.mapped_table[1], 0)#defaults to 0
        left_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
        total_join_cost = 0
        node_sorted = False#assume node is not sorted
        #if leftmost table has mvds in separate tables - aggregation, pk-fk join
        #since node is a strong entity, only joins possible is mvd tables(own or from parents) for select * query
        total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, node, left_table_size, node_sorted)
        if not len(table_list) > 1:#if no tables exist to join apart from own mapped table - which means no mvd tables
            assert total_join_cost == 0
            if total_join_cost == 0:#no tables were joined - need to count for a scan of relation
                assert node_sorted == False#if mvds present, they should be in array structure
                total_join_cost += scan_cost(left_table_size)
        cost += total_join_cost
        node_cost[node.unique_name] = cost
    elif node.is_entity() and len(node.node_cover)>0:#defined for all nodes in inheritance hierarchy
        assert len(node.children)>0 or node.is_subclass#root or subclass
        if len(node.node_cover)>1:#root/non-leaf subclass distributed in node_cover - union occurs
            #contained_all_descendants/all_by_itself child nodes exist in subtree rooted at node
            #node_cover contains node itself and contained_all_descendants/all child nodes in subtree rooted at node
            assert len(node.children)>0
            node_relevant_attributes = [attribute["pk_name"] if "pk_name" in attribute else attribute["name"] for attribute in node.attribute_list]
            created_mvd_tables_attribute_name = []
            total_join_cost = 0
            no_of_unions = 0
            for node_cover_node_name in node.node_cover:#node_cover contains node itself and any contained_all_descendants/all child nodes in the subtree rooted at node
                node_cover_node = graph.get_node_by_name(node_cover_node_name)
                if node_cover_node.unique_name != node.unique_name:
                    #if node_cover_node is not node itself, per node_cover_node cost in node_cover is the cost to join node_cover_node.mapped_table with all relevant mvd tables
                    #and scan cost to scan the joined full node_cover_node(union step)
                    #each table_view from node_cover_node in node_cover scanned and union-ed to create full table view for node
                    assert node_cover_node.is_contained_all_descendants or node_cover_node.is_all_by_itself
                    node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                    node_cover_node_table_width = table_widths.get(node_cover_node.mapped_table[1])
                    node_cover_node_table_width = 1#table width not required, modified back to consider only tuple count with added weight for folded weak entity/relationship
                    node_cover_node_table_size *= node_cover_node_table_width
                    no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                    node_cover_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                    node_cover_node_sorted = False
                    for attribute in node_cover_node.attribute_list:
                        if "pk_name" in attribute:
                            continue
                        else:
                            assert "name" in attribute
                            attr_name = attribute["name"]
                            attr_unique_name = attribute["unique_name"]
                            attribute_node = graph.get_node_by_name(attr_unique_name)
                            #child node contains own mvds and all top parent mvds - need to filter mvds relevant to node(which is a parent)
                            if attribute_node.is_multivalued and attribute_node.is_in_separate_table and attr_name in node_relevant_attributes:#get relevant mvds in separate tables
                                if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                                    #with clause for aggrgated mvd table is required to build only once
                                    is_mvd_aggregated_table_built = True
                                else:#need to create aggregated mvd table by pk
                                    is_mvd_aggregated_table_built = False
                                    created_mvd_tables_attribute_name.append(attr_name)
                                #left size is node_cover_node_table_size
                                #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                                total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, node_cover_node_table_size,
                                                                            node_cover_node_sorted, is_mvd_aggregated_table_built)
                                node_cover_node_sorted = True
                                node_cover_node_table_width += 1#for each joined mvd, a column is added
                    node_cover_node_table_size =  tables_dict.get(node_cover_node.mapped_table[1])[0] * node_cover_node_table_width
                    node_cover_node_table_size =  (tables_dict.get(node_cover_node.mapped_table[1])[0] *
                                                   (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship))
                    total_join_cost += scan_cost(node_cover_node_table_size, scan_cost_per_tuple=0.11)#1.1#1.2#to union each node_cover_node - need to scan built table for node_cover_node
                    no_of_unions += 1
                else:
                    assert node_cover_node.unique_name == node.unique_name#node itself - node could be all/contained/partial
                    assert not node_cover_node.is_contained_all_descendants#cannot be contained_all_descendants since its len(node_cover)>1
                    if config[node_cover_node.unique_name] == "all_by_itself":
                        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                        node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                        node_cover_node_table_width = table_widths.get(node_cover_node.mapped_table[1])
                        node_cover_node_table_width = 1
                        node_cover_node_table_size *= node_cover_node_table_width
                        node_cover_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        node_cover_node_sorted = False
                        for attribute in node_cover_node.attribute_list:
                            if "pk_name" in attribute:
                                continue
                            else:
                                assert "name" in attribute
                                attr_name = attribute["name"]
                                attr_unique_name = attribute["unique_name"]
                                attribute_node = graph.get_node_by_name(attr_unique_name)
                                #no need to filter mvds since it is the node itself - all mvds relevant
                                if attribute_node.is_multivalued and attribute_node.is_in_separate_table:
                                    assert attr_name in node_relevant_attributes
                                    if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                                        #with clause for aggrgated mvd table is required to build only once
                                        is_mvd_aggregated_table_built = True
                                    else:#need to create aggregated mvd table by pk
                                        is_mvd_aggregated_table_built = False
                                        created_mvd_tables_attribute_name.append(attr_name)
                                    #left size is node_cover_node_table_size
                                    #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                                    total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, node_cover_node_table_size,
                                                                                node_cover_node_sorted, is_mvd_aggregated_table_built)
                                    node_cover_node_sorted = True
                                    node_cover_node_table_width += 1#for each joined mvd, a column is added
                        assert tables_dict.get(node_cover_node.mapped_table[1])[0] < node_cover_node.relation_size#due to contained_all_descendants or all_by_itself children
                                                                                                    #in the subtree rooted under node_cover_node
                        node_cover_node_table_size =  tables_dict.get(node_cover_node.mapped_table[1])[0] * 1#node_cover_node_table_width
                        node_cover_node_table_size =  (tables_dict.get(node_cover_node.mapped_table[1])[0] *
                                                       (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship))
                        total_join_cost += scan_cost(node_cover_node_table_size, scan_cost_per_tuple=0.11)#to union each node_cover_node - need to scan built table for node_cover_node
                        no_of_unions += 1
                    elif config[node_cover_node.unique_name] == "contained_in_parent":#parent of node also can be contained_all_descendants, all_by_itself, partially_by_itself, or contained_in_parent
                        #first filter for node tuples before all joins
                        table_list = table_cover_for_nodes.get(node_cover_node.unique_name).get(node_cover_node.unique_name)
                        table_list.sort(key=lambda x: x[0], reverse=True)
                        left_table_size = node_cover_node.relation_size
                        left_table_size = find_mapped_table_size_for_materialized_node(graph, config, node_cover_node, left_table_size)#modify left table size to remove tuples from
                                                                                                                    #contained_all_descendants or all children in subtree rooted by node
                        #filter for node tuples - hence left size is (node.relation_size - all tuples from contained_all_descendants/all child in subtree rooted by node(not tables_dict.get(node.mapped_table[1])[0]))
                        node_mapped_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                        node_mapped_table_width = table_widths.get(node_cover_node.mapped_table[1])
                        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                        node_mapped_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        total_join_cost += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - considered # of tuples instead of area
                        node_mapped_table_width = 1
                        left_table_size *= node_mapped_table_width
                        left_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        node_cover_node_sorted = False
                        #mvd joins of node - mvds(from itself or from parents) can be in separate tables even if node is contained in parent
                        for attribute in node_cover_node.attribute_list:
                            if "pk_name" in attribute:
                                continue
                            else:
                                assert "name" in attribute
                                attr_name = attribute["name"]
                                attr_unique_name = attribute["unique_name"]
                                attribute_node = graph.get_node_by_name(attr_unique_name)
                                #no need to filter mvds since it is the node itself - all mvds relevant
                                if attribute_node.is_multivalued and attribute_node.is_in_separate_table:
                                    assert attr_name in node_relevant_attributes
                                    if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                                        #with clause for aggrgated mvd table is required to build only once
                                        is_mvd_aggregated_table_built = True
                                    else:#need to create aggregated mvd table by pk
                                        is_mvd_aggregated_table_built = False
                                        created_mvd_tables_attribute_name.append(attr_name)
                                    #left size is node_cover_node_table_size
                                    #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                                    total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, left_table_size,
                                                                                node_cover_node_sorted, is_mvd_aggregated_table_built)
                                    node_cover_node_sorted = True
                                    node_mapped_table_width += 1#for each joined mvd, a column is added
                        if len(table_list) > 1:
                            no_of_joins = 0
                            for i in range(len(table_list)):
                                table_node = graph.get_node_by_sort_key(table_list[i][0])
                                assert table_node.unique_name != node_cover_node.unique_name#since node is contained in parent, any table's sort key shouldn't be equal to entity - non-materialized option for entity
                                if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                                    #calculate_total_mvd_table_cost_for_node
                                    assert table_node.mapped_table == table_list[i]
                                    continue
                                elif table_list[i] == node_cover_node.mapped_table:#table in which node is contained is skipped
                                    continue
                                else:
                                    table_size = tables_dict.get(table_list[i][1])[0]
                                    table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                                    assert table_size==table_distinct_keys
                                    table_width = 1#table_widths.get(table_list[i][1])
                                    table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                                    no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                                    table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                    total_join_cost += sort_merge_join_cost(left_table_size, table_size) if (no_of_joins < 1 and not node_cover_node_sorted) else \
                                        (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                                    #doesn't consider the increased table width after join - left_table_size assumed to be remained same - actually only # of tuples remains the same - width increases
                                    #node mapped table can be coming from a parent(may not be immediate parent since parents also can be contained in parent) - contained_all_descendants/all by itself/partially by itself,
                                    no_of_joins += 1
                                    node_mapped_table_width += (table_width - 1) #for each joined table, except for key columns are added
                        full_table_width = node_mapped_table_width#len(node_cover_node.attribute_list)
                        node_cover_node_table_size = node_cover_node.relation_size
                        node_cover_node_table_size = find_mapped_table_size_for_materialized_node(graph, config, node_cover_node, node_cover_node_table_size)#to get
                                                                    #node_cover_node tuples in table - requires deducting contained_all_descendants or all children in
                                                                    #subtree rooted by node_cover_node from node_cover_node.relation_size
                        node_cover_node_table_size *=  1#full_table_width
                        node_cover_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        total_join_cost += scan_cost(node_cover_node_table_size, scan_cost_per_tuple=0.11)#to union each node_cover_node - need to scan built table for node_cover_node
                        no_of_unions += 1
                    else:
                        assert config[node_cover_node.unique_name] == "partially_by_itself"#parent of node also can be contained_all_descendants, all_by_itself, partially_by_itself, or contained_in_parent
                        table_list = table_cover_for_nodes.get(node_cover_node.unique_name).get(node_cover_node.unique_name)
                        table_list.sort(key=lambda x: x[0], reverse=True)
                        left_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]#start from node itself
                        left_table_width = table_widths.get(node_cover_node.mapped_table[1])
                        left_table_width = 1
                        left_table_size *= left_table_width #for cost estimation - consider area as the table size
                        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                        left_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        node_cover_node_sorted = False#assume node is not sorted
                        #if node has mvds in separate tables - aggregation, pk-fk join
                        for attribute in node_cover_node.attribute_list:
                            if "pk_name" in attribute:
                                continue
                            else:
                                assert "name" in attribute
                                attr_name = attribute["name"]
                                attr_unique_name = attribute["unique_name"]
                                attribute_node = graph.get_node_by_name(attr_unique_name)
                                #no need to filter mvds since it is the node itself - all mvds relevant
                                if attribute_node.is_multivalued and attribute_node.is_in_separate_table:
                                    assert attr_name in node_relevant_attributes
                                    if attr_name in created_mvd_tables_attribute_name:#Same aggregated mvd table may be required for multiple node_cover_nodes, but
                                        #with clause for aggrgated mvd table is required to build only once
                                        is_mvd_aggregated_table_built = True
                                    else:#need to create aggregated mvd table by pk
                                        is_mvd_aggregated_table_built = False
                                        created_mvd_tables_attribute_name.append(attr_name)
                                    #left size is node_cover_node_table_size
                                    #doesn't consider the increased table width after join - left_table_size(node_cover_node_table_size) assumed to be remained same - actually only # of tuples remains the same - width increases
                                    total_join_cost += calculate_mvd_table_cost(tables_dict, table_widths, attribute_node, left_table_size,
                                                                                node_cover_node_sorted, is_mvd_aggregated_table_built)
                                    node_cover_node_sorted = True
                                    left_table_width += 1#for each joined mvd, a column is added
                        assert len(table_list) > 1#for partially by itself node - joins are mandatory - irrespective of mvds present or not - atleast should join with 1 parent table
                        if len(table_list) > 1:
                            no_of_joins = 0
                            for i in range(len(table_list)):
                                table_node = graph.get_node_by_sort_key(table_list[i][0])
                                if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                                    #calculate_total_mvd_table_cost_for_node
                                    assert table_node.mapped_table == table_list[i]
                                    continue
                                elif table_node.unique_name == node_cover_node.unique_name:#table of node itself is skipped
                                    continue
                                else:
                                    #joins with tables - coming from parent nodes(parent nodes could be contained_in_parent/partially_by_itself) until immediate all by itself parent in cover for node
                                    #no need to consider mvd join cost since all relevant mvd tables cost is already included
                                    table_size = tables_dict.get(table_list[i][1])[0]
                                    table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                                    assert table_size==table_distinct_keys
                                    table_width = 1#table_widths.get(table_list[i][1])
                                    table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                                    no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                                    table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                    #if mvd joins happened for left or after first join with a node(after first join with a node in table_list) - left is sorted
                                    total_join_cost += sort_merge_join_cost(left_table_size, table_distinct_keys) if (no_of_joins < 1 and not node_cover_node_sorted) else \
                                        (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                                    no_of_joins += 1
                                    left_table_width += (table_width - 1) #for each joined table, except for key columns are added
                        full_table_width = left_table_width#len(node_cover_node.attribute_list)
                        assert tables_dict.get(node_cover_node.mapped_table[1])[0] < node_cover_node.relation_size#due to contained_all_descendants or all_by_itself children
                                                                                                        #in the subtree rooted under node_cover_node
                        node_cover_node_table_size =  tables_dict.get(node_cover_node.mapped_table[1])[0] * 1#full_table_width
                        node_cover_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        total_join_cost += scan_cost(node_cover_node_table_size, scan_cost_per_tuple=0.11)#to union each node_cover_node - need to scan built table for node_cover_node
                        no_of_unions += 1
            assert no_of_unions == len(node.node_cover)
            cost += total_join_cost
            node_cost[node.unique_name] = cost

        else:#only node itself - node itself contains all tuples - node is not distributed in node_cover - no contained_all_descendants/all child nodes in subtree rooted at node - no unions
            #contained_all_descendants node with no node_cover and leaf all_by_itself node with no node_cover is already handled
            #node can be partial/contained in parent/non-leaf all by itself - if all by itself only mvd joins happening
            assert len(node.node_cover)==1
            assert config[node.unique_name] == "partially_by_itself" or config[node.unique_name] == "contained_in_parent" or config[node.unique_name] == "all_by_itself"
            if config[node.unique_name] == "contained_in_parent":#parent of node also can be all_by_itself, partially_by_itself, contained_in_parent, or contained_all_descendants
                #first filter for node tuples before all joins
                table_list = table_cover_for_nodes.get(node.unique_name).get(node.unique_name)
                table_list.sort(key=lambda x: x[0], reverse=True)
                left_table_size = node.relation_size#filter for node tuples - hence left size is node.relation_size not tables_dict.get(node.mapped_table[1])[0]
                node_mapped_table_size = tables_dict.get(node.mapped_table[1])[0]
                node_mapped_table_width = table_widths.get(node.mapped_table[1])
                node_mapped_table_width = 1
                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node.mapped_table[1], 0)
                node_mapped_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                total_join_cost = 0
                total_join_cost += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - considered # of tuples instead of area
                left_table_size *= node_mapped_table_width
                left_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                node_sorted = False
                #mvd joins of node - mvds(from itself or from parents) can be in separate tables even if node is contained in parent
                total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, node, left_table_size, node_sorted)
                if len(table_list) > 1:
                    no_of_joins = 0
                    for i in range(len(table_list)):
                        table_node = graph.get_node_by_sort_key(table_list[i][0])
                        assert table_node.unique_name != node.unique_name#since node is contained in parent, any table's sort key shouldn't be equal to entity - non-materialized option for entity
                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                            #calculate_total_mvd_table_cost_for_node
                            assert table_node.mapped_table == table_list[i]
                            continue
                        elif table_list[i] == node.mapped_table:#table in which node is contained is skipped
                            continue
                        else:
                            table_size = tables_dict.get(table_list[i][1])[0]
                            table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                            assert table_size==table_distinct_keys
                            table_width = 1#table_widths.get(table_list[i][1])
                            table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            total_join_cost += sort_merge_join_cost(left_table_size, table_size) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                            #doesn't consider the increased table width after join - left_table_size assumed to be remained same - actually only # of tuples remains the same - width increases
                            #node mapped table can be coming from a parent(may not be immediate parent since parents also can be contained in parent) - all by itself or partially by itself,
                            no_of_joins += 1
                cost += total_join_cost
                node_cost[node.unique_name] = cost
            elif config[node.unique_name] == "partially_by_itself":
                table_list = table_cover_for_nodes.get(node.unique_name).get(node.unique_name)
                table_list.sort(key=lambda x: x[0], reverse=True)
                assert tables_dict.get(node.mapped_table[1])[0] == node.relation_size
                left_table_size = tables_dict.get(node.mapped_table[1])[0]#start from node itself
                left_table_width = 1#table_widths.get(node.mapped_table[1])
                left_table_size *= left_table_width #for cost estimation - consider area as the table size
                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node.mapped_table[1], 0)
                left_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                total_join_cost = 0
                node_sorted = False#assume node is not sorted
                #if node has mvds in separate tables - aggregation, pk-fk join
                total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, node, left_table_size, node_sorted)
                assert len(table_list) > 1#for partially by itself node - joins are mandatory - irrespective of mvds present or not - atleast should join with 1 parent table
                if len(table_list) > 1:
                    no_of_joins = 0
                    for i in range(len(table_list)):
                        table_node = graph.get_node_by_sort_key(table_list[i][0])
                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                            #calculate_total_mvd_table_cost_for_node
                            assert table_node.mapped_table == table_list[i]
                            continue
                        elif table_node.unique_name == node.unique_name:#table of node itself is skipped
                            continue
                        else:
                            #joins with tables - coming from parent nodes(parent nodes could be contained_in_parent/partially_by_itself) until immediate all by itself parent in cover for node
                            #no need to consider mvd join cost since all relevant mvd tables cost is already included
                            table_size = tables_dict.get(table_list[i][1])[0]
                            table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                            assert table_size==table_distinct_keys
                            table_width = 1#table_widths.get(table_list[i][1])
                            table_size *= table_width #for cost calculation - area = # of tuple * table width is considered
                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(table_list[i][1], 0)
                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                            #if mvd joins happened for left or after first join with a node(after first join with a node in table_list) - left is sorted
                            total_join_cost += sort_merge_join_cost(left_table_size, table_distinct_keys) if (no_of_joins < 1 and not node_sorted) else \
                                (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                            no_of_joins += 1
                cost += total_join_cost
                node_cost[node.unique_name] = cost
            else:#only mvd joins if mvds in separate tables
                assert config[node.unique_name] == "all_by_itself"
                table_list = table_cover_for_nodes.get(node.unique_name).get(node.unique_name)
                table_list.sort(key=lambda x: x[0], reverse=True) #list is sorted to join from the lowest to top by node sort key
                assert tables_dict.get(node.mapped_table[1])[0] == node.relation_size
                left_table_size = tables_dict.get(node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself - doesn't consider
                left_table_width = 1#table_widths.get(node.mapped_table[1])    #the table width that gets increased at each join step - assume left table size(tuples * width) remains the same
                left_table_size *= left_table_width #for cost estimation - consider area as the table size
                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node.mapped_table[1], 0)
                left_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                total_join_cost = 0
                node_sorted = False#assume node is not sorted
                #if leftmost table has mvds in separate tables - aggregation, pk-fk join
                #since node is a all by itself node with node cover 1, only joins possible is mvd tables(own or from parents) for select * query
                total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, node, left_table_size, node_sorted)
                if not len(table_list) > 1:#if no tables exist to join apart from own mapped table - which means no mvd tables
                    assert total_join_cost == 0
                    if total_join_cost == 0:#no tables were joined - need to count for a scan of relation
                        assert node_sorted == False#if mvds present, they should be in array structure
                        total_join_cost += scan_cost(left_table_size)
                cost += total_join_cost
                node_cost[node.unique_name] = cost

    elif node.is_entity() and node.is_weak_entity:
        depending_entities = []
        get_dependent_entities_for_weak_entity(graph, node, depending_entities)
        if config[node.unique_name] == "all_by_itself":
            table_list = table_cover_for_nodes.get(node.unique_name).get(node.unique_name)
            table_list.sort(key=lambda x: x[0], reverse=True) #list is sorted to join from the lowest to top by node sort key
            left_table_size = tables_dict.get(node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself - doesn't consider
            left_table_width = table_widths.get(node.mapped_table[1])    #the table width that gets increased at each join step - assume left table size(tuples * width) remains the same
            left_table_size *= 1#left_table_width #for cost estimation - consider area as the table size
            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node.mapped_table[1], 0)
            left_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
            total_join_cost = 0
            node_sorted = False#assume node is not sorted
            #if leftmost table has mvds in separate tables - aggregation, pk-fk join
            total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, node, left_table_size, node_sorted)
            assert len(table_list) > 1#have to join with a depending entity
            if len(table_list) > 1:#if tables exist to join apart from own mapped table
                no_of_joins = 0

                assert depending_entities[0] == node.parent_entity.unique_name
                for depending_node_name in depending_entities:#depending_entities in the list order first node's immediate parent, then parent's parent if parent also weak
                                                                #until a strong parent is reached - only 1 strong entity can exist in depending_entities list
                    depending_node = graph.get_node_by_name(depending_node_name)
                    if len(depending_node.children)>0 or depending_node.is_subclass:#root or subclass - depending_node belonging to an inheritance hierarchy
                        if len(depending_node.node_cover) > 1:#depending_node distributed in node_cover - need table view for full representation
                            #all mvds are aggregated in view - view contains full representations
                            depending_node_view_name = "temp_" + depending_node.unique_name
                            assert depending_node_view_name in [table_list[i][1] for i in range(len(table_list))]
                            #taking weak entity mapped table as the left table, each union table from node cover gets inl join cost with left table
                            total_join_cost += calculate_cost_for_node_associated_with_node_distributed_in_node_cover_helper(graph, depending_node, left_table_size,
                                                                        config, tables_dict, table_widths, folded_weak_entity_relationship_count,
                                                                        per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
                            no_of_joins += 1
                        else:#depending node not distributed in node_cover - mapped table contains all relevant tuples for depending_node
                            assert len(depending_node.node_cover)==1
                            if config[depending_node.unique_name] == "all_by_itself" or config[depending_node.unique_name]=="contained_all_descendants":
                                depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                                depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                                depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                                no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                                depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                                total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                                                        (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                                #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                                #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                                #after previous join with left, assume sorted
                                #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                                total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                                no_of_joins += 1
                            elif config[depending_node.unique_name] == "partially_by_itself":
                                assert tables_dict.get(depending_node.mapped_table[1])[0] == depending_node.relation_size
                                depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                                depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                                depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                                no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                                depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                                total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                                    (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                                #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                                #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                                #after previous join with left, assume sorted
                                #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                                total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                                no_of_joins += 1
                                #since depending node is partially by itself need to gather full attribute list for depending node from parent tables
                                depending_node_table_list = table_cover_for_nodes.get(depending_node.unique_name).get(depending_node.unique_name)
                                depending_node_table_list.sort(key=lambda x: x[0], reverse=True)
                                assert len(depending_node_table_list) > 1#for partially by itself depending_node - joins are mandatory - irrespective of mvds present or not - atleast should join with 1 parent table
                                if len(depending_node_table_list) > 1:
                                    for i in range(len(depending_node_table_list)):
                                        table_node = graph.get_node_by_sort_key(depending_node_table_list[i][0])
                                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                                            #calculate_total_mvd_table_cost_for_node
                                            assert table_node.mapped_table == depending_node_table_list[i]
                                            continue
                                        elif table_node.unique_name == depending_node.unique_name:#table of depending_node itself is skipped
                                            continue
                                        else:
                                            #joins with tables - coming from parent nodes(parent nodes could be contained_in_parent/partially_by_itself) until immediate all by itself parent in cover for depending node
                                            #no need to consider mvd join cost since all relevant mvd tables cost is already included
                                            table_size = tables_dict.get(depending_node_table_list[i][1])[0]
                                            table_distinct_keys = tables_dict.get(depending_node_table_list[i][1])[1]
                                            assert table_size==table_distinct_keys
                                            table_width = table_widths.get(depending_node_table_list[i][1])
                                            table_size *= 1#table_width #for cost calculation - area = # of tuple * table width is considered
                                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node_table_list[i][1], 0)
                                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                            #if mvd joins happened for left or after first join with a node(after first join with a node in table_list) - left is sorted
                                            total_join_cost += sort_merge_join_cost(left_table_size, table_size) if (no_of_joins < 1 and not node_sorted) else \
                                                (sort_merge_join_cost(left_table_size, table_size, left_sorted=True))#assume after first join left is sorted
                                            no_of_joins += 1
                            else:
                                assert config[depending_node.unique_name] == "contained_in_parent"
                                depending_node_mapped_table_size = tables_dict.get(depending_node.mapped_table[1])[0]
                                no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                                depending_node_mapped_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                total_join_cost += scan_cost(depending_node_mapped_table_size)#scan cost to filter for depending node tuples - considered # of tuples instead of area
                                depending_node_table_size = depending_node.relation_size#filter for depending_node tuples - hence left size is depending_node.relation_size not tables_dict.get(depending_node.mapped_table[1])[0]
                                depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                                depending_node_table_size *= 1#depending_node_table_width
                                depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                                total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                                    (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                                #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                                #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                                #after previous join with left, assume sorted
                                #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                                total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                                no_of_joins += 1
                                #depending_node is contained in parent - might have joins with top anscestor tables
                                depending_node_table_list = table_cover_for_nodes.get(depending_node.unique_name).get(depending_node.unique_name)
                                depending_node_table_list.sort(key=lambda x: x[0], reverse=True)
                                if len(depending_node_table_list) > 1:
                                    for i in range(len(depending_node_table_list)):
                                        table_node = graph.get_node_by_sort_key(depending_node_table_list[i][0])
                                        assert table_node.unique_name != depending_node.unique_name#since node is contained in parent, any table's sort key shouldn't be equal to entity - non-materialized option for entity
                                        if table_node.is_attribute() and table_node.is_multivalued:#mvd tables are skipped since all relevant mvd tables are already joined in
                                            #calculate_total_mvd_table_cost_for_node
                                            assert table_node.mapped_table == depending_node_table_list[i]
                                            continue
                                        elif depending_node_table_list[i] == depending_node.mapped_table:#table in which depending_node is contained is skipped
                                            continue
                                        else:
                                            table_size = tables_dict.get(depending_node_table_list[i][1])[0]
                                            table_distinct_keys = tables_dict.get(depending_node_table_list[i][1])[1]
                                            assert table_size==table_distinct_keys
                                            table_width = table_widths.get(depending_node_table_list[i][1])
                                            table_size *= 1#table_width #for cost calculation - area = # of tuple * table width is considered
                                            no_of_folded_weak_entity_or_relationship = folded_weak_entity_relationship_count.get(depending_node_table_list[i][1], 0)
                                            table_size *= (1 + no_of_folded_weak_entity_or_relationship*per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                                            total_join_cost += sort_merge_join_cost(left_table_size, table_size) if (no_of_joins < 1 and not node_sorted) else \
                                                (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                                            #doesn't consider the increased table width after join - left_table_size assumed to be remained same - actually only # of tuples remains the same - width increases
                                            #node mapped table can be coming from a parent(may not be immediate parent since parents also can be contained in parent) - all by itself or partially by itself,
                                            no_of_joins += 1
                    elif depending_node.is_weak_entity:
                        assert config[depending_node.unique_name] == "all_by_itself"#if a depending parent is also a weak entity - that parent has to all by itself not folded
                        depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                        depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                        depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                        depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                        total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                            (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                        #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                        #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                        #after previous join with left, assume sorted
                        #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                        total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                        no_of_joins += 1
                    else:
                        assert depending_node.is_entity and not (len(depending_node.children) > 0 or depending_node.is_subclass)#depending node is a regular entity not belonging to a hierarchy
                        assert config[depending_node.unique_name] == "all_by_itself"#regular strong entity
                        depending_node_table_size = tables_dict.get(depending_node.mapped_table[1])[0]#at each intermediate and final step -> result size(# of tuples) is same as left table size since we started with the node itself
                        depending_node_table_width = table_widths.get(depending_node.mapped_table[1])
                        depending_node_table_size *= 1#depending_node_table_width #for cost estimation - consider area as the table size
                        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(depending_node.mapped_table[1], 0)
                        depending_node_table_size *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        #if mvd joins happened for left or after first join with a node in table_list - left is sorted
                        total_join_cost += sort_merge_join_cost(left_table_size, depending_node_table_size) if (no_of_joins < 1 and not node_sorted) else \
                            (sort_merge_join_cost(left_table_size, depending_node_table_size, left_sorted=True))#assume after first join left is sorted
                        #if joined node_table has mvds in separate tables - aggregation, pk-fk join
                        #mvd joins are done to node_table only after it is joined with left - doing joins in order of lowest selectivity
                        #after previous join with left, assume sorted
                        #left side join size is only left_table_size not table_node relation_size since left and table_node is already joined and size of the join result is only left_size - doesn't consider the increased table width
                        total_join_cost += calculate_total_mvd_table_cost_for_node(graph, tables_dict, table_widths, depending_node, left_table_size, True)#mvd join for depending_node if mvds exist in separate table
                        no_of_joins += 1
            cost += total_join_cost
            node_cost[node.unique_name] = cost
        else:
            assert config[node.unique_name] == "contained_in_parent"
            #when weak entity node contained in parent - first calculate cost to build the full parent - parent could be a weak entity/subclass/regular entity
            #then consider cost for expanding the folded weak entity
            #if expansion first then build full parent considered - then pk of parent is duplicated with each expanded weak entity tuple causing more joins across tables
            #hence first create full parent(can use already calculated cost), then do expansion for folded weak entity tuples
            table_list = table_cover_for_nodes.get(node.unique_name).get(node.unique_name)
            table_list.sort(key=lambda x: x[0], reverse=True) #list is sorted to join from the lowest to top by node sort key
            avg_no_of_parent_entity_tuples_with_atleast_one_weak_entity_tuple = (node.parent_entity.relation_size *
                                                                                 (1 - (1 - 1.0/node.parent_entity.relation_size)**node.relation_size))
            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node.parent_entity.mapped_table[1], 0)
            avg_no_of_parent_entity_tuples_with_atleast_one_weak_entity_tuple *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table *
                                                                                  per_tuple_weight_for_a_folded_weak_entity_or_relationship)
            node_mapped_table_size = node.parent_entity.relation_size#if parent's node cover > 1 - still its relation_size gives the all tuples in union view
            total_join_cost = 0
            total_join_cost += scan_cost(node_mapped_table_size, scan_cost_per_tuple=3)#scan cost to filter for parent tuples with non-zero length for folded weak entity array -
                                                                #a bit more costly to check whether json array length is non-zero -
                                                                #only put # of tuples - didn't consider table_width
            #full parent buildup with filtering for non-zero array lengths for folded weak entity node
            if len(node.parent_entity.node_cover) > 1:
                #cost to generate each union table in the view - mvd joins for node cover nodes and plus other joins if node itself is PBI or CIP
                parent_view_name = "temp_"+node.parent_entity.unique_name
                assert parent_view_name in [table_list[i][1] for i in range(len(table_list))]
                #tuples per union table in node cover with non-zero length for folded weak entity array is determined inside
                #filtering tuples in each union table by weak entity array with non-zero length
                total_join_cost += calculate_cost_for_folded_node_associated_with_node_distributed_in_node_cover_helper(graph, node, node.parent_entity,
                                                                            config, tables_dict, table_widths,
                                                                            folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            else:
                total_join_cost += calculate_cost_for_folded_node_associated_with_node_not_distributed_in_node_cover_helper(graph, node,
                                                                                                                            node.parent_entity, avg_no_of_parent_entity_tuples_with_atleast_one_weak_entity_tuple, config, tables_dict, table_widths,
                                                                                                                            folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            #unfolding weak entity after all joins
            total_join_cost += scan_folded_weak_entity_modified(avg_no_of_parent_entity_tuples_with_atleast_one_weak_entity_tuple, node.relation_size)
            cost += total_join_cost
            node_cost[node.unique_name] = cost

            """
            assert config[node.unique_name] == "contained_in_parent"
            #when weak entity node contained in parent - first calculate cost to build the full parent - parent could be a weak entity/subclass/regular entity
            #then consider cost for expanding the folded weak entity
            #if expansion first then build full parent considered - then pk of parent is duplicated with each expanded weak entity tuple causing more joins across tables
            #hence first create full parent(can use already calculated cost), then do expansion for folded weak entity tuples
            total_join_cost = 0
            #full parent buildup
            assert node.parent_entity.unique_name in node_cost
            total_join_cost += node_cost[node.parent_entity.unique_name]
            #unfolding weak entity after all joins
            all_parent_tuples = node.parent_entity.relation_size # not tables_dict.get(node.mapped_table[1])[0] since parent in which node is contained can be distributed
                                        #in multiple tables - hence folded weak entity can be distributed as well
                                     #only #of tuples not width
                                    #need to scan entire parent tuples irrespective whether each parent tuple is mapped to weak entity tuple/s or not
            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node.mapped_table[1], 0)
            all_parent_tuples *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)#add weight for parent tuples
            contained_parent_total_table_width_after_joins = get_full_width_of_table_after_building_full_entity_node(graph, node.parent_entity)
            #total_join_cost += scan_folded_weak_entity(contained_parent_table_size, contained_parent_total_table_width_after_joins,
            #                                           scan_cost_for_weak_entity_col=20)#assigned a scan cost per tuple(20) higher than a regular scan(1.0)
            total_join_cost += scan_folded_weak_entity_modified(all_parent_tuples, node.relation_size)
            cost += total_join_cost
            node_cost[node.unique_name] = cost
            """
    elif node.is_relationship() and config[node.unique_name] == "all_by_itself":
        table_list = table_cover_for_nodes.get(node.unique_name).get(node.unique_name)
        table_list.sort(key=lambda x: x[0], reverse=True)
        for i in range(len(table_list)):#node itself - table list should contain only mapped table and its own mvd tables
            table_node = graph.get_node_by_sort_key(table_list[i][0])
            if table_node.is_attribute() and table_node.is_multivalued:
                assert table_node.entity.unique_name == node.unique_name
            else:
                assert table_node.unique_name == node.unique_name
        left_table_size = tables_dict.get(node.mapped_table[1])[0]#start from node itself
        left_table_width = table_widths.get(node.mapped_table[1])
        left_table_size *= 1#left_table_width #for cost estimation - consider area as the table size
        total_join_cost = 0
        node_sorted = False#assume node is not sorted
        #if node has mvds in separate tables - aggregation, pk-fk join
        total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, node, left_table_size, node_sorted)
        #entity1
        entity1_table_list = table_cover_for_nodes.get(node.unique_name).get(node.entity1.unique_name)# same as table_cover_for_nodes.get(node.entity1.unique_name)
        if len(node.entity1.node_cover)>1:
            #taking relationship mapped table as the left table, each union table from node cover does inl join cost with left table
            entity1_view_name = "temp_"+node.entity1.unique_name
            assert entity1_view_name == entity1_table_list[0][1]
            total_join_cost += calculate_cost_for_node_associated_with_node_distributed_in_node_cover_helper(graph, node.entity1, left_table_size, config, tables_dict, table_widths,
                                                                                          folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
        else:
            total_join_cost += calculate_cost_for_relationship_associated_with_node_not_distributed_in_node_cover_helper(graph, node, node.entity1, left_table_size, config, tables_dict, table_widths,
                                                                      folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
        #entity2
        entity2_table_list = table_cover_for_nodes.get(node.unique_name).get(node.entity2.unique_name)
        if len(node.entity2.node_cover)>1:
            #taking relationship mapped table as the left table, each union table from node cover does inl join cost with left table
            entity2_view_name = "temp_"+node.entity2.unique_name
            assert entity2_view_name == entity2_table_list[0][1]
            total_join_cost += calculate_cost_for_node_associated_with_node_distributed_in_node_cover_helper(graph, node.entity2, left_table_size, config, tables_dict, table_widths,
                                                                                                             folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
        else:
            total_join_cost += calculate_cost_for_relationship_associated_with_node_not_distributed_in_node_cover_helper(graph, node, node.entity2, left_table_size, config, tables_dict, table_widths,
                                                                      folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)

        cost += total_join_cost
        node_cost[node.unique_name] = cost

    elif node.is_relationship() and config[node.unique_name] == "folded_to_many_side":
        assert check_if_relationship_is_1_N(node)
        if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:#Many side is entity2 - node is folded in entity2
            assert node.mapped_table == node.entity2.mapped_table
            left_table_size = node.relation_size#todo - whether to put node.relation_size or mapped table/view size - not node mapped table/view size since need to filter for only relationship - participation may not be total
            left_table_width = table_widths.get(node.mapped_table[1])
            left_table_size *= 1#left_table_width
            total_join_cost = 0
            node_sorted = False#assume node is not sorted
            #if node has mvds in separate tables - aggregation, pk-fk join
            total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, node, left_table_size, node_sorted)
            node_mapped_table_size = node.entity2.relation_size#if entity2's node cover > 1 - still its relation_size gives the all tuples in union view
            node_mapped_table_width = table_widths.get(node.mapped_table[1])
            total_join_cost += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - only put # of tuples - didn't consider table_width

            #entity2 - entity in which relationship is folded
            entity2_table_list = table_cover_for_nodes.get(node.unique_name).get(node.entity2.unique_name)
            if len(node.entity2.node_cover)>1:#view generates the full entity node
                #cost to generate each union table in the view - mvd joins for node cover nodes and plus other joins if node itself is PBI or CIP
                entity2_view_name = "temp_"+node.entity2.unique_name
                assert entity2_view_name == entity2_table_list[0][1]
                #tuples participating in relationship per union table in node cover is determined inside - filtering each union table by not null relationship tuples
                total_join_cost += calculate_cost_for_folded_node_associated_with_node_distributed_in_node_cover_helper(graph, node,
                                                                                                                        node.entity2, config, tables_dict, table_widths,
                                                                                                                        folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            else:
                total_join_cost += calculate_cost_for_folded_node_associated_with_node_not_distributed_in_node_cover_helper(graph, node,
                                                                                                                            node.entity2, left_table_size, config, tables_dict, table_widths,
                                                                                                                            folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            #entity1
            entity1_table_list = table_cover_for_nodes.get(node.unique_name).get(node.entity1.unique_name)
            #for non-hierarchy entity nodes, node_cover size is not initialized, hence 0. For hierarchy nodes it can be 1 or (greater than 1 if distributed in node cover).
            if len(node.entity2.node_cover)>1 and len(node.entity1.node_cover)>1:
                #each table from node cover of entity2 joins with each table from node cover of entity1
                #can't take left_table_size as relationship relation size - each table has to be separately joined
                many_side_entity = node.entity2
                probability_that_many_side_entity_tuple_participates_in_relationship = node.relation_size/many_side_entity.relation_size#assume uniform participation rate
                for node_cover_node_name in many_side_entity.node_cover:#node_cover contains node itself and any contained_all_descendants/all child nodes in the subtree rooted at node
                    node_cover_node = graph.get_node_by_name(node_cover_node_name)
                    if node_cover_node.unique_name != many_side_entity.unique_name:
                        assert node_cover_node.is_contained_all_descendants or node_cover_node.is_all_by_itself
                        node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                        #only consider tuples without accounting a weight for folded weak entities/relationships in table
                        participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                        #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                    else:
                        assert node_cover_node.unique_name == many_side_entity.unique_name#node itself - node could be all/contained/partial
                        assert not node_cover_node.is_contained_all_descendants#cannot be contained_all_descendants since its len(node_cover)>1
                        #if node_cover_node is node itself, per node_cover_node cost in node_cover is the cost to join node_cover_node.mapped_table with all relevant mvd tables and other joins
                        #based on node is CIP or PBI
                        if config[node_cover_node.unique_name] == "all_by_itself":
                            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        elif config[node_cover_node.unique_name] == "contained_in_parent":
                            relevant_node_cover_node_tuples_in_mapped_table = node_cover_node.relation_size
                            relevant_node_cover_node_tuples_in_mapped_table = find_mapped_table_size_for_materialized_node(graph, config, node_cover_node,
                                                                                                                           relevant_node_cover_node_tuples_in_mapped_table)#modify node size to remove tuples from
                            #contained_all_descendants or all children in subtree rooted by node
                            #filter for node tuples - hence left size is (node.relation_size - all tuples from contained_all_descendants/all child in subtree rooted by node(not tables_dict.get(node.mapped_table[1])[0]))
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * relevant_node_cover_node_tuples_in_mapped_table
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        else:
                            assert config[node_cover_node.unique_name] == "partially_by_itself"
                            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)

                    #participating tuples from each union table(from many side in which relationship is folded) joins with entity1 which is distributed in node cover
                    total_join_cost += calculate_cost_for_node_associated_with_node_distributed_in_node_cover_helper(graph, node.entity1,
                                                    participating_tuples_from_node_cover_node, config, tables_dict, table_widths,
                                                    folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            elif len(node.entity2.node_cover)>1 and len(node.entity1.node_cover)<=1:
                #each table from node cover of entity2 joins with the table of entity1
                #can't take left_table_size as relationship relation size - each table has to be separately joined
                many_side_entity = node.entity2
                probability_that_many_side_entity_tuple_participates_in_relationship = node.relation_size/many_side_entity.relation_size#assume uniform participation rate
                for node_cover_node_name in many_side_entity.node_cover:#node_cover contains node itself and any contained_all_descendants/all child nodes in the subtree rooted at node
                    node_cover_node = graph.get_node_by_name(node_cover_node_name)
                    if node_cover_node.unique_name != many_side_entity.unique_name:
                        assert node_cover_node.is_contained_all_descendants or node_cover_node.is_all_by_itself
                        node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                        participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                        #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                    else:
                        assert node_cover_node.unique_name == many_side_entity.unique_name#node itself - node could be all/contained/partial
                        assert not node_cover_node.is_contained_all_descendants#cannot be contained_all_descendants since its len(node_cover)>1
                        #if node_cover_node is node itself, per node_cover_node cost in node_cover is the cost to join node_cover_node.mapped_table with all relevant mvd tables and other joins
                        #based on node is CIP or PBI
                        if config[node_cover_node.unique_name] == "all_by_itself":
                            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        elif config[node_cover_node.unique_name] == "contained_in_parent":
                            relevant_node_cover_node_tuples_in_mapped_table = node_cover_node.relation_size
                            relevant_node_cover_node_tuples_in_mapped_table = find_mapped_table_size_for_materialized_node(graph, config, node_cover_node,
                                                                                                                           relevant_node_cover_node_tuples_in_mapped_table)#modify node size to remove tuples from
                            #contained_all_descendants or all children in subtree rooted by node
                            #filter for node tuples - hence left size is (node.relation_size - all tuples from contained_all_descendants/all child in subtree rooted by node(not tables_dict.get(node.mapped_table[1])[0]))
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * relevant_node_cover_node_tuples_in_mapped_table
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        else:
                            assert config[node_cover_node.unique_name] == "partially_by_itself"
                            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)

                    #participating tuples from each union table joins with entity1 which is not distributed in node cover
                    total_join_cost += calculate_cost_for_relationship_associated_with_node_not_distributed_in_node_cover_helper(graph, node, node.entity1,
                                                                                participating_tuples_from_node_cover_node, config, tables_dict, table_widths,
                                                                                folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            elif len(node.entity2.node_cover)<=1 and len(node.entity1.node_cover)>1:#entity2 not distributed - can take left_table_size as sum of tuples
                entity1_view_name = "temp_"+node.entity1.unique_name
                assert entity1_view_name == entity1_table_list[0][1]
                #entity1 distributd in node cover
                total_join_cost += calculate_cost_for_node_associated_with_node_distributed_in_node_cover_helper(graph, node.entity1, left_table_size, config, tables_dict, table_widths,
                                                                                                                 folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            elif len(node.entity2.node_cover)<=1 and len(node.entity1.node_cover)<=1:#entity2 not distributed - can take left_table_size as sum of tuples
                #entity1 not distributed in node cover
                total_join_cost += calculate_cost_for_relationship_associated_with_node_not_distributed_in_node_cover_helper(graph, node, node.entity1, left_table_size, config, tables_dict, table_widths,
                                                                          folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            cost += total_join_cost
            node_cost[node.unique_name] = cost
        elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:#Many side is entity1 - node is folded in entity1
            assert node.mapped_table == node.entity1.mapped_table
            left_table_size = node.relation_size#todo - whether to put node.relation_size or mapped table/view size - not node mapped table/view size since need to filter for only relationship - participation may not be total
            left_table_width = table_widths.get(node.mapped_table[1])
            left_table_size *= 1#left_table_width
            total_join_cost = 0
            node_sorted = False#assume node is not sorted
            #if node has mvds in separate tables - aggregation, pk-fk join
            total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, node, left_table_size, node_sorted)
            node_mapped_table_size = node.entity1.relation_size#if entity1's node cover > 1 - still its relation_size gives the all tuples in union view
            node_mapped_table_width = table_widths.get(node.mapped_table[1])
            total_join_cost = 0
            total_join_cost += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - only put # of tuples - didn't consider table_width
            #entity1 - entity in which relationship is folded
            entity1_table_list = table_cover_for_nodes.get(node.unique_name).get(node.entity1.unique_name)
            if len(node.entity1.node_cover)>1:#view generates the full entity node
                #cost to generate each union table in the view - mvd joins and other joins if a node in node cover is PBI or CIP
                entity1_view_name = "temp_"+node.entity1.unique_name
                assert entity1_view_name == entity1_table_list[0][1]
                total_join_cost += calculate_cost_for_folded_node_associated_with_node_distributed_in_node_cover_helper(graph, node,
                                                                                                                        node.entity1, config, tables_dict, table_widths,
                                                                                                                        folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)

            else:
                total_join_cost += calculate_cost_for_folded_node_associated_with_node_not_distributed_in_node_cover_helper(graph, node,
                                                                                                                            node.entity1, left_table_size, config, tables_dict, table_widths,
                                                                                                                            folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            #entity2
            entity2_table_list = table_cover_for_nodes.get(node.unique_name).get(node.entity2.unique_name)
            #for non-hierarchy entity nodes, node_cover size is not initialized, hence 0. For hierarchy nodes it can be 1 or (greater than 1 if distributed in node cover).
            if len(node.entity1.node_cover)>1 and len(node.entity2.node_cover)>1:
                #each table from node cover of entity1 joins with each table from node cover of entity2
                #can't take left_table_size as relationship relation size - each table has to be separately joined
                many_side_entity = node.entity1
                probability_that_many_side_entity_tuple_participates_in_relationship = node.relation_size/many_side_entity.relation_size#assume uniform participation rate
                for node_cover_node_name in many_side_entity.node_cover:#node_cover contains node itself and any contained_all_descendants/all child nodes in the subtree rooted at node
                    node_cover_node = graph.get_node_by_name(node_cover_node_name)
                    if node_cover_node.unique_name != many_side_entity.unique_name:
                        assert node_cover_node.is_contained_all_descendants or node_cover_node.is_all_by_itself
                        node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                        participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                        #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                    else:
                        assert node_cover_node.unique_name == many_side_entity.unique_name#node itself - node could be all/contained/partial
                        assert not node_cover_node.is_contained_all_descendants#cannot be contained_all_descendants since its len(node_cover)>1
                        #if node_cover_node is node itself, per node_cover_node cost in node_cover is the cost to join node_cover_node.mapped_table with all relevant mvd tables and other joins
                        #based on node is CIP or PBI
                        if config[node_cover_node.unique_name] == "all_by_itself":
                            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        elif config[node_cover_node.unique_name] == "contained_in_parent":
                            relevant_node_cover_node_tuples_in_mapped_table = node_cover_node.relation_size
                            relevant_node_cover_node_tuples_in_mapped_table = find_mapped_table_size_for_materialized_node(graph, config, node_cover_node,
                                                                                                                           relevant_node_cover_node_tuples_in_mapped_table)#modify node size to remove tuples from
                            #contained_all_descendants or all children in subtree rooted by node
                            #filter for node tuples - hence left size is (node.relation_size - all tuples from contained_all_descendants/all child in subtree rooted by node(not tables_dict.get(node.mapped_table[1])[0]))
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * relevant_node_cover_node_tuples_in_mapped_table
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        else:
                            assert config[node_cover_node.unique_name] == "partially_by_itself"
                            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)

                    #participating tuples from each union table joins with entity2 which is distributed in node cover
                    total_join_cost += calculate_cost_for_node_associated_with_node_distributed_in_node_cover_helper(graph, node.entity2,
                                                                                                                     participating_tuples_from_node_cover_node, config, tables_dict, table_widths,
                                                                                                                     folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            elif len(node.entity1.node_cover)>1 and len(node.entity2.node_cover)<=1:
                #each table from node cover of entity1 joins with the table of entity2
                #can't take left_table_size as relationship relation size - each table has to be separately joined
                many_side_entity = node.entity1
                #each tuple from many side will participate at most once in relationship
                probability_that_many_side_entity_tuple_participates_in_relationship = node.relation_size/many_side_entity.relation_size#assume uniform participation rate
                for node_cover_node_name in many_side_entity.node_cover:#node_cover contains node itself and any contained_all_descendants/all child nodes in the subtree rooted at node
                    node_cover_node = graph.get_node_by_name(node_cover_node_name)
                    if node_cover_node.unique_name != many_side_entity.unique_name:
                        assert node_cover_node.is_contained_all_descendants or node_cover_node.is_all_by_itself
                        node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                        participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                        no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                        #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                    else:
                        assert node_cover_node.unique_name == many_side_entity.unique_name#node itself - node could be all/contained/partial
                        assert not node_cover_node.is_contained_all_descendants#cannot be contained_all_descendants since its len(node_cover)>1
                        #if node_cover_node is node itself, per node_cover_node cost in node_cover is the cost to join node_cover_node.mapped_table with all relevant mvd tables and other joins
                        #based on node is CIP or PBI
                        if config[node_cover_node.unique_name] == "all_by_itself":
                            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        elif config[node_cover_node.unique_name] == "contained_in_parent":
                            relevant_node_cover_node_tuples_in_mapped_table = node_cover_node.relation_size
                            relevant_node_cover_node_tuples_in_mapped_table = find_mapped_table_size_for_materialized_node(graph, config, node_cover_node,
                                                                                                                           relevant_node_cover_node_tuples_in_mapped_table)#modify node size to remove tuples from
                            #contained_all_descendants or all children in subtree rooted by node
                            #filter for node tuples - hence left size is (node.relation_size - all tuples from contained_all_descendants/all child in subtree rooted by node(not tables_dict.get(node.mapped_table[1])[0]))
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * relevant_node_cover_node_tuples_in_mapped_table
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)
                        else:
                            assert config[node_cover_node.unique_name] == "partially_by_itself"
                            node_cover_node_table_size = tables_dict.get(node_cover_node.mapped_table[1])[0]
                            participating_tuples_from_node_cover_node = probability_that_many_side_entity_tuple_participates_in_relationship * node_cover_node_table_size
                            no_of_folded_weak_entity_or_relationship_in_mapped_table = folded_weak_entity_relationship_count.get(node_cover_node.mapped_table[1], 0)
                            #participating_tuples_from_node_cover_node *= (1 + no_of_folded_weak_entity_or_relationship_in_mapped_table * per_tuple_weight_for_a_folded_weak_entity_or_relationship)

                    #participating tuples from each union table joins with entity2 which is not distributed in node cover
                    total_join_cost += calculate_cost_for_relationship_associated_with_node_not_distributed_in_node_cover_helper(graph, node, node.entity2,
                                                                                                                                 participating_tuples_from_node_cover_node, config, tables_dict, table_widths,
                                                                                                                                 folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            elif len(node.entity1.node_cover)<=1 and len(node.entity2.node_cover)>1:#entity1 not distributed - can take left_table_size as sum of tuples
                entity2_view_name = "temp_"+node.entity2.unique_name
                assert entity2_view_name == entity2_table_list[0][1]
                #entity2 distributed in node cover
                total_join_cost += calculate_cost_for_node_associated_with_node_distributed_in_node_cover_helper(graph, node.entity2, left_table_size, config, tables_dict, table_widths,
                                                                                    folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            elif len(node.entity1.node_cover)<=1 and len(node.entity2.node_cover)<=1:#entity1 not distributed - can take left_table_size as sum of tuples
                #entity2 not distributed in node cover
                total_join_cost += calculate_cost_for_relationship_associated_with_node_not_distributed_in_node_cover_helper(graph, node, node.entity2, left_table_size, config, tables_dict, table_widths,
                                                                          folded_weak_entity_relationship_count, per_tuple_weight_for_a_folded_weak_entity_or_relationship=0.15)
            cost += total_join_cost
            node_cost[node.unique_name] = cost

    """
    elif node.is_relationship() and config[node.unique_name] == "all_by_itself":
        #assume relationship a_b(with participating entities a and b) - first entities are built by joining all required tables for participating entities - a and b
        #then joined result joined with table mapped for relationship node a_b
        #this avoids duplicating joins(full attribute list building phase for entities) for keys in relationship node
        table_list = table_cover_for_nodes.get(node.unique_name).get(node.unique_name)
        table_list.sort(key=lambda x: x[0], reverse=True)
        for i in range(len(table_list)):#node itself - table list should contain only mapped table and its own mvd tables
            table_node = graph.get_node_by_sort_key(table_list[i][0])
            if table_node.is_attribute() and table_node.is_multivalued:
                assert table_node.entity.unique_name == node.unique_name
            else:
                assert table_node.unique_name == node.unique_name
        left_table_size = tables_dict.get(node.mapped_table[1])[0]#start from node itself
        left_table_width = table_widths.get(node.mapped_table[1])
        left_table_size *= 1#left_table_width #for cost estimation - consider area as the table size
        total_join_cost = 0
        node_sorted = False#assume node is not sorted
        #if node has mvds in separate tables - aggregation, pk-fk join
        total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, node, left_table_size, node_sorted)
        #full entity1 buildup
        total_join_cost += node_cost[node.entity1.unique_name]
        #full entity2 buildup
        total_join_cost += node_cost[node.entity2.unique_name]
        #full entity1 join with relationship node
        entity1_relation_size = node.entity1.relation_size
        entity1_full_width = get_full_width_of_table_after_building_full_entity_node(graph, node.entity1)
        entity1_relation_size *= 1#entity1_full_width
        total_join_cost += sort_merge_join_cost(left_table_size, entity1_relation_size, right_sorted=True) if not node_sorted else \
            (sort_merge_join_cost(left_table_size, entity1_relation_size, left_sorted=True, right_sorted=True))#entity1 is assumed to be right - and it is sorted since it is already fully built
        #full entity2 join with relationship node
        entity2_relation_size = node.entity2.relation_size
        entity2_full_width = 1#get_full_width_of_table_after_building_full_entity_node(graph, node.entity2)
        entity2_relation_size *= entity2_full_width
        total_join_cost += sort_merge_join_cost(left_table_size, entity2_relation_size, left_sorted=True, right_sorted=True)#Assume relationship is joined with entity1 first.
        # Since relationship already joined with entity1, assume left(relationship) also sorted - right here is entity2
        cost += total_join_cost
        node_cost[node.unique_name] = cost
    elif node.is_relationship() and config[node.unique_name] == "folded_to_many_side":
        assert check_if_relationship_is_1_N(node)
        if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:#Many side is entity2 - node is folded in entity2
            assert node.mapped_table == node.entity2.mapped_table
            left_table_size = node.relation_size#todo - whether to put node.relation_size or mapped table/view size - not node mapped table/view size since need to filter for only relationship - participation may not be total
            left_table_width = table_widths.get(node.mapped_table[1])
            left_table_size *= 1#left_table_width
            total_join_cost = 0
            node_sorted = False#assume node is not sorted
            #if node has mvds in separate tables - aggregation, pk-fk join
            total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, node, left_table_size, node_sorted)
            node_mapped_table_size = node.entity2.relation_size#if entity2's node cover > 1 - still its relation_size gives the all tuples in union view
            node_mapped_table_width = table_widths.get(node.mapped_table[1])
            total_join_cost = 0
            total_join_cost += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - only put # of tuples - didn't consider table_width
            #full entity1 buildup
            total_join_cost += node_cost[node.entity1.unique_name]
            #full entity2 buildup
            total_join_cost += node_cost[node.entity2.unique_name]
            #entity1 join
            entity1_relation_size = node.entity1.relation_size
            entity1_full_width = get_full_width_of_table_after_building_full_entity_node(graph, node.entity1)
            entity1_relation_size *= 1#entity1_full_width
            total_join_cost += sort_merge_join_cost(left_table_size, entity1_relation_size, left_sorted=True, right_sorted=True)#left(relationship node mapped table which is entity2 table) is sorted, right(entity1) also sorted during full buildup
            cost += total_join_cost
            node_cost[node.unique_name] = cost
        elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:#Many side is entity1 - node is folded in entity1
            assert node.mapped_table == node.entity1.mapped_table
            left_table_size = node.relation_size#todo - whether to put node.relation_size or mapped table/view size - not node mapped table/view size since need to filter for only relationship - participation may not be total
            left_table_width = table_widths.get(node.mapped_table[1])
            left_table_size *= 1#left_table_width
            total_join_cost = 0
            node_sorted = False#assume node is not sorted
            #if node has mvds in separate tables - aggregation, pk-fk join
            total_join_cost += calculate_total_mvd_table_cost_for_node(graph,  tables_dict, table_widths, node, left_table_size, node_sorted)
            node_mapped_table_size = node.entity1.relation_size#if entity1's node cover > 1 - still its relation_size gives the all tuples in union view
            node_mapped_table_width = table_widths.get(node.mapped_table[1])
            total_join_cost = 0
            total_join_cost += scan_cost(node_mapped_table_size)#scan cost to filter for node tuples - only put # of tuples - didn't consider table_width
            #full entity1 buildup
            total_join_cost += node_cost[node.entity1.unique_name]
            #full entity2 buildup
            total_join_cost += node_cost[node.entity2.unique_name]
            #entity2 join
            entity2_relation_size = node.entity2.relation_size
            entity2_full_width = get_full_width_of_table_after_building_full_entity_node(graph, node.entity2)
            entity2_relation_size *= 1#entity2_full_width
            total_join_cost += sort_merge_join_cost(left_table_size, entity2_relation_size, left_sorted=True, right_sorted=True)#left(relationship node mapped table which is entity1 table) is sorted, right(entity2) also sorted during full buildup
            cost += total_join_cost
            node_cost[node.unique_name] = cost
    """
    return cost


def calculate_select_cost_for_single_entity_or_relationship_helper(graph, node, config, tables_dict, table_widths,
                                                                   folded_weak_entity_relationship_count):
    select_all_cost_for_single_query = calculate_select_cost_for_single_entity_or_relationship_for_single_query(graph, node, config, tables_dict, table_widths,
                                                                                                                folded_weak_entity_relationship_count)
    return select_all_cost_for_single_query * node.workload_select_frequency

#each folded weak entity/relationship insert goes through its node_tables + (mapped_tables_list if not empty)
#mapped_tables_list will be non-empty when the folded weak entity's parent/relationship's many side is a hierarchy node distributed in node cover
#e.g. if Product distributed in node cover and productimage weak entity contained in product - for each productimage insert, an insert will be generated
#for each table where product is distributed
#assume product distributed in relation_1, relation_4,
#for productimage insert ("product_id": 27980, "image_id": 72321, "sort_order": 289}, an insert is generated for each table where product is distributed
#UPDATE relation_1 SET productimage = COALESCE(productimage, '[]'::jsonb) || '[{"image_id": 72321, "sort_order": 289}]'::JSONB WHERE product_id=27980
#UPDATE relation_4 SET productimage = COALESCE(productimage, '[]'::jsonb) || '[{"image_id": 72321, "sort_order": 289}]'::JSONB WHERE digitalproduct_id=27980
#of these 2 updates, only one will go through - that is the table which contains product id 27980
#this is because no prior knowledge about which table(relation_1 or relation_4) contains product id 27980
def calculate_total_workload_insert_cost_for_folded_weak_entity_or_relationship(graph, node, tables_dict):#for folded weak entity/relationship
    insert_cost_for_relevant_node_tables = 0

    relevant_tables = set()
    relevant_tables |= node.node_tables #can't do 'relevant_tables = node.node_tables' since any changes to  relevant_tables will modify original node.node_tables
    relevant_tables.update(node.mapped_tables_list)#if folded weak entity/relationship distributed in multiple tables due to parent/many_side entity distributed in node cover
                                                    #in addition to own node_tables need to consider mapped_tables_list as well in that case

    workload_insert_frequency_for_node = node.workload_insert_frequency#total no of inserts per entity/relationship node - each of these inserts goes through all relevant tables

    for relevant_node_sort_key, table_name in relevant_tables:#each insert of entity/relationship node, performs an insert to each table in relevant_tables except for mvd tables
                                                            #(the insert may or may not result in actual row insert - e.g. previous example with product id 27980)
                                                            #per single insert of entity/relationship node, no of inserts to a mvd table can be more than one
        relevant_node = graph.get_node_by_sort_key(relevant_node_sort_key)
        if relevant_node.is_attribute():
            assert relevant_node.is_multivalued and relevant_node.is_in_separate_table
            pass#mvd tables already handled separately
        else:
            table_size = tables_dict.get(table_name)[0]
            insert_cost_for_relevant_node_tables += sort_merge_join_cost(workload_insert_frequency_for_node, table_size)#extra cost incurred for folded entity/relationship inserts

    insert_cost_for_relevant_node_tables += insert_cost_for_workload_queries(workload_insert_frequency_for_node)#cost to do actual row inserts - actual row inserts are equal to
                                                                                                #workload_insert_frequency of the node,
                                                                                                #no indexes are updated since weak entity/relationship is a folded column
    return insert_cost_for_relevant_node_tables


#for each entity/relationship/mvd attr - calculate insert cost due to workload insert queries
#for each node, total inserts(workload_insert_frequency_for_node) is considered
#each node makes inserts to each table in node.node_tables - but mvd tables in node_tables is hanled separately since workload_insert_frequency for mvd attribute indicates
#full insert contribution into mvd attr from all relevant nodes(when mvd attribute coming from a hierarchy parent subclass)
#can get per insert, node cost - but that cost doesn't include the cost incurred by the insert into mvd tables
#instead of getting per insert, node cost and multiplying by no of inserts per node(workload_insert_frequency_for_node),
#get full contribution of all inserts(workload_insert_frequency_for_node) per node
def calculate_total_workload_insert_cost_for_single_entity_or_relationship_helper(graph, node, config, tables_dict):
    insert_cost_for_relevant_node_tables = 0

    #handle insert cost relevant to folded weak entity/relationship separately
    if node.is_entity() and node.is_weak_entity and config[node.unique_name] == "contained_in_parent":
        insert_cost_for_relevant_node_tables += calculate_total_workload_insert_cost_for_folded_weak_entity_or_relationship(graph, node, tables_dict)
    elif node.is_relationship() and config[node.unique_name] == "folded_to_many_side":
        insert_cost_for_relevant_node_tables += calculate_total_workload_insert_cost_for_folded_weak_entity_or_relationship(graph, node, tables_dict)
    elif node.is_attribute() and node.is_multivalued and node.is_in_separate_table:
        workload_insert_frequency_for_node = node.workload_insert_frequency#if attribute coming from a top class in hierarchy, inserts to all child classes, may have increased
                                                                            #workload_insert_frequency for attribute - attribute's workload_insert_frequency indicates the
                                                                            #total contribution from all classes in that case
        table_name = node.mapped_table[1]
        table_size = tables_dict[table_name][0]
        insert_cost_for_relevant_node_tables += insert_cost_for_workload_queries(workload_insert_frequency_for_node, table_size, num_indexes=1)
        #insert_cost(workload_insert_frequency_for_node, num_indexes=1)#assume each table has index for primary key - each tuple incurs an insert + index update cost
    else:
        workload_insert_frequency_for_node = node.workload_insert_frequency
        for relevant_node_sort_key, table_name in node.node_tables:#each insert of entity/relationship node, makes an insert to each table in node_tables except for mvd tables
                                                                    #per single insert of entity/relationship node, no of inserts to a mvd table can be more than one
            relevant_node = graph.get_node_by_sort_key(relevant_node_sort_key)
            if relevant_node.is_attribute():
                assert relevant_node.is_multivalued and relevant_node.is_in_separate_table
                pass#mvd tables already handled separately
            else:
                table_size = tables_dict[table_name][0]
                insert_cost_for_relevant_node_tables += insert_cost_for_workload_queries(workload_insert_frequency_for_node, table_size, num_indexes=1)
                                                        #insert_cost(workload_insert_frequency_for_node, num_indexes=1)

    return insert_cost_for_relevant_node_tables

def calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict, table_widths,
                                        folded_weak_entity_relationship_count, include_db_initialization_cost):  #select, insert - workload queries have single entity or relationship
    cost = 0

    #db initialization insert cost
    if include_db_initialization_cost:
        cost += calculate_db_initialization_insert_cost_for_tables(tables_dict)
        cost += calculate_db_initialization_insert_cost_for_folded_weak_entities_and_relationships(graph, config, tables_dict, table_widths)#the temp tables that
                                                                                        #need to be created for updating tables - e.g. for folded weak entities or folded 1:N relationships

    #workload select * queries - select cost
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            cost += calculate_select_cost_for_single_entity_or_relationship_helper(graph, node, config, tables_dict, table_widths,
                                                                                   folded_weak_entity_relationship_count)

    #workload insert queries - insert cost
    workload_insert_cost = 0
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship() or (node.is_attribute() and node.is_multivalued and node.is_in_separate_table):
            workload_insert_cost += calculate_total_workload_insert_cost_for_single_entity_or_relationship_helper(graph, node, config, tables_dict)
    node_cost["workload_insert_cost"] = workload_insert_cost
    #print("workload insert cost: ", workload_insert_cost)
    cost += workload_insert_cost

    return cost

#update immediate parent with contained_all_descendants or all_by_itself
def update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes(graph, config):
    def get_immediate_parent_node_with_all_by_itself(config, node):  #immediate parent to node
        assert node is not None
        if config[node.unique_name] == "contained_all_descendants" or config[node.unique_name] == "all_by_itself":
            return node.unique_name
        elif config[node.unique_name] == "partially_by_itself":
            return get_immediate_parent_node_with_all_by_itself(config, node.parent_entity)
        elif config[node.unique_name] == "contained_in_parent":
            return get_immediate_parent_node_with_all_by_itself(config, node.parent_entity)

    for node in graph.nodes:
        if node.is_entity() and node.is_subclass and config[node.unique_name] == "partially_by_itself":
            node.immediate_parent_with_all_by_itself_unique_name = get_immediate_parent_node_with_all_by_itself(config,
                                                                                                                node.parent_entity)


def initialize_dummy_schema_config(graph):  #needed this initialization for workload generation
    reset_partitioning_options_for_node(graph)
    initialize_partitioning_options_for_node(graph)

    all_components = [graph_node for graph_node in graph.nodes if
                      graph_node.is_entity() or graph_node.is_relationship() or (
                              graph_node.is_attribute() and graph_node.is_multivalued)]

    config = {}
    for component in all_components:
        config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)

    tables_dict = define_the_generated_physical_schema(graph, config)
    return config


def add_parent_attributes_to_table(graph, node, table_attributes, is_child_all_by_itself: bool):
    if node.parent_entity is not None:
        add_parent_attributes_to_table(graph, node.parent_entity, table_attributes, is_child_all_by_itself)

    return add_attributes_to_table(graph, node, table_attributes, is_child_all_by_itself)


def add_attributes_to_table(graph, node, table_attributes,
                            is_child_all_by_itself=None):  #for attributes, add only unique name
    #add attributes
    for attribute in node.attributes:
        if not attribute.is_primary_key and not attribute.is_discriminator:
            if attribute.is_composite:  #assume - 1 level of composite
                if attribute.is_flattened:
                    for subattribute in attribute.children:
                        table_attributes.append(subattribute.unique_name)
                else:
                    table_attributes.append(attribute.unique_name)
            elif attribute.is_multivalued:  #todo - need to do when an attribute is an array of composite type - both mvd and composite
                if node.mapped_table is not None:
                    if node.mapped_table == attribute.mapped_table:  #store mvd as array attribute
                        assert not attribute.is_in_separate_table
                        table_attributes.append(attribute.unique_name)
            else:
                table_attributes.append(attribute.unique_name)


#this is required to calculate the table width for cost calculation - for pks, add their name only, for attributes, add their unique name only in table_attributes for corresponding table
# need only the count of columns in table
#create_table_statements in construct_create_statements1 is simplified to only add table columns to get table width
def calculate_table_width_for_physical_tables_in_config(graph, config, table_mapping):
    initialize_keys(graph, table_mapping)

    table_width_dict = {}

    for i, (table_name, table_list) in enumerate(table_mapping.items()):
        table = table_name
        table_attributes = []  #add [attribute_name,..,...]
        is_entity_in_table = False
        is_relationship_in_table = False
        primary_keys = []

        table_list_copy = table_list.copy()
        for n in table_list_copy:
            x = graph.get_node_by_name(n)
            assert x

        for unique_name in table_list:  #iterate each node mapped to table - table_list is the set of nodes mapped to table
            node = graph.get_node_by_name(unique_name)
            if node.is_entity() and not node.is_subclass and not node.is_weak_entity:  #Regular Entity
                is_entity_in_table = True
                for key, type, key_unique_name, ER_key_name in node.key.table_key:
                    if key not in primary_keys:
                        table_attributes.append(key)
                        primary_keys.append(key)
                #add attributes
                add_attributes_to_table(graph, node, table_attributes)

            #sub class
            elif node.is_entity() and node.is_subclass and not node.is_weak_entity:
                is_entity_in_table = True
                for i in range(len(node.key.table_key)):
                    if node.key.table_key[i][0] not in primary_keys:
                        table_attributes.append(node.key.table_key[i][0])
                        primary_keys.append(node.key.table_key[i][0])

                if not node.is_contained_in_parent:
                    if node.is_contained_all_descendants or node.is_all_by_itself:  #need to add all attributes from all parents in hierarchy - parent table may/may not exist - checking if immediate parent exists in a different table doesn't capture this
                        add_parent_attributes_to_table(graph, node.parent_entity, table_attributes,
                                                       node.is_contained_all_descendants or node.is_all_by_itself)

                #add attributes
                add_attributes_to_table(graph, node, table_attributes)

                if node.is_parent_in_table:
                    if not any(name == "role" for name in table_attributes):
                        table_attributes.append("role")

            elif node.is_entity() and not node.is_subclass and node.is_weak_entity:
                is_entity_in_table = True
                if node.is_parent_in_table:  #store weak entity as array
                    table_attributes.append(node.unique_name)
                else:  #add attributes for - depending entity, weak entity discriminator attribute, weak entity other attributes
                    #strong entity - this depending entity can be a weak entity too
                    for i in range(len(node.key.table_key[0])):
                        if node.key.table_key[0][i][0] not in primary_keys:
                            table_attributes.append(node.key.table_key[0][i][0])
                            primary_keys.append(node.key.table_key[0][i][0])
                    #weak entity - discriminator attributes
                    for i in range(len(node.key.table_key[1])):
                        if node.key.table_key[1][i][0] not in primary_keys:
                            table_attributes.append(node.key.table_key[1][i][0])
                            primary_keys.append(node.key.table_key[1][i][0])

                    #add attributes
                    add_attributes_to_table(graph, node, table_attributes)

            elif node.is_relationship():
                is_relationship_in_table = True
                if not node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:  #M:N
                    for i in range(len(node.key.table_key)):  #i=0,1 - for 2 participating entities
                        for j in range(len(node.key.table_key[i])):
                            if node.key.table_key[i][j][0] not in primary_keys:
                                table_attributes.append(node.key.table_key[i][j][0])
                                primary_keys.append(node.key.table_key[i][j][0])

                    #add attributes
                    #add_attributes_to_table(graph, node, table_attributes, created_types_names, created_types)

                else:
                    many_side_node = node.entity1 if not node.rel_dict['entity1']['one'] and node.rel_dict['entity2'][
                        'one'] else node.entity2
                    #no need to add pk to table for relationship when it is folded, since pk is already added from entity itself
                    #need to explicitly add the pk only when relationship is in separate table
                    if config[node.unique_name] != "folded_to_many_side":
                        for i in range(len(node.key.table_key[0])):  #only add N side keys as pk keys
                            if node.key.table_key[0][i][0] not in primary_keys:
                                table_attributes.append(node.key.table_key[0][i][0])
                                primary_keys.append(node.key.table_key[0][i][0])

                    for i in range(
                            len(node.key.table_key[1])):  #add attributes from 1 side as attributes for relationship
                        if node.key.table_key[1][i][0] not in primary_keys:
                            table_attributes.append(node.key.table_key[1][i][0])

                    #add attributes
                    #add_attributes_to_table(graph, node, table_attributes, created_types_names, created_types)

                #handle when participating entities of relationships are subclasses and when all with a parent class in a single table - e.g. [Person, Student, Instructor, advisor] in a single table
                entity1 = node.entity1
                entity2 = node.entity2
                if entity1.is_subclass and entity2.is_subclass:
                    if entity1.mapped_table == node.mapped_table and entity2.mapped_table == node.mapped_table:
                        if entity1.is_parent_in_table and entity2.is_parent_in_table:
                            if entity1.key.table_key[0][0] == entity2.key.table_key[0][
                                0]:  #same pk - which means subclasses from same hierarchy - this doesn't have to be that both have same immediate parent
                                assert check_if_relationship_is_1_N(
                                    node)  #for this to happen - relationship has to be not M:N
                                table_attributes.append(node.name.lower() + "_id")  #e.g. advisor_id

                #add attributes
                add_attributes_to_table(graph, node, table_attributes)

            elif node.is_attribute() and node.is_multivalued:
                if node.is_in_separate_table:  #this has set by search algorithm
                    if node.mapped_table is not None:  #parent entity may or may not exist in a table - no_table node can have a mvd in separate table
                        if len(table_list) == 1:  #mvd as a separate table - this check is not required since it is covered by node.is_in_separate_table
                            for i in range(len(node.key.table_key[0])):  #except mvd
                                if node.key.table_key[0][i][0] not in primary_keys:
                                    table_attributes.append(node.key.table_key[0][i][0])
                                    primary_keys.append(node.key.table_key[0][i][0])

                            #add mvd to primary key
                            if node.key.table_key[1][0] not in primary_keys:
                                table_attributes.append(node.key.table_key[1][0][0])
                                primary_keys.append(node.key.table_key[1][0][0])

                            #add attributes
                            add_attributes_to_table(graph, node, table_attributes)

                else:
                    #attribute already added as array
                    pass

        if table_attributes:
            table_width_dict[table_name] = len(table_attributes)
    return table_width_dict

def get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mapping):
    folded_weak_entity_relationship_count = {}
    for table_name, mapped_node_names in table_mapping.items():
        for node_name in mapped_node_names:
            node = graph.get_node_by_name(node_name)
            if node.is_entity() and node.is_weak_entity and config[node.unique_name] == "contained_in_parent":
                if table_name in folded_weak_entity_relationship_count:
                    folded_weak_entity_relationship_count[table_name] += 1
                else:
                    folded_weak_entity_relationship_count[table_name] = 1
            elif node.is_relationship() and config[node.unique_name] == "folded_to_many_side":
                if table_name in folded_weak_entity_relationship_count:
                    folded_weak_entity_relationship_count[table_name] += 1
                else:
                    folded_weak_entity_relationship_count[table_name] = 1
    #print("folded weak entity relationship count: ", folded_weak_entity_relationship_count)
    return folded_weak_entity_relationship_count


def get_nodes_cost():
    return node_cost.copy()

#cost is defined for complete config - config is complete
def exhaustive_search(graph, include_db_initialization_cost):
    reset_partitioning_options_for_node(graph)
    initialize_partitioning_options_for_node(graph)

    nodes = [node.unique_name for node in graph.nodes if
             node.is_entity() or node.is_relationship() or (node.is_attribute() and node.is_multivalued)]
    partitioning_options = [node.partitioning_options for node in graph.nodes if
                            node.is_entity() or node.is_relationship() or (node.is_attribute() and node.is_multivalued)]

    best_config = None
    best_cost = float('inf')
    best_nodes_individual_cost = None

    total_iters = prod(len(opts) for opts in partitioning_options) if partitioning_options else 0
    print("search space size for exhaustive enumeration:", total_iters)

    for combination in product(*partitioning_options):
        config = dict(zip(nodes, combination))
        is_config_valid = check_config_is_valid(graph, config)
        if is_config_valid:
            #print("\n\n",config,"\n", "tables:", define_the_generated_physical_schema(graph, config))
            tables_dict = define_the_generated_physical_schema(graph, config)
            table_mappings = generate_table_mappings(graph)
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
            initialize_table_cover_for_nodes(graph, config)
            cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict,
                                                            table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)#cost for workload
            #print("config cost:", config)
            #print("cost:", cost,"\n")
            if cost < best_cost:
                best_config = config.copy()
                best_cost = cost
                best_nodes_individual_cost = get_nodes_cost()

    graph.config = best_config
    graph.cost = best_cost
    graph.nodes_cost = best_nodes_individual_cost
    define_the_generated_physical_schema(graph, best_config)  #update graph parameters for selected best config
    update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes(graph,
                                                                             best_config)  #update graph parameters for selected best config

    print("best config-brute force:", best_config)
    print("best cost-brute force:", best_cost, "\n")
    return best_config, best_cost

#move is defined as only single node change from original config - config
#since move is defined as a single node change - finds the best node to change and its best partitioning option
def do_step(graph, graph_components, config, cost, include_db_initialization_cost):
    best_config = config.copy()
    best_cost = cost
    best_nodes_individual_cost = None

    for graph_component in graph_components:
        for partitioning_option in graph_component.partitioning_options:#for a single node - try all possible partitioning options
            if config.get(graph_component.unique_name) == partitioning_option:
                continue
            new_config = config.copy()#always start from original config
            new_config[graph_component.unique_name] = partitioning_option
            if check_config_is_valid(graph, new_config):
                tables_dict = define_the_generated_physical_schema(graph, new_config)
                table_mappings = generate_table_mappings(graph)  #table mapping - each table mapped to the representative node list based on chosen config
                table_widths = calculate_table_width_for_physical_tables_in_config(graph, new_config, table_mappings)
                folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, new_config, table_mappings)
                initialize_table_cover_for_nodes(graph, new_config)
                #table_widths not required, replaced to consider only tuple counts
                #when weak entity/relationship folded, weight of the tuples are multiplied by a constant factor per folded weak entity/relationship
                new_cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, new_config, tables_dict,
                                                                                     table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
                new_nodes_individual_cost = get_nodes_cost()
                if new_cost < best_cost:
                    best_config = new_config.copy()
                    best_cost = new_cost
                    best_nodes_individual_cost = new_nodes_individual_cost
    return best_config, best_cost, best_nodes_individual_cost


def greedy_search(graph, include_db_initialization_cost, iterations=0):
    reset_partitioning_options_for_node(graph)
    initialize_partitioning_options_for_node(graph)

    all_components = [graph_node for graph_node in graph.nodes if
                      graph_node.is_entity() or graph_node.is_relationship() or (
                              graph_node.is_attribute() and graph_node.is_multivalued)]

    #starting config
    config = {}
    for component in all_components:
        config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)

    """
    config["address"] = "contained_in_parent"
    config["pricehistory"] = "contained_in_parent"
    config["productimage"] = "contained_in_parent"
    config["productvariant"] = "contained_in_parent"
    config["browsingsession"] = "contained_in_parent"
    config["suppliercontact"] = "contained_in_parent"
    """


    tables_dict = define_the_generated_physical_schema(graph, config)
    table_mappings = generate_table_mappings(graph)
    table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
    folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
    initialize_table_cover_for_nodes(graph, config)
    cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict, table_widths,
                                                                folded_weak_entity_relationship_count, include_db_initialization_cost)#cost of the workload for the chosen config
    nodes_individual_cost = get_nodes_cost()
    print("default cost:", cost)

    best_config = config.copy()
    best_cost = cost
    best_nodes_individual_cost = nodes_individual_cost

    #for mvds it is obvious keeping them CIP is the best, so disregard mvds from the components to which options assigned
    all_components_except_mvd_attrs = [graph_node for graph_node in graph.nodes if
                                       graph_node.is_entity() or graph_node.is_relationship()]


    for iteration in range(iterations):#do a step at each iteration
        new_config, new_cost, new_nodes_individual_cost = do_step(graph, all_components_except_mvd_attrs, best_config, best_cost, include_db_initialization_cost)
        if new_cost < best_cost:
            best_config = new_config.copy()
            best_cost = new_cost
            best_nodes_individual_cost = new_nodes_individual_cost
        else:#no improvements - can stop greedy search
            assert new_cost == best_cost
            assert new_config == best_config
            print("greedy search stopped after {} iterations".format(iteration+1))
            break

    graph.config = best_config
    graph.cost = best_cost
    graph.nodes_cost = best_nodes_individual_cost
    define_the_generated_physical_schema(graph, best_config)  #update graph parameters for selected best config
    update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes(graph,
                                                                             best_config)  #update graph parameters for selected best config - required for mapping the select * entity queries - for child entities of partially_by_itself

    print("best config-greedy:", best_config)
    print("best cost-greedy:", best_cost, "\n")
    return best_config, best_cost

def greedy_search_with_random_starts(graph, include_db_initialization_cost, iterations=1000, random_starts=10):
    reset_partitioning_options_for_node(graph)
    initialize_partitioning_options_for_node(graph)

    all_components = [graph_node for graph_node in graph.nodes if
                      graph_node.is_entity() or graph_node.is_relationship() or (
                              graph_node.is_attribute() and graph_node.is_multivalued)]

    best_global_config = None
    best_global_cost = float('inf')
    best_nodes_individual_global_cost = None

    for i in range(random_starts):
        config = {}
        best_local_config = None
        best_local_cost = float('inf')
        best_nodes_individual_local_cost = None
        if i == 0:  #first random start based on default heuristics
            for component in all_components:
                config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)
            tables_dict = define_the_generated_physical_schema(graph, config)
            table_mappings = generate_table_mappings(graph)
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
            initialize_table_cover_for_nodes(graph, config)
            best_local_cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict,
                                                                table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
            best_local_config = config.copy()
            best_nodes_individual_local_cost = get_nodes_cost()

        else:  #next random starts randomly chosen
            bool_check = True
            while bool_check:
                for component in all_components:
                    if component.is_attribute() and component.is_multivalued:#for mvd attributes, it always makes sense to store as contained_in_parent
                        config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)
                    else:
                        config[component.unique_name] = random.choice(component.partitioning_options)
                if check_config_is_valid(graph, config):
                    bool_check = False  #found a valid config, exit from the loop
                else:
                    config = {}

            tables_dict = define_the_generated_physical_schema(graph, config)
            table_mappings = generate_table_mappings(
                graph)  #table mapping - each table mapped to the representative node list based on chosen config
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
            initialize_table_cover_for_nodes(graph, config)
            best_local_cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict,
                                                                table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
            best_local_config = config.copy()
            best_nodes_individual_local_cost = get_nodes_cost()

        #for mvds it is obvious keeping them CIP is the best, so disregard mvds from the components to which options assigned
        all_components_except_mvd_attrs = [graph_node for graph_node in graph.nodes if
                                           graph_node.is_entity() or graph_node.is_relationship()]

        for iteration in range(iterations):#do a step at each iteration
            new_config, new_cost, new_nodes_individual_cost = do_step(graph, all_components_except_mvd_attrs, best_local_config, best_local_cost, include_db_initialization_cost)
            if new_cost < best_local_cost:
                best_local_config = new_config.copy()
                best_local_cost = new_cost
                best_nodes_individual_local_cost = new_nodes_individual_cost
            else:#no improvements - can stop greedy search
                assert new_cost == best_local_cost
                assert new_config == best_local_config
                print("local greedy search for random start {} stopped after {} iterations".format(i+1, iteration+1))
                break

        if best_global_config is None:
            best_global_config = best_local_config.copy()
            best_global_cost = best_local_cost
            best_nodes_individual_global_cost = best_nodes_individual_local_cost
        else:
            if best_local_cost < best_global_cost:
                best_global_config = best_local_config.copy()
                best_global_cost = best_local_cost
                best_nodes_individual_global_cost = best_nodes_individual_local_cost

    graph.config = best_global_config
    graph.cost = best_global_cost
    graph.nodes_cost = best_nodes_individual_global_cost
    define_the_generated_physical_schema(graph, best_global_config)  #update graph parameters for selected best config
    update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes(graph,
                                                                             best_global_config)  #update graph parameters for selected best config

    print("best config-random starts:", best_global_config)
    print("best cost-random starts:", best_global_cost, "\n")
    return best_global_config, best_global_cost


def stochastic_greedy_search(graph, include_db_initialization_cost, iterations=0):
    reset_partitioning_options_for_node(graph)
    initialize_partitioning_options_for_node(graph)

    all_components = [graph_node for graph_node in graph.nodes if
                      graph_node.is_entity() or graph_node.is_relationship() or (
                              graph_node.is_attribute() and graph_node.is_multivalued)]

    #starting config
    config = {}
    best_cost = float('inf')
    for component in all_components:
        config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)

    #config["poitem"] = "contained_in_parent"
    #config["address"] = "contained_in_parent"
    #config["browsingsession"] = "contained_in_parent"
    #config["actor"] = "all_by_itself"
    #config["user"] = "no_table"
    #config["user"] = "contained_all_descendants"
    #config["phone"] = "contained_in_parent"
    #config["smartwatch"] = "contained_in_parent"
    #config["bundled_phone"] = "folded_to_many_side"
    #config["product"] = "contained_all_descendants"
    #config["electronics"] = "all_by_itself"
    #config["computer"] = "contained_in_parent"
    #config["desktop"] = "partially_by_itself"
    #config["laptop"] = "all_by_itself"
    #config["appliance"] = "contained_in_parent"
    #config["physical_product_reviews"] = "folded_to_many_side"
    #config["productimage"] = "contained_in_parent"

    """
    config["pricehistory"] = "contained_in_parent"
    config["productimage"] = "contained_in_parent"
    config["productvariant"] = "contained_in_parent"
    config["browsingsession"] = "contained_in_parent"


    options = ["all_by_itself", "partially_by_itself", "contained_in_parent"]
    random.seed(10)

    config["product"] = "all_by_itself"
    config["physicalproduct"] = random.choice(options)
    config["digitalproduct"] = random.choice(options)
    config["electronics"] = random.choice(options)
    config["computer"] = random.choice(options)
    config["desktop"] = random.choice(options)
    config["laptop"] = random.choice(options)
    config["tablet"] = random.choice(options)
    config["smartwatch"] = random.choice(options)
    config["camera"] = random.choice(options)
    config["phone"] = random.choice(options)
    config["accessories"] = random.choice(options)
    config["appliance"] = random.choice(options)
    config["kitchenappliance"] = random.choice(options)
    config["apparel"] = random.choice(options)
    config["clothing"] = random.choice(options)
    config["menclothing"] = random.choice(options)
    config["womenclothing"] = random.choice(options)
    config["footwear"] = random.choice(options)
    config["media"] = random.choice(options)
    config["software"] = random.choice(options)

    config["user"] = "all_by_itself"
    config["customer"] = random.choice(options)
    config["primecustomer"] = random.choice(options)
    config["businesscustomer"] = random.choice(options)
    config["employee"] = random.choice(options)
    config["corporateemployee"] = random.choice(options)
    config["engineer"] = random.choice(options)
    config["supportagent"] = random.choice(options)
    config["fulfillmentassociate"] = random.choice(options)
    config["categorymanager"] = random.choice(options)

    print("config: ", config)
    """



    tables_dict = define_the_generated_physical_schema(graph, config)
    table_mappings = generate_table_mappings(graph)
    table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
    folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
    initialize_table_cover_for_nodes(graph, config)
    best_cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict, table_widths,
                                                            folded_weak_entity_relationship_count, include_db_initialization_cost)#cost of the workload for the chosen config
    best_nodes_individual_cost = get_nodes_cost()
    print("default best cost:", best_cost)

    for iteration in range(iterations):
        index = random.randint(0, len(all_components) - 1)
        random_component = all_components[index]
        random_partitioning_option_index = random.randint(0, len(random_component.partitioning_options) - 1)
        new_config = config.copy()
        new_config[random_component.unique_name] = random_component.partitioning_options[
            random_partitioning_option_index]
        if check_config_is_valid(graph, new_config):
            tables_dict = define_the_generated_physical_schema(graph, new_config)
            table_mappings = generate_table_mappings(graph)  #table mapping - each table mapped to the representative node list based on chosen config
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, new_config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, new_config, table_mappings)
            initialize_table_cover_for_nodes(graph, new_config)
            #table_widths not required, replaced to consider only tuple counts
            #when weak entity/relationship folded, weight of the tuples are multiplied by a constant factor per folded weak entity/relationship
            cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, new_config, tables_dict,
                                                                                 table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
            if cost < best_cost:
                config = new_config
                best_cost = cost
                best_nodes_individual_cost = get_nodes_cost()
        else:
            continue

    graph.config = config
    graph.cost = best_cost
    graph.nodes_cost = best_nodes_individual_cost
    define_the_generated_physical_schema(graph, config)  #update graph parameters for selected best config
    update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes(graph,
                                                                             config)  #update graph parameters for selected best config - required for mapping the select * entity queries - for child entities of partially_by_itself

    print("best config-greedy:", config)
    print("best cost-greedy:", best_cost, "\n")
    return config, best_cost


def stochastic_greedy_search_with_random_starts(graph, include_db_initialization_cost, iterations=5000, random_starts=10):
    reset_partitioning_options_for_node(graph)
    initialize_partitioning_options_for_node(graph)

    all_components = [graph_node for graph_node in graph.nodes if
                      graph_node.is_entity() or graph_node.is_relationship() or (
                              graph_node.is_attribute() and graph_node.is_multivalued)]

    best_global_config = None
    best_global_cost = float('inf')
    best_nodes_individual_global_cost = None

    for i in range(random_starts):
        config = {}
        best_local_cost = float('inf')
        if i == 0:  #first random start based on default heuristics
            for component in all_components:
                config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)
            tables_dict = define_the_generated_physical_schema(graph, config)
            table_mappings = generate_table_mappings(graph)
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
            initialize_table_cover_for_nodes(graph, config)
            best_local_cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict,
                                            table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
            best_nodes_individual_local_cost = get_nodes_cost()

        else:  #next random starts randomly chosen
            """
            def get_random_initial_valid_configuration(graph, all_components, config):
                for component in all_components:
                    config[component.unique_name] = random.choice(component.partitioning_options)
                if check_config_is_valid(graph, config):
                    return config
                else:
                    config = {}
                    return get_random_initial_valid_configuration(graph, all_components, config)

            config = get_random_initial_valid_configuration(graph, all_components, config)
            """
            #instead of recursion, replaced with an iterative approach since recursion exceeds the depth(get_random_initial_valid_configuration calling itself until depth exceeded)
            # trying to find a valid configuration
            bool_check = True
            while bool_check:
                for component in all_components:
                    config[component.unique_name] = random.choice(component.partitioning_options)
                if check_config_is_valid(graph, config):
                    bool_check = False  #found a valid config, exit from the loop
                else:
                    config = {}

            tables_dict = define_the_generated_physical_schema(graph, config)
            table_mappings = generate_table_mappings(
                graph)  #table mapping - each table mapped to the representative node list based on chosen config
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
            initialize_table_cover_for_nodes(graph, config)
            best_local_cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict,
                                table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
            best_nodes_individual_local_cost = get_nodes_cost()

        for iteration in range(iterations):
            index = random.randint(0, len(all_components) - 1)
            random_component = all_components[index]
            random_partitioning_option_index = random.randint(0, len(random_component.partitioning_options) - 1)
            new_config = config.copy()
            new_config[random_component.unique_name] = random_component.partitioning_options[
                random_partitioning_option_index]
            if check_config_is_valid(graph, new_config):
                tables_dict = define_the_generated_physical_schema(graph, new_config)
                table_mappings = generate_table_mappings(
                    graph)  #table mapping - each table mapped to the representative node list based on chosen config
                table_widths = calculate_table_width_for_physical_tables_in_config(graph, new_config, table_mappings)
                folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, new_config, table_mappings)
                initialize_table_cover_for_nodes(graph, new_config)
                cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, new_config, tables_dict,
                                    table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
                if cost < best_local_cost:
                    config = new_config
                    best_local_cost = cost
                    best_nodes_individual_local_cost = get_nodes_cost()
            else:
                continue

        if best_global_config is None:
            best_global_config = config
            best_global_cost = best_local_cost
            best_nodes_individual_global_cost = best_nodes_individual_local_cost
        else:
            if best_local_cost < best_global_cost:
                best_global_config = config
                best_global_cost = best_local_cost
                best_nodes_individual_global_cost = best_nodes_individual_local_cost

    graph.config = best_global_config
    graph.cost = best_global_cost
    graph.nodes_cost = best_nodes_individual_global_cost
    define_the_generated_physical_schema(graph, best_global_config)  #update graph parameters for selected best config
    update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes(graph,
                                                                             best_global_config)  #update graph parameters for selected best config

    print("best config-random starts:", best_global_config)
    print("best cost-random starts:", best_global_cost, "\n")
    return best_global_config, best_global_cost

#execute the greedy search for defined no of runs- each run search for a solution using defined no of iterations
#purpose is to see if the solution gets better as no of runs increases
#if solution doesn't improve over the runs, we can assume that we almost reach the optimal solution
def progressive_stochastic_greedy_search(graph, run, include_db_initialization_cost, iterations=0):
    reset_partitioning_options_for_node(graph)
    initialize_partitioning_options_for_node(graph)

    #starting config
    if run == 0:
        all_components = [graph_node for graph_node in graph.nodes if
                          graph_node.is_entity() or graph_node.is_relationship() or (
                                  graph_node.is_attribute() and graph_node.is_multivalued)]
        config = {}
        best_cost = float('inf')
        for component in all_components:
            config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)
    else:
        config = graph.config#run the greedy for iterations no of steps starting from previously found config
        best_cost = graph.cost

    #for mvds it is obvious keeping them CIP is the best, so disregard mvds from the components to which options randomly assigned
    all_components_except_mvd_attrs = [graph_node for graph_node in graph.nodes if
                                       graph_node.is_entity() or graph_node.is_relationship()]

    tables_dict = define_the_generated_physical_schema(graph, config)
    table_mappings = generate_table_mappings(graph)
    table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
    folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
    initialize_table_cover_for_nodes(graph, config)
    best_cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict, table_widths,
                                                        folded_weak_entity_relationship_count, include_db_initialization_cost)#cost of the workload for the chosen config
    best_nodes_individual_cost = get_nodes_cost()
    print("default best cost:", best_cost)

    for iteration in range(iterations):
        index = random.randint(0, len(all_components_except_mvd_attrs) - 1)
        random_component = all_components_except_mvd_attrs[index]
        random_partitioning_option_index = random.randint(0, len(random_component.partitioning_options) - 1)
        new_config = config.copy()
        new_config[random_component.unique_name] = random_component.partitioning_options[
            random_partitioning_option_index]
        if check_config_is_valid(graph, new_config):
            tables_dict = define_the_generated_physical_schema(graph, new_config)
            table_mappings = generate_table_mappings(graph)  #table mapping - each table mapped to the representative node list based on chosen config
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, new_config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, new_config, table_mappings)
            initialize_table_cover_for_nodes(graph, new_config)
            #table_widths not required, replaced to consider only tuple counts
            #when weak entity/relationship folded, weight of the tuples are multiplied by a constant factor per folded weak entity/relationship
            cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, new_config, tables_dict,
                                table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
            if cost < best_cost:
                config = new_config
                best_cost = cost
                best_nodes_individual_cost = get_nodes_cost()
        else:
            continue

    graph.config = config
    graph.cost = best_cost
    graph.nodes_cost = best_nodes_individual_cost
    define_the_generated_physical_schema(graph, config)  #update graph parameters for selected best config
    update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes(graph,
                                                                             config)  #update graph parameters for selected best config - required for mapping the select * entity queries - for child entities of partially_by_itself

    print("best config-greedy:", config)
    print("best cost-greedy:", best_cost, "\n")
    return config, best_cost

#execute the greedy search with random starts for defined no of runs- each run search for a solution using defined no of iterations
#purpose is to see if the solution gets better as no of runs increases
#if solution doesn't improve over the runs, we can assume that we almost reach the optimal solution
def progressive_stochastic_greedy_search_with_random_starts(graph, run, include_db_initialization_cost, iterations=0, random_starts=10):
    reset_partitioning_options_for_node(graph)
    initialize_partitioning_options_for_node(graph)

    #after initial progressive run
    if run != 0:
        config_from_previous_run = graph.config
        cost_for_previous_run = graph.cost

    all_components = [graph_node for graph_node in graph.nodes if
                      graph_node.is_entity() or graph_node.is_relationship() or (
                              graph_node.is_attribute() and graph_node.is_multivalued)]

    best_global_config = None
    best_global_cost = float('inf')
    best_nodes_individual_global_cost = None

    for i in range(random_starts):
        config = {}
        best_local_cost = float('inf')
        if run == 0 and i == 0:  #for progressive greedy, for first run, first random start based on default heuristics
            for component in all_components:
                config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)
            tables_dict = define_the_generated_physical_schema(graph, config)
            table_mappings = generate_table_mappings(graph)
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
            initialize_table_cover_for_nodes(graph, config)
            best_local_cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict,
                                    table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
            best_nodes_individual_local_cost = get_nodes_cost()

        elif run != 0 and i == 0: #for progressive greedy, for next runs, first random start based on previously found config
            config = graph.config#run the greedy for iterations no of steps starting from previously found config
            tables_dict = define_the_generated_physical_schema(graph, config)
            table_mappings = generate_table_mappings(graph)
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
            initialize_table_cover_for_nodes(graph, config)
            best_local_cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict,
                                table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
            best_nodes_individual_local_cost = get_nodes_cost()
            assert best_local_cost == cost_for_previous_run

        else:#next random starts randomly chosen
            assert i !=0
            #instead of recursion, replaced with an iterative approach since recursion exceeds the depth(get_random_initial_valid_configuration calling itself until depth exceeded)
            # trying to find a valid configuration
            bool_check = True
            while bool_check:
                for component in all_components:
                    if component.is_attribute() and component.is_multivalued:#for mvd attributes, it always makes sense to store as contained_in_parent
                        config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)
                    else:
                        config[component.unique_name] = random.choice(component.partitioning_options)
                if check_config_is_valid(graph, config):
                    bool_check = False  #found a valid config, exit from the loop
                else:
                    config = {}

            tables_dict = define_the_generated_physical_schema(graph, config)
            table_mappings = generate_table_mappings(
                graph)  #table mapping - each table mapped to the representative node list based on chosen config
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
            initialize_table_cover_for_nodes(graph, config)
            best_local_cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, config, tables_dict,
                                table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
            best_nodes_individual_local_cost = get_nodes_cost()

        #for mvds it is obvious keeping them CIP is the best, so disregard mvds from the components to which options randomly assigned
        all_components_except_mvd_attrs = [graph_node for graph_node in graph.nodes if
                                       graph_node.is_entity() or graph_node.is_relationship()]

        for iteration in range(iterations):
            index = random.randint(0, len(all_components_except_mvd_attrs) - 1)
            random_component = all_components_except_mvd_attrs[index]
            random_partitioning_option_index = random.randint(0, len(random_component.partitioning_options) - 1)
            new_config = config.copy()
            new_config[random_component.unique_name] = random_component.partitioning_options[
                random_partitioning_option_index]
            if check_config_is_valid(graph, new_config):
                tables_dict = define_the_generated_physical_schema(graph, new_config)
                table_mappings = generate_table_mappings(
                    graph)  #table mapping - each table mapped to the representative node list based on chosen config
                table_widths = calculate_table_width_for_physical_tables_in_config(graph, new_config, table_mappings)
                folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, new_config, table_mappings)
                initialize_table_cover_for_nodes(graph, new_config)
                cost = calculate_insert_select_cost_for_entity_relationship_workload(graph, new_config, tables_dict,
                                    table_widths, folded_weak_entity_relationship_count, include_db_initialization_cost)
                if cost < best_local_cost:
                    config = new_config
                    best_local_cost = cost
                    best_nodes_individual_local_cost = get_nodes_cost()
            else:
                continue

        if best_global_config is None:
            best_global_config = config
            best_global_cost = best_local_cost
            best_nodes_individual_global_cost = best_nodes_individual_local_cost
        else:
            if best_local_cost < best_global_cost:
                best_global_config = config
                best_global_cost = best_local_cost
                best_nodes_individual_global_cost = best_nodes_individual_local_cost

    graph.config = best_global_config
    graph.cost = best_global_cost
    graph.nodes_cost = best_nodes_individual_global_cost
    define_the_generated_physical_schema(graph, best_global_config)  #update graph parameters for selected best config
    update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes(graph,
                                                                             best_global_config)  #update graph parameters for selected best config

    print("best config-random starts:", best_global_config)
    print("best cost-random starts:", best_global_cost, "\n")
    return best_global_config, best_global_cost


def calculate_insert_select_cost_for_entity_relationship_for_workload_for_baselines(graph, config, tables_dict, table_widths,
                                                                  folded_weak_entity_relationship_count):  #select, insert - workload queries have single entity or relationship
    #cost = 0
    workload_cost_for_nodes = {"select":{}, "insert":{}}

    #workload select * queries - select cost
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            node_workload_select_cost = calculate_select_cost_for_single_entity_or_relationship_helper(graph, node, config, tables_dict, table_widths,
                                                                                   folded_weak_entity_relationship_count)
            workload_cost_for_nodes.get("select")[node.unique_name] = node_workload_select_cost
            #cost += node_select_cost

    #workload insert queries - insert cost
    #workload_insert_cost = 0
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship() or (node.is_attribute() and node.is_multivalued and node.is_in_separate_table):
            node_workload_insert_cost = calculate_total_workload_insert_cost_for_single_entity_or_relationship_helper(graph, node, config, tables_dict)
            workload_cost_for_nodes.get("insert")[node.unique_name] = node_workload_insert_cost
            #workload_insert_cost += node_workload_insert_cost
    #node_cost["workload_insert_cost"] = workload_insert_cost
    #print("workload insert cost: ", workload_insert_cost)
    #cost += workload_insert_cost
    #return cost

    return workload_cost_for_nodes

def find_node_costs_for_workload_for_baselines_helper(graph, baseline, all_components, config):
    if baseline == "ABI":
        for component in all_components:
            if component.node_type_for_partitioning_options == "sub_class":
                config[component.unique_name] = partitioning_options['sub_class'].get(2)
            elif component.node_type_for_partitioning_options == "1_N_relationship":
                config[component.unique_name] = partitioning_options['1_N_relationship'].get(2)
    elif baseline == "ABI_folded":
        for component in all_components:
            if component.node_type_for_partitioning_options == "sub_class":
                config[component.unique_name] = partitioning_options['sub_class'].get(2)
            elif component.node_type_for_partitioning_options == "1_N_relationship":
                config[component.unique_name] = partitioning_options['1_N_relationship'].get(1)
    elif baseline == "PBI":
        for component in all_components:
            if component.node_type_for_partitioning_options == "sub_class":
                config[component.unique_name] = partitioning_options['sub_class'].get(3)
            elif component.node_type_for_partitioning_options == "1_N_relationship":
                config[component.unique_name] = partitioning_options['1_N_relationship'].get(2)
    elif baseline == "PBI_folded":
        for component in all_components:
            if component.node_type_for_partitioning_options == "sub_class":
                config[component.unique_name] = partitioning_options['sub_class'].get(3)
            elif component.node_type_for_partitioning_options == "1_N_relationship":
                config[component.unique_name] = partitioning_options['1_N_relationship'].get(1)
    elif baseline == "CIP":
        for component in all_components:
            if component.node_type_for_partitioning_options == "sub_class":
                config[component.unique_name] = partitioning_options['sub_class'].get(4)
            elif component.node_type_for_partitioning_options == "1_N_relationship":
                config[component.unique_name] = partitioning_options['1_N_relationship'].get(2)
    elif baseline == "CIP_folded":
        for component in all_components:
            if component.node_type_for_partitioning_options == "sub_class":
                config[component.unique_name] = partitioning_options['sub_class'].get(4)
            elif component.node_type_for_partitioning_options == "1_N_relationship":
                config[component.unique_name] = partitioning_options['1_N_relationship'].get(1)

    tables_dict = define_the_generated_physical_schema(graph, config)
    table_mappings = generate_table_mappings(graph)
    table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
    folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
    initialize_table_cover_for_nodes(graph, config)
    return calculate_insert_select_cost_for_entity_relationship_for_workload_for_baselines(graph, config, tables_dict, table_widths,
                                                                                       folded_weak_entity_relationship_count)

def find_node_costs_for_workload_for_baselines(graph):
    all_components = [graph_node for graph_node in graph.nodes if
                      graph_node.is_entity() or graph_node.is_relationship() or (
                              graph_node.is_attribute() and graph_node.is_multivalued)]
    config = {}
    for component in all_components:
        config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)

    node_costs_for_baselines = {}

    #ABI
    baseline = "ABI"
    config_ABI = config.copy()
    node_costs_for_baselines[baseline] = find_node_costs_for_workload_for_baselines_helper(graph, baseline, all_components, config_ABI)
    #ABI_folded
    baseline = "ABI_folded"
    config_ABI_folded = config.copy()
    node_costs_for_baselines[baseline] = find_node_costs_for_workload_for_baselines_helper(graph, baseline, all_components, config_ABI_folded)
    #PBI
    baseline = "PBI"
    config_PBI = config.copy()
    node_costs_for_baselines[baseline] = find_node_costs_for_workload_for_baselines_helper(graph, baseline, all_components, config_PBI)
    #PBI_folded
    baseline = "PBI_folded"
    config_PBI_folded = config.copy()
    node_costs_for_baselines[baseline] = find_node_costs_for_workload_for_baselines_helper(graph, baseline, all_components, config_PBI_folded)
    #CIP
    baseline = "CIP"
    config_CIP = config.copy()
    node_costs_for_baselines[baseline] = find_node_costs_for_workload_for_baselines_helper(graph, baseline, all_components, config_CIP)
    #CIP_folded
    baseline = "CIP_folded"
    config_CIP_folded = config.copy()
    node_costs_for_baselines[baseline] = find_node_costs_for_workload_for_baselines_helper(graph, baseline, all_components, config_CIP_folded)

    return node_costs_for_baselines


#define 6 baselines: ABI, ABI+folded, PBI, PBI+folded, CIP, CIP+folded
def find_minimum_node_costs_for_workload_for_baselines(graph):
    baselines = ["ABI", "ABI_folded", "PBI", "PBI_folded", "CIP", "CIP_folded"]
    node_costs_for_baselines = find_node_costs_for_workload_for_baselines(graph)

    minimum_node_costs_across_baselines = {"select":{}, "insert":{}}

    for node in node_costs_for_baselines[baselines[0]]["select"]:
        min_node_cost_for_select_workload = node_costs_for_baselines[baselines[0]]["select"][node]
        for baseline in baselines[1:]:
            if node_costs_for_baselines[baseline]["select"][node] < min_node_cost_for_select_workload:
                min_node_cost_for_select_workload = node_costs_for_baselines[baseline]["select"][node]
        minimum_node_costs_across_baselines["select"][node] = min_node_cost_for_select_workload

    for node in node_costs_for_baselines[baselines[0]]["insert"]:
        min_node_cost_for_insert_workload = node_costs_for_baselines[baselines[0]]["insert"][node]
        for baseline in baselines[1:]:
            if node_costs_for_baselines[baseline]["insert"][node] < min_node_cost_for_insert_workload:
                min_node_cost_for_insert_workload = node_costs_for_baselines[baseline]["insert"][node]
        minimum_node_costs_across_baselines["insert"][node] = min_node_cost_for_insert_workload

    return minimum_node_costs_across_baselines


def calculate_insert_select_normalized_cost_for_entity_relationship_workload(graph, config, tables_dict, table_widths,
                                                                  folded_weak_entity_relationship_count, minimum_node_costs_across_baselines):  #select, insert - workload queries have single entity or relationship
    normalized_cost = 0

    #workload select * queries - select cost
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            cost = calculate_select_cost_for_single_entity_or_relationship_helper(graph, node, config, tables_dict, table_widths,
                                                                                   folded_weak_entity_relationship_count)
            if cost != 0:
                assert node.workload_select_frequency != 0
                cost = cost/minimum_node_costs_across_baselines.get("select").get(node.unique_name)
                normalized_cost += cost

    #workload insert queries - insert cost
    workload_insert_normalized_cost = 0
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship() or (node.is_attribute() and node.is_multivalued and node.is_in_separate_table):
            cost = calculate_total_workload_insert_cost_for_single_entity_or_relationship_helper(graph, node, config, tables_dict)
            #normalize costs for entity or relationships only - assume mvd attributes are by default in CIP option
            if node.is_entity() or node.is_relationship():
                if cost != 0:
                    assert node.workload_insert_frequency != 0
                    cost = cost/minimum_node_costs_across_baselines.get("insert").get(node.unique_name)
                    workload_insert_normalized_cost += cost
    node_cost["workload_insert_cost"] =  workload_insert_normalized_cost
    #print("workload insert cost: ", workload_insert_cost)
    normalized_cost +=  workload_insert_normalized_cost

    return normalized_cost

def do_step_with_normalized_costs(graph, graph_components, config, cost, minimum_node_costs_for_workload_across_baselines):
    best_config = config.copy()
    best_cost = cost
    best_nodes_individual_cost = None

    for graph_component in graph_components:
        for partitioning_option in graph_component.partitioning_options:#for a single node - try all possible partitioning options
            if config.get(graph_component.unique_name) == partitioning_option:
                continue
            new_config = config.copy()#always start from original config
            new_config[graph_component.unique_name] = partitioning_option
            if check_config_is_valid(graph, new_config):
                tables_dict = define_the_generated_physical_schema(graph, new_config)
                table_mappings = generate_table_mappings(graph)  #table mapping - each table mapped to the representative node list based on chosen config
                table_widths = calculate_table_width_for_physical_tables_in_config(graph, new_config, table_mappings)
                folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, new_config, table_mappings)
                initialize_table_cover_for_nodes(graph, new_config)
                #table_widths not required, replaced to consider only tuple counts
                #when weak entity/relationship folded, weight of the tuples are multiplied by a constant factor per folded weak entity/relationship
                new_cost = calculate_insert_select_normalized_cost_for_entity_relationship_workload(graph, new_config, tables_dict,
                                                                table_widths, folded_weak_entity_relationship_count, minimum_node_costs_for_workload_across_baselines)
                new_nodes_individual_cost = get_nodes_cost()
                if new_cost < best_cost:
                    best_config = new_config.copy()
                    best_cost = new_cost
                    best_nodes_individual_cost = new_nodes_individual_cost
    return best_config, best_cost, best_nodes_individual_cost


#search for minimum total cost where workload cost for each node is normalized by the min cost for node found across 6 baselines
#baselines - ABI, ABI+folded, PBI, PBI+folded, CIP, CIP+folded
def greedy_search_with_random_starts_for_obj_of_optimizing_for_normalized_costs(graph, iterations=1000, random_starts=10):
    reset_partitioning_options_for_node(graph)
    initialize_partitioning_options_for_node(graph)

    minimum_node_costs_for_workload_across_baselines = find_minimum_node_costs_for_workload_for_baselines(graph)

    all_components = [graph_node for graph_node in graph.nodes if
                      graph_node.is_entity() or graph_node.is_relationship() or (
                              graph_node.is_attribute() and graph_node.is_multivalued)]

    best_global_config = None
    best_global_cost = float('inf')
    best_nodes_individual_global_cost = None

    for i in range(random_starts):
        config = {}
        best_local_config = None
        best_local_cost = float('inf')
        best_nodes_individual_local_cost = None
        if i == 0:  #first random start based on default heuristics
            for component in all_components:
                config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)
            tables_dict = define_the_generated_physical_schema(graph, config)
            table_mappings = generate_table_mappings(graph)
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
            initialize_table_cover_for_nodes(graph, config)
            best_local_cost = calculate_insert_select_normalized_cost_for_entity_relationship_workload(graph, config, tables_dict,
                                                            table_widths, folded_weak_entity_relationship_count, minimum_node_costs_for_workload_across_baselines)
            best_local_config = config.copy()
            best_nodes_individual_local_cost = get_nodes_cost()

        else:  #next random starts randomly chosen
            bool_check = True
            while bool_check:
                for component in all_components:
                    if component.is_attribute() and component.is_multivalued:#for mvd attributes, it always makes sense to store as contained_in_parent
                        config[component.unique_name] = heuristic_default_option(component.node_type_for_partitioning_options)
                    else:
                        config[component.unique_name] = random.choice(component.partitioning_options)
                if check_config_is_valid(graph, config):
                    bool_check = False  #found a valid config, exit from the loop
                else:
                    config = {}

            tables_dict = define_the_generated_physical_schema(graph, config)
            table_mappings = generate_table_mappings(
                graph)  #table mapping - each table mapped to the representative node list based on chosen config
            table_widths = calculate_table_width_for_physical_tables_in_config(graph, config, table_mappings)
            folded_weak_entity_relationship_count = get_folded_relationship_weak_entity_count_for_tables(graph, config, table_mappings)
            initialize_table_cover_for_nodes(graph, config)
            best_local_cost = calculate_insert_select_normalized_cost_for_entity_relationship_workload(graph, config, tables_dict,
                                                            table_widths, folded_weak_entity_relationship_count, minimum_node_costs_for_workload_across_baselines)
            best_local_config = config.copy()
            best_nodes_individual_local_cost = get_nodes_cost()

        #for mvds it is obvious keeping them CIP is the best, so disregard mvds from the components to which options assigned
        all_components_except_mvd_attrs = [graph_node for graph_node in graph.nodes if
                                           graph_node.is_entity() or graph_node.is_relationship()]

        for iteration in range(iterations):#do a step at each iteration
            new_config, new_cost, new_nodes_individual_cost = do_step_with_normalized_costs(graph, all_components_except_mvd_attrs, best_local_config, best_local_cost,
                                                                                            minimum_node_costs_for_workload_across_baselines)
            if new_cost < best_local_cost:
                best_local_config = new_config.copy()
                best_local_cost = new_cost
                best_nodes_individual_local_cost = new_nodes_individual_cost
            else:#no improvements - can stop greedy search
                assert new_cost == best_local_cost
                assert new_config == best_local_config
                print("local greedy search for random start {} stopped after {} iterations".format(i+1, iteration+1))
                break

        if best_global_config is None:
            best_global_config = best_local_config.copy()
            best_global_cost = best_local_cost
            best_nodes_individual_global_cost = best_nodes_individual_local_cost
        else:
            if best_local_cost < best_global_cost:
                best_global_config = best_local_config.copy()
                best_global_cost = best_local_cost
                best_nodes_individual_global_cost = best_nodes_individual_local_cost

    graph.config = best_global_config
    graph.cost = best_global_cost
    graph.nodes_cost = best_nodes_individual_global_cost
    define_the_generated_physical_schema(graph, best_global_config)  #update graph parameters for selected best config
    update_immediate_parent_with_all_by_itself_for_partially_by_itself_nodes(graph,
                                                                             best_global_config)  #update graph parameters for selected best config

    print("best config-random starts:", best_global_config)
    print("best cost-random starts:", best_global_cost, "\n")
    return best_global_config, best_global_cost
