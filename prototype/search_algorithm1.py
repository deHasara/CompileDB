from itertools import product
from partition_rules import check_conditions_for_abstract_table
from cost_model import insert_cost, search_cost, scan_cost, union_all_cost, sort_merge_join_cost

#for no_table -> node.mapped_table is None
partitioning_options = {
    "entity": {1: "all_by_itself", 2: "no_table"},
    "weak_entity": {1: "all_by_itself", 2:"contained_in_parent"},
    "sub_class": {1: "all_by_itself", 2: "partially_by_itself", 3: "contained_in_parent"},
    "1_N_relationship": {1: "folded_to_many_side", 2:"all_by_itself"},
    "M_N_relationship": {1:"all_by_itself"},
    "composite_attribute": {1:"flattened", 2:"unflattened"},
    "multi_valued_attribute": {1:"all_by_itself", 2:"contained_in_parent"}
}

# Set of options that produce a physical table
materialized_options = {
    "entity": ["all_by_itself"],
    "weak_entity": ["all_by_itself"],
    "sub_class": ["all_by_itself", "partially_by_itself"],
    "1_N_relationship": ["all_by_itself"],
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["all_by_itself"]
}

#default options for node_type
default_options = {
    "entity": ["all_by_itself"],
    "weak_entity": ["all_by_itself"],
    "sub_class": ["partially_by_itself"],
    "1_N_relationship": ["folded_to_many_side"],
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["all_by_itself"]
}

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


def check_if_a_parent_entity_be_no_table(graph, node):#check if parent entity can have option to have no physical table
    #for this to happen parent entity insert frequency should be 0, all immediate children should have total participation, and it shouldn't participate in a relationship
    if node.insert_frequency==0:
        if not check_if_entity_participates_in_a_relationship(graph, node):
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
    if node.is_entity() and len(node.children) !=0:#check if the node is a parent entity not a regular entity or leaf entity in hierarchy(regular and leaf entity has no children)
        check_if_a_parent_entity_be_no_table(graph, node)
        if node.is_option_to_be_abstract:
            if partitioning_options['entity'].get(2):
                node.partitioning_options.append(partitioning_options['entity'].get(2))

def initialize_partitioning_options_for_node_helper(node, node_type):
    node.partitioning_options.extend(partitioning_options[node_type].values())


def initialize_partitioning_options_for_node(graph):
    for node in graph.nodes:
        add_abstract_option_for_possible_nodes(graph, node)
        if node.is_entity() and not node.is_subclass and not node.is_weak_entity:
            node.node_type_for_partitioning_options = 'entity'
            node.partitioning_options.append(partitioning_options['entity'].get(1))
        elif node.is_entity() and node.is_subclass:
            node.node_type_for_partitioning_options = 'sub_class'
            initialize_partitioning_options_for_node_helper(node, "sub_class")
        elif node.is_entity() and node.is_weak_entity:
            node.node_type_for_partitioning_options = 'weak_entity'
            initialize_partitioning_options_for_node_helper(node, "weak_entity")
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

def get_node_tables_for_no_table_parent_in_hierarchy(graph, node):
    assert len(node.children) > 0
    node_tables_set = {t[1] for t in node.node_tables}
    if node.children is not None:
        for child_node in node.children:
            new_tables = {t for t in child_node.node_tables if t[1] not in node_tables_set}
            node.node_tables |= new_tables

def figure_out_mappings(graph, node_list):
    for node in node_list:
        if node.is_entity():
            node.node_tables = set()#avoid duplicates
            if node.mapped_table:
                node.node_tables.add(node.mapped_table)
            for attribute in node.attributes:
                if attribute in node_list and attribute.is_multivalued and attribute.is_in_separate_table:
                    node.node_tables.add(attribute.mapped_table)
            if node.is_subclass: #for this to work, tables should be added by iterating through nodes from top to bottom in class hierarchy
                if node.is_parent_in_table:#contained in parent - single table inheritance
                    #node_tables_set = {t[1] for t in node.node_tables}
                    #new_tables = {t for t in node.parent_entity.node_tables if t[1] not in node_tables_set}
                    #node.node_tables |= new_tables
                    node.node_tables |= node.parent_entity.node_tables
                elif node.is_partially_by_itself:#partially by itself - class table inheritance
                    #node_tables_set = {t[1] for t in node.node_tables}
                    #new_tables = {t for t in node.parent_entity.node_tables if t[1] not in node_tables_set}
                    #node.node_tables |= new_tables
                    node.node_tables |= node.parent_entity.node_tables
                else:#all by itself - concrete table inheritance - parent may or may not be present
                    #node_tables_set = {t[1] for t in node.node_tables}
                    #new_tables = {t for t in node.parent_entity.node_tables if t[1] not in node_tables_set}
                    #node.node_tables |= new_tables
                    node.node_tables |= node.parent_entity.node_tables


        elif node.is_relationship():#for this to work, all entities node_tables should be added before adding node_tables for relationships
            node.node_tables = set()#avoid duplicates
            node.node_tables.add(node.mapped_table)
            for attribute in node.attributes:
                if attribute in node_list and attribute.is_multivalued and attribute.is_in_separate_table:
                    node.node_tables.add(attribute.mapped_table)


    #after mapping - check for nodes which didn't get mapped to tables - these are parent entities in inheritance hierarchy - this happen when no table option is chosen
    #for node in graph.nodes[::-1]:#this should be updated in reverse order - bottom to top - start with bottom most parent, update it, then go up
    for node in node_list[::-1]:
        if node.is_entity():
            if not node.mapped_table:#node doesn't map to any table - e.g. if person table doesn't exist-> need to map person queries to union of subclasses
                #this happens within class hierarchies only
                get_node_tables_for_no_table_parent_in_hierarchy(graph, node)

def reset_mapped_table_for_nodes(graph):
    for node in graph.nodes:
        node.mapped_table = None

def reset_node_tables(graph):
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            node.node_tables = set()

def reset_node_options(graph):
    for node in graph.nodes:
        if node.is_entity():
            node.is_contained_in_parent = False
            node.is_partially_by_itself = False
            node.is_all_by_itself = False
            node.immediate_parent_with_all_by_itself_unique_name = None
        elif node.is_attribute() :
            node.is_in_separate_table = False

def initialize_mapped_table_for_non_materialized_nodes(graph, node_list, config):
    #for node in graph.nodes:
    for node in node_list:
        if node.is_entity() and not node.is_subclass and not node.is_weak_entity:#abstract parent class
            if config[node.unique_name] not in materialized_options["entity"]:
                node.mapped_table = None
        elif node.is_entity() and  node.is_subclass:
            if config[node.unique_name] not in materialized_options["sub_class"]:
                if config[node.unique_name] == "contained_in_parent":
                    node.mapped_table = node.parent_entity.mapped_table
                    node.is_contained_in_parent = True
                    node.is_partially_by_itself = False
                    node.is_all_by_itself = False
                else:#no table
                    node.mapped_table = None
        elif node.is_entity() and node.is_weak_entity:
            if config[node.unique_name] not in materialized_options["weak_entity"]:
                node.mapped_table = node.parent_entity.mapped_table
                node.is_contained_in_parent = True
                node.is_partially_by_itself = False
                node.is_all_by_itself = False
        elif node.is_relationship() and check_if_relationship_is_1_N(node):
            if config[node.unique_name] not in materialized_options["1_N_relationship"]:
                node.mapped_table = node.entity2.mapped_table if not node.rel_dict['entity2']['one'] else node.entity1.mapped_table
        elif node.is_attribute() and node.is_multivalued:
            if config[node.unique_name] not in materialized_options["multi_valued_attribute"]:
                node.is_in_separate_table = False
                node.mapped_table = node.entity.mapped_table


def define_the_generated_physical_schema(graph, node_list, config):
    reset_mapped_table_for_nodes(graph)
    reset_node_tables(graph)
    reset_node_options(graph)
    tables = []
    tables_dict = {}#table_name:cardinality
    rel_name = "relation_"
    i=0
    for node in node_list:
        if node.is_entity() and not node.is_subclass and not node.is_weak_entity:#if the entity is root of hieraarchy, then table size cannot be determined at this step
            if config[node.unique_name] in materialized_options["entity"]:
                tables.append(rel_name + str(i))
                node.mapped_table = (node.sort_key, rel_name + str(i))#node mapped table -> (node.sort_key, rel_name)
                tables_dict[node.mapped_table[1]] = (node.relation_size, node.relation_size)#(relation_size, entity_distinct_keys)
                i+=1
                node.is_all_by_itself = True
        elif node.is_entity() and node.is_subclass:
            if config[node.unique_name] in materialized_options["sub_class"]:
                tables.append(rel_name + str(i))
                node.mapped_table = (node.sort_key, rel_name + str(i))
                tables_dict[node.mapped_table[1]] = (node.relation_size, node.relation_size)
                i+=1
                node.is_partially_by_itself = True if config[node.unique_name]=="partially_by_itself" else False
                node.is_all_by_itself = True if config[node.unique_name]=="all_by_itself" else False
                node.is_contained_in_parent = False
        elif node.is_entity() and node.is_weak_entity:
            if config[node.unique_name] in materialized_options["weak_entity"]:
                tables.append(rel_name + str(i))
                node.mapped_table = (node.sort_key, rel_name + str(i))
                tables_dict[node.mapped_table[1]] = (node.relation_size, node.relation_size)#(relation_size, entity_distinct_keys)
                i+=1
                node.is_contained_in_parent = False
                node.is_partially_by_itself = False
                node.is_all_by_itself = True
        elif node.is_relationship():
            if check_if_relationship_is_1_N(node):
                if config[node.unique_name] in materialized_options["1_N_relationship"]:
                    tables.append(rel_name + str(i))
                    node.mapped_table = (node.sort_key, rel_name + str(i))
                    tables_dict[node.mapped_table[1]] = (node.relation_size, node.entity1.relation_size, node.entity2.relation_size)#(relation_size, entity1_distinct_keys, entity2_distinct_keys) - here relation size equal many side relation size
                    i+=1
            else:
                if config[node.unique_name] in materialized_options["M_N_relationship"]:
                    tables.append(rel_name + str(i))
                    node.mapped_table = (node.sort_key, rel_name + str(i))
                    tables_dict[node.mapped_table[1]] = (node.relation_size, node.entity1.relation_size, node.entity2.relation_size)#(relation_size, entity1_distinct_keys, entity2_distinct_keys)
                    i+=1
        elif node.is_attribute() and node.is_multivalued:
            if config[node.unique_name] in materialized_options["multi_valued_attribute"]:
                tables.append(rel_name + str(i))
                node.mapped_table = (node.sort_key, rel_name + str(i))
                tables_dict[node.mapped_table[1]] = (node.relation_size, node.entity.relation_size)#(relation_size, entity_distinct_keys)
                i+=1
                node.is_in_separate_table = True

    initialize_mapped_table_for_non_materialized_nodes(graph, node_list, config)

    figure_out_mappings(graph, node_list)

    return tables_dict

def add_mvd_tables_for_node(node, tables_list):
    for attr in node.attributes:
        if attr.is_multivalued and attr.is_in_separate_table:
            tables_list.append(attr.mapped_table)

def get_table_list_unique_to_immediate_parent_node_with_all_by_itself(graph, config, node, tables_list):#immediate parent to node
    assert node is not None
    if config[node.unique_name] == "all_by_itself":
        tables_list.append(node.mapped_table)
        if node.is_mvds:
            add_mvd_tables_for_node(node, tables_list)
        return tables_list, node.unique_name
    elif config[node.unique_name] == "partially_by_itself":
        return get_table_list_unique_to_immediate_parent_node_with_all_by_itself(graph, config, node.parent_entity, tables_list)
    elif config[node.unique_name] == "contained_in_parent":
        return get_table_list_unique_to_immediate_parent_node_with_all_by_itself(graph, config, node.parent_entity, tables_list)


def calculate_insert_cost_for_tables(tables_dict):
    insert_cost_for_all_tables = 0

    for table in tables_dict:
        table_size = tables_dict.get(table)[0]
        insert_cost_for_all_tables += insert_cost(table_size)
    return insert_cost_for_all_tables


def calculate_select_cost_for_single_entity_or_relationship_helper(graph, node, config, tables_dict):
    cost = 0

    if node.is_entity() and config[node.unique_name]=="no_table":#only a parent entity(doesn't have to be root) in inheritance hierarchy can have no table option
        #for a node(has to be a parent) with no_table option - cost would be union of immediate parent with all by itself, and for each child of node, find immediate child with all
        #by itself if child is not all by itself and union - todo
        child_tables_cardinalities_for_union = []
        for child_node in node.children:
            child_tables_cardinalities_for_union.append(child_node.relation_size)
        cost += union_all_cost(child_tables_cardinalities_for_union) * node.select_frequency
    elif (node.is_entity() or node.is_relationship()) and config[node.unique_name]=="all_by_itself":#scan - these nodes may or may not have mvds
        tables_set_unique_to_node = set()
        if node.is_entity() and node.is_subclass:
            tables_set_unique_to_node.add(node.mapped_table)
            for attr in node.attributes:
                if attr.is_multivalued and attr.is_in_separate_table:
                    tables_set_unique_to_node.add(attr.mapped_table)
        else:
            tables_set_unique_to_node = node.node_tables#for strong entity, weak entity, relationship of all_by_itself, node tables contain only mapped table and mvd tables
        node_mapped_table_size = tables_dict.get(node.mapped_table[1])[0]
        node_mapped_table_distinct_keys = node_mapped_table_size
        if len(tables_set_unique_to_node) > 1:#mvds present and in separate table
            total_join_cost = 0
            mvd_tables = list(tables_set_unique_to_node - set(node.mapped_table))
            #each mvd table needs 1 scan to aggregate by pk, then each aggregated mvd by pk(same size as node_mapped table) gets joined with node_mapped_table - it is a pk-fk join
            for i in range(0, len(mvd_tables)):#if exists multiple mvds and all/some of them in separate tables
                table_size = tables_dict.get(mvd_tables[i][1])[0]
                total_join_cost += scan_cost(table_size)#aggregate cost for mvd
                total_join_cost += sort_merge_join_cost(node_mapped_table_size, node_mapped_table_size) if i == 0 else (
                    sort_merge_join_cost(node_mapped_table_size, node_mapped_table_size, left_sorted=True))#assume after first join left is sorted
            cost += total_join_cost * node.select_frequency
        else:#scan - if mvds present, they should be in array structure
            cost += scan_cost(node_mapped_table_size) * node.select_frequency
    elif node.is_relationship() and config[node.unique_name]=="folded_to_many_side":
        table_size = tables_dict.get(node.mapped_table[1])[0]#scan cost
        cost += scan_cost(table_size) * node.select_frequency
    elif node.is_entity() and node.is_weak_entity and config[node.unique_name]=="contained_in_parent":#todo - cost for nested scanning
        table_size = tables_dict.get(node.mapped_table[1])[0]
        cost += scan_cost(table_size) * node.select_frequency
    elif node.is_entity() and node.is_subclass and config[node.unique_name] != "all_by_itself":
        #for partially by itself - find immediate parent node in hierarchy which is all by itself and join all tables from that parent to node
        #best join order would be starting from smallest table - that would be the node itself - then work up all the way to immediate parent with all by itself
        if config[node.unique_name] == "partially_by_itself":
            tables_list_unique_to_immediate_parent_with_all_by_itself = []
            tables_list_unique_to_immediate_parent_with_all_by_itself, immediate_parent_unique_name = (
                get_table_list_unique_to_immediate_parent_node_with_all_by_itself(graph, config, node.parent_entity, tables_list_unique_to_immediate_parent_with_all_by_itself))
            immediate_parent_with_all_by_itself = graph.get_node_by_name(immediate_parent_unique_name)
            node.immediate_parent_with_all_by_itself_unique_name = immediate_parent_with_all_by_itself.unique_name
            table_set = set(tables_list_unique_to_immediate_parent_with_all_by_itself) | node.node_tables.difference(immediate_parent_with_all_by_itself.node_tables)
            table_list = list(table_set)
            table_list.sort(key=lambda x: x[0], reverse=True) #list is sorted to join from the lowest level table and gradually until the immediate_parent_with_all_by_itself - e.g. Grad_student -> Student -> Person
            assert graph.get_node_by_sort_key(table_list[0][0]).unique_name == node.unique_name
            left_table_size = tables_dict.get(node.mapped_table[1])[0]#at each intermediate and final step -> result size is same as left table size since we started with lowest level node - sorted in descending order
            left_distinct_keys = tables_dict.get(node.mapped_table[1])[1]
            assert left_table_size==left_distinct_keys
            total_join_cost = 0
            for i in range(1, len(table_list)):#e.g. student joining person_phone_no joining person
                node_table = graph.get_node_by_sort_key(table_list[i][0])
                if node_table.is_attribute() and node_table.is_multivalued:#for this table size != table distinct keys
                    assert node_table.is_in_separate_table
                    table_size = tables_dict.get(table_list[i][1])[0]
                    table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                    total_join_cost += scan_cost(table_size)
                    total_join_cost += sort_merge_join_cost(left_table_size, table_distinct_keys) if i == 1 else \
                        (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
                else:
                    table_size = tables_dict.get(table_list[i][1])[0]
                    table_distinct_keys = tables_dict.get(table_list[i][1])[1]
                    assert table_size==table_distinct_keys
                    total_join_cost += sort_merge_join_cost(left_table_size, table_distinct_keys) if i == 1 else \
                        (sort_merge_join_cost(left_table_size, table_distinct_keys, left_sorted=True))#assume after first join left is sorted
            cost += total_join_cost * node.select_frequency

        #for contained in parent - find parent if it is all by itself, then 2nd elif - if not, find immediate parent node in hierarchy which is all by itself and join all tables from that parent to node's immediate parent
        elif config[node.unique_name] == "contained_in_parent":
            if config[node.parent_entity.unique_name] == "all_by_itself":
                cost += calculate_select_cost_for_single_entity_or_relationship_helper(graph, node.parent_entity, config, tables_dict)
            elif config[node.parent_entity.unique_name] == "partially_by_itself":
                cost += calculate_select_cost_for_single_entity_or_relationship_helper(graph, node.parent_entity, config, tables_dict)
            else:
                cost += calculate_select_cost_for_single_entity_or_relationship_helper(graph, node.parent_entity, config, tables_dict)

    return cost


def calculate_insert_select_cost_for_single_entity_or_relationship(graph, node_list, config, tables_dict):#select, insert - workload queries have single entity or relationship
    cost = 0

    #insert cost
    cost += calculate_insert_cost_for_tables(tables_dict)

    #select cost
    for node in node_list:
        if node.is_entity() or node.is_relationship():
            cost += calculate_select_cost_for_single_entity_or_relationship_helper(graph, node, config, tables_dict)#config is not complete- cost for partial config

    return cost




