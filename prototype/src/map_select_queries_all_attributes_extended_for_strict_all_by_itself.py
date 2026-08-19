import logging

from er_graph import Node, Graph

#For this select * query is defined as -
#strong entity - all its attributes
#strong subclass entity - all attributes inherited from parent/s and its own attributes
#weak entity - pk from parent + own discriminator(if exists) + own attrobutes + all attributes from parent
#relationship - pks from 2 entities and its own attributes + all attributes from 2 entities

memoized_select_all_queries = {}

#full table view built for nodes in hierarchy with node_cover - from this temp tables list, can directly output all node tuples with full attribute list for full representation of node
with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover = {}
#with clauses for mvd tables for nodes with no node cover - required for defining no_table nodes - to avoid duplicating mvd tables from multiple entities in node cover for no_table node
with_clause_mvd_cte_temp_tables_for_nodes_with_no_node_cover = {}

#these two covers are required for renaming tables for relationships - uniquely identify from which participating entity tables/nodes are contributed
#e.g. WITH product_mv_attributes AS (SELECT r2.product_id, ARRAY_AGG(r2.mv_attributes) FILTER (WHERE r2.mv_attributes IS NOT NULL) AS mv_attributes FROM relation_2 AS r2
# GROUP BY r2.product_id) SELECT r96.product_id, r96.bundle_product_product_id, COALESCE(pma_main.mv_attributes,   ARRAY[]::text[]) AS product_mv_attributes, COALESCE(pma_bundle.mv_attributes, ARRAY[]::text[]) AS bundle_product_mv_attributes
# FROM relation_96 AS r96 JOIN relation_1 AS r1_main ON r1_main.product_id = r96.product_id JOIN relation_1 AS r1_bundle ON r1_bundle.product_id = r96.bundle_product_product_id
#LEFT JOIN product_mv_attributes AS pma_main ON pma_main.product_id = r1_main.product_id LEFT JOIN product_mv_attributes AS pma_bundle ON pma_bundle.product_id = r1_bundle.product_id;
attribute_node_cover = {}#Full attribute node cover to answer select * query for each node(entity/relationship)
table_cover = {}#Full table cover to answer select * query for each node(entity/relationship)

def init_memoized_attributes_and_select_all_queries():
    memoized_select_all_queries.clear()
    attribute_node_cover.clear()
    table_cover.clear()
    with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover.clear()
    with_clause_mvd_cte_temp_tables_for_nodes_with_no_node_cover.clear()

def get_attribute_cover():
    return attribute_node_cover

def get_table_cover():
    return table_cover

#all separate mvd tables - either coming from top parents or itself
def add_mvd_tables_for_node(node, tables_set:set):
    for attribute in node.attribute_list:
        if attribute.get("is_multivalued", False) and attribute.get("is_in_separate_table", False):#attribute_list parameters correctly set to selected config. At this step
            tables_set.add(attribute.get("mapped_table"))                 #it is correct to check from attribute_list since attribute_list for nodes are already initialized

#for contained_all_descendants or all by itself nodes - return mapped_table and all relevant mvd tables
def get_table_set_unique_to_node(graph, node, tables_set:set):#for inheritance hierarchies
    assert node is not None
    assert node.is_contained_all_descendants == True or node.is_all_by_itself == True
    if node.is_contained_all_descendants or node.is_all_by_itself:
        tables_set.add(node.mapped_table)
        add_mvd_tables_for_node(node, tables_set)
        return tables_set

#only returns mapped table and mvd tables for all by itself node
def get_table_set_unique_to_node_with_all_by_itself(node, tables_set:set):#for inheritance hierarchies
    assert node is not None
    assert node.is_all_by_itself == True
    if node.is_all_by_itself:
        tables_set.add(node.mapped_table)
        add_mvd_tables_for_node(node, tables_set)
        return tables_set

#for a node - returns the immediate parent of contained_all_descendants or all_by_itself
def get_immediate_parent_node_with_all_by_itself(graph, node):#immediate parent to node
    assert node is not None
    if node.is_contained_all_descendants or node.is_all_by_itself:
        return node
    elif node.is_partially_by_itself:
        assert node.parent_entity is not None
        return get_immediate_parent_node_with_all_by_itself(graph, node.parent_entity)
    elif node.is_contained_in_parent:
        return get_immediate_parent_node_with_all_by_itself(graph, node.parent_entity)

def check_if_relationship_is_1_N(node):
    if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:
        return True
    elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:
        return True
    else:
        return False

#find the minimum cover to represent the no_table node - minimum cover consists of immediate contained_all_descendants/all_by_itself children - these children may not be at the same level in hierarchy because
#some immediate children may be no table as well, then have to traverse down until child node cover is found to cover that branch
#for no table node - immediate children can be only contained_all_descendants, all by itself or no table
def find_all_by_itself_children_for_no_table_node(node, children_list):
    for child in node.children:
        if child.is_contained_all_descendants:
            children_list.append(child.unique_name)
        elif child.is_all_by_itself:#simply add the child for all by itself - later handle for non-leaf(view required for full tuple coverage) vs leaf(view not required)
            children_list.append(child.unique_name)
        else:# then it has to be a no_table as well - can't be partially by itself or contained in parent
            #if child is a no_table, add the children list(all_by_itself) representing that child
            assert child.is_no_table  #no table
            assert child.mapped_table is None
            find_all_by_itself_children_for_no_table_node(child, children_list)

def find_all_children_rooted_at_node(node, all_entities):#immediate and not - all children
    for child in node.children:
        if len(child.children) > 0:
            find_all_children_rooted_at_node(child, all_entities)
        all_entities.add(child.unique_name)

#required for mvd tables coming from subclass or root strong entity - pks/joining reference table can change for mvd tables
def get_lowest_level_subclass_or_root_in_select_all_nodes_for_entity(graph, entity_node):
    select_all_nodes_list = []
    for node_name in entity_node.select_all_nodes:
        select_all_node = graph.get_node_by_name(node_name)
        select_all_nodes_list.append(select_all_node)
    select_all_nodes_list.sort(key=lambda node: node.sort_key, reverse=True)#highest sort key to lowest
    for select_all_node in select_all_nodes_list:
        if select_all_node.is_subclass or len(select_all_node.children)>0:#there should be only one subclass(if no subclasses could be a root as well) since only a single strong entity is added in select_all_nodes for a node
            return select_all_node.unique_name
    return None

def get_dependent_entities_for_weak_entity(graph, weak_entity, depending_entities):
    depending_entities.append(weak_entity.parent_entity.unique_name)
    if weak_entity.parent_entity.is_weak_entity:#if parent is also a weak entity, need to iterate until a strong depending entity found
        get_dependent_entities_for_weak_entity(graph, weak_entity.parent_entity, depending_entities)

def reset_select_all_nodes_and_select_all_tables(graph):
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            node.select_all_nodes = []
            node.select_all_tables = set()
            node.select_all_attributes_count = None

def set_select_all_query_column_count_for_entity_or_relationship(graph):
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            if node.is_entity() and not node.is_weak_entity:
                node.select_all_attributes_count = len(node.attribute_list)
            elif node.is_entity() and node.is_weak_entity:
                select_all_attributes_count = 0
                for attribute_cover_node_name in node.select_all_nodes:
                    attribute_cover_node = graph.get_node_by_name(attribute_cover_node_name)
                    if attribute_cover_node.unique_name == node.unique_name:
                        select_all_attributes_count += len(attribute_cover_node.attribute_list)
                    else:
                        for attribute in attribute_cover_node.attribute_list:
                            if "pk_name" not in attribute and "name" in attribute:#filter for non-pk attributes
                                select_all_attributes_count += 1
                node.select_all_attributes_count = select_all_attributes_count
            else:
                assert node.is_relationship()
                assert node.entity1.select_all_attributes_count > 0#participating entiites could be strong/weak entities
                assert node.entity2.select_all_attributes_count > 0
                select_all_attributes_count = 0
                select_all_attributes_count += len(node.attribute_list)
                select_all_attributes_count += node.entity1.select_all_attributes_count
                select_all_attributes_count += node.entity2.select_all_attributes_count
                for attribute in node.entity1.attribute_list:#deduct pk s from entity1 since they are already coming from relationship itself
                    if "pk_name" in attribute and not "name" in attribute:
                        select_all_attributes_count -= 1
                for attribute in node.entity2.attribute_list:#deduct pk s from entity2 since they are already coming from relationship itself
                    if "pk_name" in attribute and not "name" in attribute:
                        select_all_attributes_count -= 1
                node.select_all_attributes_count = select_all_attributes_count



#select_all_nodes - all entity/relationship nodes required to get attribute set to answer select * query
#attribute set of select * query for,
#strong entity -> pks and its own attributes
#weak entity -> pks (including discriminator if exists), its own attributes, all attributes from depending parent/s
#relationship -> pks, its own attributes, all attributes from participating entities
def initialize_select_nodes_for_single_entity_or_relationship_helper(graph, entity_or_relationship_node):
    if entity_or_relationship_node.mapped_table:#strong entities - can be regular entity/subclass - its own pk - attribute list in node fully define the node itself
        if entity_or_relationship_node.is_entity() and not entity_or_relationship_node.is_weak_entity:
            return [entity_or_relationship_node.unique_name]
        elif entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity:#attribute list in node doesn't define the node fully - need to get all
            depending_entities = []                                                                 #parent nodes for full attribute list
            depending_entities.append(entity_or_relationship_node.unique_name)#first add node itself - this order matters for attribute order in sql query
            get_dependent_entities_for_weak_entity(graph, entity_or_relationship_node, depending_entities)
            return depending_entities
        elif entity_or_relationship_node.is_relationship():#attribute list in node doesn't define the node fully - need to get all participating nodes for full attribute list
            depending_entities = []
            depending_entities.append(entity_or_relationship_node.unique_name)#first add node itself - this order matters for attribute order in sql query
            depending_entities.extend(entity_or_relationship_node.entity1.select_all_nodes)
            depending_entities.extend(entity_or_relationship_node.entity2.select_all_nodes)

            attribute_node_cover[entity_or_relationship_node.unique_name] = {entity_or_relationship_node.entity1.unique_name : list(entity_or_relationship_node.entity1.select_all_nodes),
                                                                             entity_or_relationship_node.entity2.unique_name : list(entity_or_relationship_node.entity2.select_all_nodes),
                                                                             entity_or_relationship_node.unique_name : [entity_or_relationship_node.unique_name]}
            return depending_entities
    else:#no table - no_table option is possible for an entity which belong to an inheritance hierarchy(also has to be non-leaf) only
        assert len(entity_or_relationship_node.children) > 1#has to belong to an inheritance hierarchy
        depending_entities = []
        find_all_by_itself_children_for_no_table_node(entity_or_relationship_node, depending_entities)
        return depending_entities


#initialize physical tables required to answer a select * entity/relationship
#strong entity - all its attributes
#strong subclass entity - all attributes inherited from parent/s and its own attributes
#weak entity - pk from parent + own discriminator(if exists) + own attrobutes + all attributes from parent
#relationship - pks from 2 entities and its own attributes + all attributes from 2 entities
#E.g. if phone_smartphone exists between phone and smartphone - phone_smartphone.select_all_tables is {table_product, table_product_mvd_attribute,
# table_physicalproduct, table_phone, table_smartphone, table_phone_smartphone}.
#Lossless full table cover is - {phone: {table_product, table_product_mvd_attribute, table_physicalproduct, table_phone}, smartphone: {table_product, table_product_mvd_attribute, table_physicalproduct,
# table_smartphone}, phone_smartphone: {table_phone_smartphone}}
#For a node(could be a subclass/root) - select_all_tables set to mapped table(main table coming from node itself)
#and all mvd tables(could be coming from parents or itself).
#if len(node_cover)==1 which means cover is only itself, mapped_table of node contains all relevant tuples
#Mapped_table doesn't include all tuples from the node if len(node_cover)>1 since node is distributed across its node_cover including node itself.
#However the coverage is achieved by node_cover defined for node when building the select * query.
def initialize_select_tables_for_single_entity_or_relationship_helper(graph, entity_or_relationship_node):
    if entity_or_relationship_node.mapped_table:#set table cover for non- no_table nodes
        if (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_all_by_itself and
                not entity_or_relationship_node.is_subclass and not entity_or_relationship_node.is_weak_entity and len(entity_or_relationship_node.children)==0):#excluding hierarchical nodes including root
            return entity_or_relationship_node.node_tables.copy()#for strong entity(non-hierarchical), node_tables contain only its mapped_table and own mvd_tables - node tables is sufficient to cover the node fully
        elif (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_contained_all_descendants and not entity_or_relationship_node.is_subclass):
            return entity_or_relationship_node.node_tables.copy()#for contained_all_descendants root, its node_tables contain only its mapped_table and own mvd_tables
        elif (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_all_by_itself and
              not entity_or_relationship_node.is_subclass and not entity_or_relationship_node.is_weak_entity):#root with all by itself
            #for all by itself - select all tables set to only its mapped table and mvd tables(coming from parents or itself)
            #this may not fully define node if node is distributed in node_cover, but node full cover is achieved by node_cover defined for node when building the query
            tables_set_to_unique_to_node = set()
            return get_table_set_unique_to_node_with_all_by_itself(entity_or_relationship_node, tables_set_to_unique_to_node)
        elif entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_subclass:
            if entity_or_relationship_node.is_contained_in_parent:#parent may be contained_all_descendants or all by itself or partially by itself or contained in its parent
                #this may not fully define node(all relevant tuples distributed across multiple tables) if len(node_cover)>1 since node is distributed in node_cover,
                #but node full cover is achieved by node_cover defined for node when building the query
                tables_set = set()
                add_mvd_tables_for_node(entity_or_relationship_node, tables_set)#if relevant(own or coming from parent) mvds are still in separate tables
                tables_set |= initialize_select_tables_for_single_entity_or_relationship_helper(graph, entity_or_relationship_node.parent_entity)
                return tables_set
            elif entity_or_relationship_node.is_partially_by_itself:
                #for partially by itself node, a parent with contained_all_descendants/all_by_itself should exist
                #this may not fully define node(all relevant tuples distributed across multiple tables) if len(node_cover)>1 since node is distributed in node_cover(child nodes and itself),
                #but node full cover is achieved by node_cover defined for node when building the query
                assert entity_or_relationship_node.immediate_parent_with_all_by_itself_unique_name is not None
                immediate_parent_with_all_by_itself = graph.get_node_by_name(entity_or_relationship_node.immediate_parent_with_all_by_itself_unique_name)
                tables_list_unique_to_immediate_parent_with_all_by_itself = set()
                tables_list_unique_to_immediate_parent_with_all_by_itself= get_table_set_unique_to_node(graph, immediate_parent_with_all_by_itself,
                                                                                                        tables_list_unique_to_immediate_parent_with_all_by_itself)
                table_set = (set(tables_list_unique_to_immediate_parent_with_all_by_itself) |
                             entity_or_relationship_node.node_tables.difference(immediate_parent_with_all_by_itself.node_tables))
                return table_set
            elif entity_or_relationship_node.is_all_by_itself:
                #for all by itself - select all tables set to only its mapped table and relevant mvd tables(coming from parents or itself)
                #this may not fully define node if it is non-leaf and if node is distributed in node_cover,
                #for leaf all_by_itself node, it is guarenteed that len(node_cover)==1 and node itself fully covers all tuples
                #node full cover is achieved by node_cover defined for node when building the query
                tables_set_to_unique_to_node = set()
                return get_table_set_unique_to_node_with_all_by_itself(entity_or_relationship_node, tables_set_to_unique_to_node)
            elif entity_or_relationship_node.is_contained_all_descendants:
                #mapped_table fully define node - which means all relevant tuples included in the mapped_table
                tables_set_unique_to_node = set()
                return get_table_set_unique_to_node(graph, entity_or_relationship_node, tables_set_unique_to_node)
        elif entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity:#added for weak entity since according to assumption, select * from weak entity
            depending_entities = []                                                         #should get all parent attributes + weak entity attributes (not just pks + weak entity)
            table_set = set()                                                               #this definition is an assumption
            get_dependent_entities_for_weak_entity(graph, entity_or_relationship_node, depending_entities)
            for parent_entity in depending_entities:
                parent_node = graph.get_node_by_name(parent_entity)
                assert len(table_cover[parent_node.unique_name][parent_node.unique_name]) > 0
                #an all by itself node is incomplete in its own mapped_table only if it has contained_all_descendants/all children in the subtree under the node(which means
                #its node cover is greater than one).
                #an all by itself node is complete(means all relevant tuples included in the mapped_table itself) if it is a leaf in the hierarchy - where no children
                if len(parent_node.node_cover)>1:#if weak entity has a depending parent which is distributed in node_cover - parent's full table view is added
                    #this is added as a representation for full table generated for parent_node by doing union across its node_cover - all required coverage is in the full union table itself
                    parent_entity_full_table_view_name = "temp_" + parent_node.unique_name
                    parent_entity_table_cover = [(parent_node.sort_key, parent_entity_full_table_view_name)]
                else:
                    parent_entity_table_cover = table_cover[parent_node.unique_name][parent_node.unique_name]
                table_set |= set(parent_entity_table_cover)#table cover for all parent_nodes need to be initialized before weak entity
            if entity_or_relationship_node.is_all_by_itself:
                table_set |= entity_or_relationship_node.node_tables#for weak entity with all by itself - node_tables contain only mapped table and mvd tables if mvds in separate tables
            #folded weak entity cannot have its own mvd attributes in separate tables
            #if weak entity has a depending non-leaf parent of all by itself with node cover greater than 1 - its full table view is added
            #if the weak entity is folded in a non-leaf parent which is all by itself, weak entity will be distributed in many tables (across the node cover of parent)
            #to generate select * for weak_entity, first full parent table is generated with a with clause doing union across node_cover, then weak entity is unfolded on that built table
            return table_set
        elif entity_or_relationship_node.is_relationship():
            table_set = set()
            #if relationship has a participating entity which is distributed in node_cover - only participating entity's full table view is added
            #this is added as a representation for full table generated for participating entity by doing union across its node_cover - all required coverage is in the full union table itself
            if len(entity_or_relationship_node.entity1.node_cover)>1:
                #a view is needed only when mapped_table doesn't cover - for that it has to be a node with node cover greater than 1 - node can be all/partial/contained in parent
                entity1_full_table_view_name = "temp_" + entity_or_relationship_node.entity1.unique_name
                entity1_table_cover = [(entity_or_relationship_node.entity1.sort_key, entity1_full_table_view_name)]
            else:
                entity1_table_cover = table_cover[entity_or_relationship_node.entity1.unique_name][entity_or_relationship_node.entity1.unique_name]

            if len(entity_or_relationship_node.entity2.node_cover)>1:
                entity2_full_table_view_name = "temp_" + entity_or_relationship_node.entity2.unique_name
                entity2_table_cover = [(entity_or_relationship_node.entity2.sort_key, entity2_full_table_view_name)]
            else:
                entity2_table_cover = table_cover[entity_or_relationship_node.entity2.unique_name][entity_or_relationship_node.entity2.unique_name]

            if graph.config[entity_or_relationship_node.unique_name] == "folded_to_many_side":#1:N relationship
                many_side = entity_or_relationship_node.entity1 if not entity_or_relationship_node.rel_dict['entity1']['one'] and entity_or_relationship_node.rel_dict['entity2']['one'] \
                                    else entity_or_relationship_node.entity2
                if len(many_side.node_cover)>1:#a node is incomplete in its own mapped_table
                    relationship_node_mvd_tables_set = set()
                    add_mvd_tables_for_node(entity_or_relationship_node, relationship_node_mvd_tables_set)
                    many_side_full_table_view_name = "temp_" + many_side.unique_name
                    relationship_node_table_cover = {(many_side.sort_key, many_side_full_table_view_name)}#mapped table is the complete table view of the many side
                    relationship_node_table_cover |= relationship_node_mvd_tables_set
                else:
                    relationship_node_table_cover = entity_or_relationship_node.node_tables.copy()#for relationship - node_tables contain only mapped table and mvd tables if mvds in separate tables
            else:
                relationship_node_table_cover = entity_or_relationship_node.node_tables.copy()#for relationship - node_tables contain only mapped table and mvd tables if mvds in separate tables

            table_set |= set(entity1_table_cover)
            table_set |= set(entity2_table_cover)
            table_set |= relationship_node_table_cover
            table_cover[entity_or_relationship_node.unique_name] = {entity_or_relationship_node.entity1.unique_name : entity1_table_cover,
                                                                    entity_or_relationship_node.entity2.unique_name : entity2_table_cover,
                                                                    entity_or_relationship_node.unique_name : list(relationship_node_table_cover)}
            return table_set
    else:#no table - return empty set
        return set()

#select_all_tables - all unique physical tables/non-physical table views required to answer select * query - set - remove duplicates - e.g. for a recursive relationship, all tables from an entity only added once
#select_all_nodes - all entity/relationship nodes required to get attribute set to answer select * query - select_all_nodes can have duplicates(e.g. for recursive relationshp, both participating
# entities are the same) - for query generation(e.g. select * from recursive_relationship), node cover is iterated(e.g. for recursive relationship, same entity is iterated twice)
# hence select_all_nodes is defined as a list not a set
def initialize_select_tables_for_single_entity_or_relationship(graph):
    reset_select_all_nodes_and_select_all_tables(graph)

    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            if node.is_entity():
                node.select_all_tables = initialize_select_tables_for_single_entity_or_relationship_helper(graph, node)#defined for all nodes except nodes which are no_table
                table_cover[node.unique_name] = {node.unique_name:list(node.select_all_tables)}
                node.select_all_nodes = initialize_select_nodes_for_single_entity_or_relationship_helper(graph, node)#defined for all nodes except nodes which are no_table
                attribute_node_cover[node.unique_name] = {node.unique_name:list(node.select_all_nodes)}
            elif node.is_relationship():
                node.select_all_tables = initialize_select_tables_for_single_entity_or_relationship_helper(graph, node)
                node.select_all_nodes = initialize_select_nodes_for_single_entity_or_relationship_helper(graph, node)

    set_select_all_query_column_count_for_entity_or_relationship(graph)

#table views are generated for entities with len(entity.node_cover)>1 in graph
#nodes in hierarchy with all/contained in parent/partially may have itself distributed in node_cover - including root with all option
def get_mapped_table_for_entity_or_relationship(graph, entity_or_relationship_node):
    #a contained_all_descendants node is complete.
    #an all by itself node is complete if it is a leaf in the hierarchy - where no children
    #for all other types including non-leaf all by itself - can induce a view
    if entity_or_relationship_node.is_entity() and len(entity_or_relationship_node.node_cover)>1:#induce a view
        entity_full_table_view_name = "temp_" + entity_or_relationship_node.unique_name
        return (entity_or_relationship_node.sort_key, entity_full_table_view_name)
    elif (entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and
          len(entity_or_relationship_node.parent_entity.node_cover)>1 and entity_or_relationship_node.is_contained_in_parent):
        #folded weak entity depending on a node distributed across node_cover
        entity_full_table_view_name = "temp_" + entity_or_relationship_node.parent_entity.unique_name
        return (entity_or_relationship_node.parent_entity.sort_key, entity_full_table_view_name)#mapped_table for folded weak entity is the view of parent
    elif (entity_or_relationship_node.is_relationship() and check_if_relationship_is_1_N(entity_or_relationship_node) and
          graph.config[entity_or_relationship_node.unique_name] == "folded_to_many_side"):
        many_side_entity = entity_or_relationship_node.entity2 if entity_or_relationship_node.rel_dict['entity1']['one'] and not entity_or_relationship_node.rel_dict['entity2']['one'] \
            else entity_or_relationship_node.entity1
        if len(many_side_entity.node_cover)>1:#folded relationship having a participating many side node distributed in node_cover
            relationship_full_table_view_name = "temp_" + many_side_entity.unique_name
            return (many_side_entity.sort_key, relationship_full_table_view_name)#mapped table for folded relationship is the view of many side
        else:
            return entity_or_relationship_node.mapped_table
    else:
        return entity_or_relationship_node.mapped_table

#e.g. WITH ph AS ( SELECT person_id, ARRAY_AGG(DISTINCT tel_no ORDER BY tel_no) AS tel_nos FROM telephone WHERE tel_no IS NOT NULL GROUP BY person_id)
def generate_with_clause_for_mvd_table(mvd_node, tables, types, graph, mvd_select_clause, mvd_from_clause, mvd_where_clause, mvd_group_by_clause):
    relevant_tables = [table for table in tables if table[0]==mvd_node.mapped_table[1]]
    assert len(relevant_tables)==1
    relevant_tables_keys_names_sorted = mvd_node.mapped_table
    relevant_table_attribute_lists = {}
    table_tuple = mvd_node.mapped_table
    table = relevant_tables[0][1]
    relevant_table_attribute_lists[table_tuple] = [attribute_info[0] for attribute_info in table]

    for i in range(len(mvd_node.key.table_key[0])):#except mvd
        pk_attr_name = mvd_node.key.table_key[0][i][0]
        mvd_select_clause.append(f"{mvd_node.mapped_table[1]}.{pk_attr_name} AS {pk_attr_name}")

    mvd_attr_name = mvd_node.key.table_key[1][0][0]#mvd
    mvd_select_clause.append(f"ARRAY_AGG({mvd_node.mapped_table[1]}.{mvd_attr_name}) AS {mvd_attr_name}")
    mvd_where_clause.append(f"{mvd_attr_name} IS NOT NULL")
    mvd_from_clause.append(mvd_node.mapped_table[1])

    mvd_select_clause_str = ", ".join(mvd_select_clause)
    if "AGG" in mvd_select_clause_str:#the group by clause is modified to include all attributes(except AGG attributes) to do the group by - each tuple grouped by all attributes
        mvd_group_by_clause.extend([c.split()[0] for c in mvd_select_clause if "AGG" not in c])#group by all attributes except attributes with 'AGG' in tuple

#required for folded weak entity/relationship
#for folded weak entity/relationship generate the full view for entity distributed in node cover
#view contains all relevant attributes of entity and folded weak entity/relationship column
def generate_temp_view_with_clause_for_entity_with_node_cover(entity_node, folded_weak_entity_or_relationship_node, tables, types, graph):
    node_cover = entity_node.node_cover
    assert len(node_cover)>1
    assert node_cover[0] == entity_node.unique_name #this matters since for union query attribute names are adhered to attribute names from entity itself(pk names can be different across node cover)
    #e.g.if entity is person and person contain person, student in node cover -  person_id in person, student_id in student - for attribute name structure, names in person are followed
    #hence node_cover is defined as a list instead of set(set doesn't maintain order)
    assert entity_node.mapped_table

    entity_node_attributes = []
    for attribute in entity_node.attribute_list:#to get own attributes for final select clause
        if "pk_name" in attribute:
            entity_node_attributes.append(attribute["pk_name"])
        elif "name" in attribute and attribute["name"] != "role":
            entity_node_attributes.append(attribute["name"])

    entity_node_mapped_table_all_attributes = entity_node_attributes.copy()#to get own attributes plus any folded weak entity/relationship attributes for temp table full view
    """
    for table in tables:
        if table[0] == entity_node.mapped_table[1]:
            for table_attributes in table[1]:
                table_attribute_entity_unique_name = table_attributes[3]#entity from which attribute comes in
                table_attribute_node = graph.get_node_by_name(table_attribute_entity_unique_name)
                if (table_attribute_node.is_entity() and table_attribute_node.is_weak_entity and table_attribute_node.is_contained_in_parent and
                        table_attribute_node.parent_entity.unique_name == entity_node.unique_name and table_attributes[0] not in entity_node_mapped_table_all_attributes):
                    #folded weak entity only relevant to entity_node itself
                    entity_node_mapped_table_all_attributes.append(table_attributes[0])
                elif table_attribute_node.is_relationship() and table_attributes[0] not in entity_node_mapped_table_all_attributes:
                    assert check_if_relationship_is_1_N(table_attribute_node)#folded 1:N relationship
                    many_side_entity = table_attribute_node.entity2 if table_attribute_node.rel_dict['entity1']['one'] and not table_attribute_node.rel_dict['entity2']['one'] \
                        else table_attribute_node.entity1
                    if many_side_entity.unique_name == entity_node.unique_name:#folded relationship only relevant to entity_node itself
                        #if entity_node is contained_in_parent, mapped_table would have folded relationships relevant to other entities
                        #need to filter folded relationship only relevant to entity_node itself
                        entity_node_mapped_table_all_attributes.append(table_attributes[0])
            break
    """
    for table in tables:
        if table[0] == entity_node.mapped_table[1]:
            for table_attributes in table[1]:
                table_attribute_entity_unique_name = table_attributes[3]#entity from which attribute comes in
                if table_attribute_entity_unique_name == folded_weak_entity_or_relationship_node.unique_name:
                    entity_node_mapped_table_all_attributes.append(table_attributes[0])
                    break #found the required attribute representing folded weak entity or relationship, hence stop


    temp_view_name = entity_node.unique_name + "_" + folded_weak_entity_or_relationship_node.unique_name

    with_clause = []#mvd tables, temp table to aggregate all tuples across node cover for full representation of node added as with clauses
    union_clause = []


    mvd_cte_built_tables = []#mvd_tables_to_which_with_clauses_generated

    for node_name in node_cover:
        node_cover_node = graph.get_node_by_name(node_name)

        relevant_tables = [table for table in tables if table[0] in [select_table for sort_key, select_table in node_cover_node.select_all_tables]]
        relevant_tables_keys_names_sorted = sorted(list(node_cover_node.select_all_tables), key=lambda x: x[0])
        relevant_table_attribute_lists = {}
        for table in relevant_tables:
            table_tuple = next((t for t in relevant_tables_keys_names_sorted if t[1] == table[0]), None)
            relevant_table_attribute_lists[table_tuple] = [attribute_info[0] for attribute_info in table[1]]

        assert node_cover_node.mapped_table

        select_clause = []
        select_clause_without_folded_weak_entities_or_relationship_attributes = []
        from_clause = []
        join_clause = []
        left_join_clause = []
        where_clause = []

        node_cover_node_mapped_table = node_cover_node.mapped_table#consider original mapped_table
        from_clause.append(node_cover_node_mapped_table[1])
        tables_sorted_reverse = sorted(relevant_tables_keys_names_sorted, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table

        if len(tables_sorted_reverse)>1:#if joins needed - add pk, fk join clauses
            for joining_table in tables_sorted_reverse:
                node = graph.get_node_by_sort_key(joining_table[0])
                if not node.is_attribute():#all nodes belong to hierarchy - all nodes are strong entites

                    node_mapped_table = node.mapped_table

                    assert node_mapped_table in relevant_tables_keys_names_sorted

                    if node.key.reference_table is not None:
                        if node.key.table_key and isinstance(node.key.table_key[0], tuple):#strong entity, strong subclass entity
                            node_join_clause = []
                            assert len(node.key.table_key) == 1
                            for i in range(len(node.key.table_key)):
                                if node.key.reference_table[i] in [t[1] for t in relevant_tables_keys_names_sorted]:
                                    if (node_mapped_table[1] != node.key.reference_table[i]) and (node.mapped_table[1] != node.key.reference_table[i]):
                                        node_join_clause.append(f"{node_mapped_table[1]}.{node.key.table_key[i][0]} {"="} {node.key.reference_table[i]}.{node.key.reference_key[i][0]}")
                            node_join_clause_str = " AND ".join(node_join_clause)
                            assert len(node.key.reference_table) == 1
                            if node_join_clause_str:
                                join_clause.append(f"JOIN {node.key.reference_table[0]} AS {node.key.reference_table[0]} ON " + node_join_clause_str)

                else:#mvd in separate table
                    #a child in node_cover may have an own mvds in separate table which are not relevant attributes for parent - need to filter for those
                    #execute only if mvd in separate table coming from table_cover is relevant for entity_node
                    if node.name in entity_node_attributes:
                        assert node.is_multivalued
                        assert node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple)
                        with_table_name = node.entity.unique_name + "_" + node.name
                        if node.entity.unique_name == node_cover_node.unique_name:#mvd in separate table coming from node itself
                            left_join_clause.append(f"LEFT JOIN {with_table_name} ON {with_table_name}.{node.key.table_key[0][0][0]} {"="} {node.key.reference_table[0]}.{node.key.reference_key[0][0][0]}")
                        else:#mvd in separate table coming from a differnt node - not node itself
                            #all nodes in node_cover are nodes in hierarchy - hence any mvd table coming from a node in node_cover
                            #comes from a subclass/root in hierarchy. Hence pk/reference table may change
                            #mvd coming from subclass or root strong entity - pks/joining reference table can change for mvd tables
                            assert node.entity.is_subclass or len(node.entity.children)>0
                            #since mvd's entity belongs to a hierarchy - # of pks of the entity should be 1 - subclass/root is a strong entity
                            lowest_level_subclass_or_root_name = get_lowest_level_subclass_or_root_in_select_all_nodes_for_entity(graph, node_cover_node)
                            assert lowest_level_subclass_or_root_name
                            lowest_level_subclass = graph.get_node_by_name(lowest_level_subclass_or_root_name)
                            entity_table_to_join_with_mvd_table = lowest_level_subclass.mapped_table[1]
                            pk_of_entity_table_to_join_with_mvd_table = lowest_level_subclass.key.table_key[0][0]
                            left_join_clause.append(f"LEFT JOIN {with_table_name} ON {with_table_name}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{entity_table_to_join_with_mvd_table}.{pk_of_entity_table_to_join_with_mvd_table}")

        if node_cover_node.is_entity() and node_cover_node.is_subclass and node_cover_node.is_contained_in_parent:#only if contained_in_parent
            if len(node_cover_node.children)>0:#entity_or_relationship_node can be any sub parent which is contained in parent
                assert "role" in relevant_table_attribute_lists[node_cover_node_mapped_table]
                # collect entity names (entity + contained children)
                all_entities = {node_cover_node.unique_name}#add entity itself
                #add all children rooted at node
                find_all_children_rooted_at_node(node_cover_node, all_entities)
                all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                where_clause.append(f"{node_cover_node_mapped_table[1]}.{"role"} {"IN"} ({all_entities_str})")
            else:#entity itself - where clause would be just role in (entity_name)
                #for leaf subclass contained in parent
                assert "role" in relevant_table_attribute_lists[node_cover_node_mapped_table]
                where_clause.append(f"{node_cover_node_mapped_table[1]}.{"role"} {"IN"} ('{node_cover_node.unique_name}')")


        #node_cover for a node contains the node itself, and other child nodes which are contained_all_descendants/all_by_itself to fully cover all tuples for node
        if node_cover_node.unique_name != entity_node.unique_name:#not entity_node itself - some other child in the node_cover
            for attribute in node_cover_node.attribute_list:
                attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                #filter only required attributes from child node in node cover - child has parents' attributes + its own
                #pk, attributes coming from entity node and entity node's parents
                if ("pk_name" in attribute) or (attr_name in entity_node_attributes):
                    if not (attribute.get("is_multivalued", False) and attribute.get("is_in_separate_table", False)):#for any attribute which not a mvd in separate table - found table is node mapped table for all by itself or contained_all_descendants node
                        found = node_cover_node.mapped_table
                        found_table_name = found[1] if found else None
                    else:#mvd in separate table
                        assert attribute["is_multivalued"] and attribute["is_in_separate_table"]
                        found = [t for t in relevant_table_attribute_lists if attr_name in relevant_table_attribute_lists[t]]
                        found_table_name = found[0][1] if found else None
                        assert found[0][1] == attribute["mvd_separate_table_name"][1]

                    if attribute.get("is_multivalued", False):
                        if attribute.get("is_in_separate_table", False):
                            attribute_node = graph.get_node_by_name(attribute.get("unique_name", None))
                            assert attribute_node
                            with_table_name = attribute_node.entity.unique_name + "_" + attribute_node.name
                            if with_table_name not in mvd_cte_built_tables:
                                mvd_with_clause_str = ""
                                mvd_select_clause = []
                                mvd_from_clause = []
                                mvd_where_clause = []
                                mvd_group_by_clause = []
                                generate_with_clause_for_mvd_table(attribute_node, tables, types, graph, mvd_select_clause, mvd_from_clause, mvd_where_clause, mvd_group_by_clause)
                                mvd_select_clause_str = ", ".join(mvd_select_clause)
                                mvd_from_clause_str = ", ".join(mvd_from_clause)
                                mvd_where_clause_str = " AND ".join(mvd_where_clause)
                                mvd_group_by_clause_str = ", ".join(mvd_group_by_clause)
                                mvd_with_clause_str += (f"{with_table_name} AS (SELECT {mvd_select_clause_str} FROM {mvd_from_clause_str} WHERE {mvd_where_clause_str} "
                                                        f"GROUP BY {mvd_group_by_clause_str})")
                                with_clause.append(mvd_with_clause_str)
                                mvd_cte_built_tables.append(with_table_name)
                                if temp_view_name not in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover:
                                    with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[temp_view_name] = [{attribute_node.unique_name : mvd_with_clause_str}]
                                    #order of entering clauses matters - hence for each node - it is a list of dictionaries - e.g. mvd tables has to be put first before referencing in a query in union
                                else:
                                    with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[temp_view_name].append({attribute_node.unique_name : mvd_with_clause_str})
                            select_clause.append(f"COALESCE({with_table_name}.{attribute_node.name}, ARRAY[]::text[]) AS {attr_name}")
                        else:#mvd stored as array
                            select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")
                    else:
                        select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")

            node_cover_node_mapped_table = node_cover_node.mapped_table
            for attr_name in relevant_table_attribute_lists[node_cover_node_mapped_table]:
                #adding the relevant folded attribute to the full view of the entity
                #so that corresponding view can be used when writing select * queries for folded weak entity/relationship
                if (attr_name not in entity_node_attributes) and (attr_name in entity_node_mapped_table_all_attributes):#folded weak entity/relationship
                    found_table_name = node_cover_node_mapped_table[1]
                    select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")

        else:#node_cover_node is entity_node itself - all attributes from node itself needed except for role attribute - mvds could be in a separate table - no filtering of attributes
            for attribute in node_cover_node.attribute_list:
                attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                if attr_name in entity_node_attributes:#filter "role" attribute in attribute_list

                    if "pk_name" in attribute:
                        found = node_cover_node.mapped_table#pk attributes of node come from mapped table
                        found_table_name = found[1] if found else None
                    elif "name" in attribute:#non pk attributes may come from node mapped table or other table - e.g. parent attributes of subclass if subclass is partially by itself, mvd in separate table
                        found = [t for t in relevant_table_attribute_lists if attr_name in relevant_table_attribute_lists[t]]
                        found_table_name = found[0][1] if found else None

                    if attribute.get("is_multivalued", False):
                        if attribute.get("is_in_separate_table", False):
                            attribute_node = graph.get_node_by_name(attribute.get("unique_name", None))
                            assert attribute_node
                            with_table_name = attribute_node.entity.unique_name + "_" + attribute_node.name
                            if with_table_name not in mvd_cte_built_tables:
                                mvd_with_clause_str = ""
                                mvd_select_clause = []
                                mvd_from_clause = []
                                mvd_where_clause = []
                                mvd_group_by_clause = []
                                generate_with_clause_for_mvd_table(attribute_node, tables, types, graph, mvd_select_clause, mvd_from_clause, mvd_where_clause, mvd_group_by_clause)
                                mvd_select_clause_str = ", ".join(mvd_select_clause)
                                mvd_from_clause_str = ", ".join(mvd_from_clause)
                                mvd_where_clause_str = " AND ".join(mvd_where_clause)
                                mvd_group_by_clause_str = ", ".join(mvd_group_by_clause)
                                mvd_with_clause_str += (f"{with_table_name} AS (SELECT {mvd_select_clause_str} FROM {mvd_from_clause_str} WHERE {mvd_where_clause_str} "
                                                        f"GROUP BY {mvd_group_by_clause_str})")
                                with_clause.append(mvd_with_clause_str)
                                mvd_cte_built_tables.append(with_table_name)
                                if temp_view_name not in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover:
                                    with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[temp_view_name] = [{attribute_node.unique_name : mvd_with_clause_str}]
                                else:
                                    with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[temp_view_name].append({attribute_node.unique_name : mvd_with_clause_str})
                            select_clause.append(f"COALESCE({with_table_name}.{attribute_node.name}, ARRAY[]::text[]) AS {attr_name}")
                        else:#mvd stored as array
                            select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")
                    else:
                        select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")

            node_cover_node_mapped_table = node_cover_node.mapped_table
            for attr_name in relevant_table_attribute_lists[node_cover_node_mapped_table]:
                #adding the relevant folded attribute to the full view of the entity
                #so that corresponding view can be used when writing select * queries for folded weak entity/relationship
                if (attr_name not in entity_node_attributes) and (attr_name in entity_node_mapped_table_all_attributes):#folded weak entity/relationship
                    found_table_name = node_cover_node_mapped_table[1]
                    select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")

        select_clause_str = ", ".join(select_clause)
        from_clause_str = ", ".join(from_clause)
        join_clause_str = " ".join(join_clause)
        left_join_clause_str = " ".join(left_join_clause)
        where_clause_str = ", ".join(where_clause)

        node_cover_node_select_all_clause = ""
        node_cover_node_select_all_clause += f"SELECT {select_clause_str} FROM {from_clause_str}"

        if join_clause:
            node_cover_node_select_all_clause += f" {join_clause_str}"
        if left_join_clause:
            node_cover_node_select_all_clause += f" {left_join_clause_str}"
        if where_clause:
            node_cover_node_select_all_clause += f" WHERE {where_clause_str}"
        union_clause.append(node_cover_node_select_all_clause)

    union_clause_str = " UNION ALL ".join(union_clause)
    union_with_table_name = "temp_" + entity_node.unique_name
    union_with_clause_str = f"{union_with_table_name} AS ({union_clause_str})"
    with_clause.append(union_with_clause_str)
    #entity with folded weak entity/relationship clause is saved to use for weak entity/relationship node select * query
    if temp_view_name not in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover:
        with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[temp_view_name] = [{entity_node.unique_name : union_with_clause_str}]
    else:
        with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[temp_view_name].append({entity_node.unique_name : union_with_clause_str})

    return temp_view_name


#only contained_all_descendants/all by itself children can be in the node_cover of the no_table node
def generate_select_query_for_no_table_entity_helper(no_table_node, child_node, child_pks_and_inherited_attribute_list_from_no_table_parent, no_table_parent_attribute_list,
                                                     with_clause_for_no_table_entity, tables_in_with_clause_for_no_table_entity, tables, types, graph):
    relevant_tables = []
    created_tables_by_names = {table[0]:table for table in tables}
    for sort_key, select_table in child_node.select_all_tables:
        if select_table in created_tables_by_names:#if table is an actual physical table created in db
            relevant_tables.append(created_tables_by_names[select_table])
        else:#table view coming from an all by itself node - this view is not an actual physical table - a view generated from node_cover for full information
            table_node = graph.get_node_by_sort_key(sort_key)
            assert table_node.is_entity() and table_node.is_all_by_itself and len(table_node.children)>0
            assert select_table == "temp_" + table_node.unique_name
            #mapped table of an all by itself node contains tuples coming from itself, however for the purpose of defining the attribute list for view, can use that view
            new_table_info = [select_table] + created_tables_by_names[table_node.mapped_table[1]][1:]#view has the same attribute list from mapped table of all by itself node
            relevant_tables.append(new_table_info)

    relevant_tables_keys_names_sorted = sorted(list(child_node.select_all_tables), key=lambda x: x[0])
    relevant_table_attribute_lists = {}
    for table in relevant_tables:
        table_tuple = next((t for t in relevant_tables_keys_names_sorted if t[1] == table[0]), None)
        relevant_table_attribute_lists[table_tuple] = [attribute_info[0] for attribute_info in table[1]]

    if child_node.mapped_table:#e.g. query is SELECT * from Person; but Person may not have a table - in that scenario, need to union all children
        select_clause = []
        from_clause = []
        join_clause = []
        left_join_clause = []

        mapped_table = get_mapped_table_for_entity_or_relationship(graph, child_node)#(sort_key, mapped_table)
        from_clause.append(mapped_table[1])

        #non-leaf all by itself may have node cover > 1 - generates the view which has the full coverage for itself - hence no need of joins
        #for other types of child nodes(contained_all_descendants or leaf all by itself nodes or non-leaf all by itself with node cover==1) - join step required
        #if child_node.is_contained_all_descendants or (child_node.is_all_by_itself and len(child_node.children)==0):#equivalent of checking the node cover size
        if len(child_node.node_cover) == 1:
            tables_sorted_reverse = sorted(relevant_tables_keys_names_sorted, key=lambda x: x[0], reverse=True)
            if len(tables_sorted_reverse)>1:#if joins needed - add pk, fk join clauses
                for joining_table in tables_sorted_reverse:
                    node = graph.get_node_by_sort_key(joining_table[0])
                    if node.is_attribute():
                        assert node.is_attribute() and node.is_multivalued and node.is_in_separate_table#only mvd joins happen and only mvd joins require join clauses
                        assert node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple)
                        with_table_name = node.entity.unique_name + "_" + node.name
                        if node.entity.unique_name == no_table_node.unique_name:#only consider mvds coming from no_table
                            child_pk = child_node.key.table_key[0][0]#since child is a strong entity, consists of single pk
                            left_join_clause.append(f"LEFT JOIN {with_table_name} ON {with_table_name}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{mapped_table[1]}.{child_pk}")


        for node_name in child_node.select_all_nodes:
            select_all_node = graph.get_node_by_name(node_name)
            assert select_all_node.is_entity()

            if select_all_node.is_contained_all_descendants or (select_all_node.is_all_by_itself and len(select_all_node.node_cover)==1):#contained_all_descendants or all by itself with no node cover - no need of view
                for with_temp_table_dict in with_clause_mvd_cte_temp_tables_for_nodes_with_no_node_cover[select_all_node.unique_name]:
                    for with_temp_table_name, with_temp_table_clause in with_temp_table_dict.items():
                        mvd_entity_name = with_temp_table_name.split(".")[0]#derive entity_name from format -> attribute_node.unique_name - user.mv_user
                        #filter for mvds coming from no_table
                        if mvd_entity_name == no_table_node.unique_name and with_temp_table_name not in tables_in_with_clause_for_no_table_entity:
                            with_clause_for_no_table_entity.append(with_temp_table_clause)#append the temp table for mvd tables
                            tables_in_with_clause_for_no_table_entity.append(with_temp_table_name)

            if select_all_node.is_entity() and len(select_all_node.node_cover)>1:#can be a subclass or root in hierarchy
                for with_temp_table_dict in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[select_all_node.unique_name]:
                    for with_temp_table_name, with_temp_table_clause in with_temp_table_dict.items():
                        if with_temp_table_name not in tables_in_with_clause_for_no_table_entity:
                            with_clause_for_no_table_entity.append(with_temp_table_clause)#append the temp table view(including mvd tables) with full table construction for node
                            tables_in_with_clause_for_no_table_entity.append(with_temp_table_name)

            select_all_node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, select_all_node)

            #for non-leaf all by itself node - full table view is already built in with clause temp table
            #all attributes for the all by itself are in the temp table - even all the mvd attributes coming from separate tables are aggregated and folded
            #hence temp table view is sufficient and complete to get all attributes
            if select_all_node.is_entity() and len(select_all_node.node_cover)>1:#can be a root or subclass in hierarchy
                assert select_all_node.is_all_by_itself#has to be all by itself since no_table node node_cover consists of contained_all_descendants/all and if select_all_node in node_cover
                                                                #has len(select_all_node.node_cover)>1 - it cannot be contained_all_descendants - has to be all by itself
                for attribute in select_all_node.attribute_list:
                    if select_all_node.unique_name != child_node.unique_name:
                        if "pk_name" in attribute:#from other nodes need only non-pk attributes since pks are already coming from entity_relationship node itself
                            continue#avoid executing rest of the body in the loop
                    attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                    if attr_name in child_pks_and_inherited_attribute_list_from_no_table_parent:#filter attributes only from no_table parent or pks
                        attr_index = child_pks_and_inherited_attribute_list_from_no_table_parent.index(attr_name)
                        assert attr_name == no_table_parent_attribute_list[attr_index] if attr_index != 0 else True#checking all other attributes except pk - assume single attribute pk - 0th index
                        parent_attr_name = no_table_parent_attribute_list[attr_index] if attr_index==0 else attr_name#for pks get parent's pk name - e.g. if person no_table - set attr_name to
                                                                                                              #person_id instead of student_id

                        found_table_name = "temp_" + select_all_node.unique_name#full table representation view is named "temp_"+node.unique_name for all by itself nodes
                        assert found_table_name==select_all_node_mapped_table[1]
                        select_clause.append(f"{found_table_name}.{attr_name} AS {parent_attr_name}")

            else:#not a node distributed in node cover - need to build the attribute list - might be coming from different tables
                for attribute in select_all_node.attribute_list:
                    if select_all_node.unique_name != child_node.unique_name:
                        if "pk_name" in attribute:#from other nodes need only non-pk attributes since pks are already coming from entity_relationship node itself
                            continue#avoid executing rest of the body in the loop
                    attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                    if attr_name in child_pks_and_inherited_attribute_list_from_no_table_parent:#filter attributes only from no_table parent or pks
                        attr_index = child_pks_and_inherited_attribute_list_from_no_table_parent.index(attr_name)
                        assert attr_name == no_table_parent_attribute_list[attr_index] if attr_index != 0 else True#checking all other attributes except pk - assume single attribute pk - 0th index
                        parent_attr_name = no_table_parent_attribute_list[attr_index] if attr_index==0 else attr_name

                        if "pk_name" in attribute:
                            found = select_all_node_mapped_table#pk attributes of an entity come from mapped table only
                            found_table_name = found[1] if found else None
                        elif "name" in attribute:#non pk attributes may come from node mapped table or other table - e.g. parent attributes of subclass if subclass is partially by itself, mvd in separate table
                            found = [t for t in relevant_table_attribute_lists if attr_name in relevant_table_attribute_lists[t]]
                            found_table_name = found[0][1] if found else None
                        if attribute["pk_type" if "pk_type" in attribute else "type"] == 'COMPOSITE':
                            if found:
                                # not split up
                                select_clause.append(f"{found_table_name}.{attr_name} AS {parent_attr_name}")
                            else:
                                # look for attr_name__ in the attribute lists
                                split_parts = []
                                for t in relevant_table_attribute_lists:
                                    for a in relevant_table_attribute_lists[t]:
                                        if f"{attr_name}__" in a:
                                            split_parts.append(a)
                                select_clause.extend([f"{t} AS {t}" for t in split_parts])
                        elif attribute.get("is_multivalued", False):
                            if attribute.get("is_in_separate_table", False):#mvd tables are already added in with clause
                                attribute_node = graph.get_node_by_name(attribute.get("unique_name", None))
                                assert attribute_node
                                select_clause.append(f"COALESCE({with_table_name}.{attribute_node.name}, ARRAY[]::text[]) AS {attribute_node.name}")
                            else:
                                select_clause.append(f"{found_table_name}.{attr_name} AS {parent_attr_name}")
                        else:
                            select_clause.append(f"{found_table_name}.{attr_name} AS {parent_attr_name}")

        select_clause_str = ", ".join(select_clause)
        from_clause_str = ", ".join(from_clause)
        join_clause_str = " ".join(join_clause)
        left_join_clause_str = " ".join(left_join_clause)


        select_all_clause = ""
        select_all_clause += f"SELECT {select_clause_str} FROM {from_clause_str}"
        if join_clause:
            select_all_clause += f" {join_clause_str}"
        if left_join_clause:
            select_all_clause += f" {left_join_clause_str}"

        return select_all_clause

def generate_select_query_for_single_folded_weak_entity(weak_entity_node, tables, types, graph):
    relevant_tables = []
    created_tables_by_names = {table[0]:table for table in tables}
    for sort_key, select_table in weak_entity_node.select_all_tables:
        if select_table in created_tables_by_names:#if table is an actual physical table created in db
            relevant_tables.append(created_tables_by_names[select_table])
        else:#table view coming from a node distributed in node_cover - this view is not an actual physical table - a view generated from node_cover for full information
            table_node = graph.get_node_by_sort_key(sort_key)
            assert table_node.is_entity() and len(table_node.node_cover)>1#a node mapped_table is incomplete for a node distributed in node_cover
            assert select_table == "temp_" + table_node.unique_name
            #mapped table of a node distributed in node_cover contains only a subset of all relevant tuples, however for the purpose of defining the attribute list for view, can use that table
            new_table_info = [select_table] + created_tables_by_names[table_node.mapped_table[1]][1:]#view has the same attribute list from mapped table
            relevant_tables.append(new_table_info)

    relevant_tables_keys_names_sorted = sorted(list(weak_entity_node.select_all_tables), key=lambda x: x[0])
    relevant_table_attribute_lists = {}
    for table in relevant_tables:
        table_tuple = next((t for t in relevant_tables_keys_names_sorted if t[1] == table[0]), None)
        relevant_table_attribute_lists[table_tuple] = [attribute_info[0] for attribute_info in table[1]]

    if weak_entity_node.mapped_table:#e.g. query is SELECT * from Person; but Person may not have a table - in that scenario, need to union all children
        with_clause = []
        select_clause = []
        from_clause = []
        join_clause = []
        left_join_clause = []
        where_clause = []
        group_by_clause = []
        cross_join_lateral_clause = []
        weak_entity_unique_name_char = weak_entity_node.unique_name[0]

        depending_entities = weak_entity_node.select_all_nodes
        strong_parent_entity = graph.get_node_by_name(depending_entities[-1])#only 1 strong parent exists in depending entities - last in the list
        assert strong_parent_entity.is_entity() and not strong_parent_entity.is_weak_entity

        mapped_table = get_mapped_table_for_entity_or_relationship(graph, weak_entity_node)#weak entity mapped_table - (sort_key, mapped_table)
        from_clause.append(mapped_table[1])
        tables_sorted_reverse = sorted(relevant_tables_keys_names_sorted, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table
        if len(tables_sorted_reverse)>1:#if joins needed - add pk, fk join clauses
            for joining_table in tables_sorted_reverse:
                node = graph.get_node_by_sort_key(joining_table[0])
                if not node.is_attribute():

                    #node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, node)
                    #assert node_mapped_table in relevant_tables_keys_names_sorted

                    #If weak entity's strong parent entity is a subclass and be partial/contained, there would be joining table\s coming from subclass's top parents
                    #These top parents may have a node cover. But if the subclass's node cover is 1, all required tuples(in full/sub set of attributes) are already in subclass's mapped table
                    #Subclass only need top parents' original mapped tables to generate full attribute cover since all inserts relevant to subclass will be in the
                    #top parent's original mapped table - no need to gather all tuples of top parents from views.
                    #Hence it is correct to map node_mapped_table to node.mapped_table for all nodes corresponding to joining tables
                    #non-attribute nodes relevant to joining tables could be other depending parent weak entities, strong parent entity, and its parents if strong parent is partial/contained
                    if (strong_parent_entity.is_subclass and len(strong_parent_entity.node_cover)==1 and
                                (strong_parent_entity.is_partially_by_itself or strong_parent_entity.is_contained_in_parent)):
                        node_mapped_table = node.mapped_table
                    else:
                        node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, node)
                    assert node_mapped_table in relevant_tables_keys_names_sorted


                    if node.key.reference_table is not None:
                        if node.key.table_key and isinstance(node.key.table_key[0], tuple):#strong entity, strong subclass entity
                            node_join_clause = []
                            assert len(node.key.table_key) == 1
                            for i in range(len(node.key.table_key)):
                                if node.key.reference_table[i] in [t[1] for t in relevant_tables_keys_names_sorted]:
                                    if (node_mapped_table[1] != node.key.reference_table[i]) and (node.mapped_table[1] != node.key.reference_table[i]):
                                        node_join_clause.append(f"{node_mapped_table[1]}.{node.key.table_key[i][0]} {"="} {node.key.reference_table[i]}.{node.key.reference_key[i][0]}")
                            node_join_clause_str = " AND ".join(node_join_clause)
                            assert len(node.key.reference_table) == 1
                            if node_join_clause_str:
                                join_clause.append(f"JOIN {node.key.reference_table[0]} AS {node.key.reference_table[0]} ON " + node_join_clause_str)
                        elif node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple):#weak entity, relationship
                            assert len(node.key.table_key) == 2
                            for i in range(len(node.key.table_key)):
                                #for weak entity len(node.key.reference_table) is 1 and for relationship it is 2
                                #only for i=0(parent key), following condition is executed for weak entity,
                                if len(node.key.reference_table) >= i+1:#for weak entity reference table added for parent only, for relationship ref table added for each participating entity
                                    if (node_mapped_table[1] != node.key.reference_table[i]) and node.mapped_table[1] != node.key.reference_table[i]:
                                        node_join_clause = []
                                        reference_entity = graph.get_node_by_name(node.key.table_key_entities[i][0])#pk_entity = [[], []]
                                        if reference_entity.is_entity() and len(reference_entity.node_cover)>1:
                                            #if entity from which the reference table comes from is distributed in node_cover
                                            #full table representation view is named "temp_"+node.unique_name for node distributed in node_cover
                                            reference_table_name = "temp_" + reference_entity.unique_name
                                            for j in range(len(node.key.table_key[i])):
                                                node_join_clause.append(f"{node_mapped_table[1]}.{node.key.table_key[i][j][0]} {"="} "
                                                                        f"{reference_table_name}.{node.key.reference_key[i][j][0]}")
                                            node_join_clause_str = " AND ".join(node_join_clause)
                                            if node_join_clause_str:
                                                join_clause.append(f"JOIN {reference_table_name} AS {reference_table_name} ON " + node_join_clause_str)
                                        else:
                                            for j in range(len(node.key.table_key[i])):
                                                node_join_clause.append(f"{node_mapped_table[1]}.{node.key.table_key[i][j][0]} {"="} {node.key.reference_table[i]}.{node.key.reference_key[i][j][0]}")
                                            node_join_clause_str = " AND ".join(node_join_clause)
                                            if node_join_clause_str:
                                                join_clause.append(f"JOIN {node.key.reference_table[i]} AS {node.key.reference_table[i]} ON " + node_join_clause_str)

                else:#mvd in separate table
                    assert node.is_multivalued
                    assert node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple)
                    with_table_name = node.entity.unique_name + "_" + node.name
                    assert node.entity.unique_name != weak_entity_node.unique_name#since weak_entity node is folded, its own mvds cannot be in separate tables
                    if node.entity.unique_name != weak_entity_node.unique_name:#mvd in separate table coming from a differnt node - not node itself
                        if node.entity.is_weak_entity or (not node.entity.is_subclass and not len(node.entity.children)>0):#mvd coming from a (weak entity) or (non-subclass non-root strong entity) - pks/joining reference table no change for mvd table
                            left_join_clause.append(f"LEFT JOIN {with_table_name} ON {with_table_name}.{node.key.table_key[0][0][0]} {"="} {node.key.reference_table[0]}.{node.key.reference_key[0][0][0]}")
                        else:##mvd coming from subclass or root strong entity - pks/joining reference table can change for mvd tables
                            #mvd from a subclass/root - pk in mvd table may not match subclass pk - e.g. mv_person table has person_id, and student has student_id
                            #mvd table's joining reference table also should be changed to student
                            #e.g. LEFT JOIN person_mv on person_mv.person_id = person.person_id -> LEFT JOIN person_mv on person_mv.person_id = student.student_id (if student on separate table)
                            #since mvd's entity belongs to a hierarchy - # of pks of the entity should be 1 - subclass/root is a strong entity
                            lowest_level_subclass_or_root_name = get_lowest_level_subclass_or_root_in_select_all_nodes_for_entity(graph, weak_entity_node)
                            assert lowest_level_subclass_or_root_name
                            lowest_level_subclass = graph.get_node_by_name(lowest_level_subclass_or_root_name)
                            entity_table_to_join_with_mvd_table = lowest_level_subclass.mapped_table[1]
                            pk_of_entity_table_to_join_with_mvd_table = lowest_level_subclass.key.table_key[0][0]
                            left_join_clause.append(f"LEFT JOIN {with_table_name} ON {with_table_name}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{entity_table_to_join_with_mvd_table}.{pk_of_entity_table_to_join_with_mvd_table}")

        for node_name in weak_entity_node.select_all_nodes:
            select_all_node = graph.get_node_by_name(node_name)

            if select_all_node.is_entity() and len(select_all_node.node_cover)>1:#can be a subclass or root in hierarchy
                temp_view_name = select_all_node.unique_name + "_" + weak_entity_node.unique_name
                if temp_view_name not in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover:
                    generated_view = generate_temp_view_with_clause_for_entity_with_node_cover(select_all_node, weak_entity_node, tables, types, graph)
                    assert generated_view == temp_view_name
                for with_temp_table_dict in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[temp_view_name]:
                    for with_temp_table_name, with_temp_table_clause in with_temp_table_dict.items():
                        with_clause.append(with_temp_table_clause)#append the temp table view(including mvd tables) with full table construction for node

            select_all_node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, select_all_node)

            #for an entity which belongs to a hierarchy, and contained in parent, need to consider each child by role type to get all tuples for entity
            #e.g. hierarchy Person -> Customer(20 tuples) -> Prime Customer(30) -> Family prime(10)
            #Customer, Prime Customer in same relation_1(Person table), Family prime all by itself in relation_2
            #Person - all by itself, Customer - contained in parent, Prime Customer - contained in parent, Family prime - all by itself
            #1. 20 entries with role_type 'customer' and 30 with 'primecustomer' and 10 with role_type 'familyprime' in relation_1
            #2. 10 entries in relation_2
            #e.g. If Family Prime is partially_by_itself or all_by_itself - all tuples of Family Prime
            #has a corresponding tuple in Person table - so select * from Customer == select * from relation_1 where role in ('customer','primecustomer', 'familyprime')
            #select * from primecustomer == select * from relation_1 where role in ('primecustomer', 'familyprime')
            #select * from familyprime == select * from relation_2
            #select * from person == select * from relation_1 - no need to filter by role
            #in hierarchy, if atleast one child of node is contained_in_parent - then node has role column, with each tuple identified by child name
            #in this example in relation_1 - 20 entries with role_type 'customer' and 30 with 'primecustomer' and 10 with role_type 'familyprime' in relation_1
            if select_all_node.is_entity() and select_all_node.is_subclass and select_all_node.is_contained_in_parent and len(select_all_node.node_cover)<=1:
                #no view built since node covers itself
                #only if contained_in_parent select_all_node doesn't build a view, add this - otherwise view has already filtered the tuples for select_all_node
                if len(select_all_node.children)>0:#entity_or_relationship_node can be any sub parent which is contained in parent
                    assert "role" in relevant_table_attribute_lists[select_all_node_mapped_table]
                    # collect entity names (entity + contained children)
                    all_entities = {select_all_node.unique_name}#add entity itself
                    #add all children rooted at node
                    find_all_children_rooted_at_node(select_all_node, all_entities)
                    all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                    where_clause.append(f"{select_all_node_mapped_table[1]}.{"role"} {"IN"} ({all_entities_str})")
                else:#entity itself - where clause would be just role in (entity_name)
                    #for leaf subclass contained in parent
                    assert "role" in relevant_table_attribute_lists[select_all_node_mapped_table]
                    where_clause.append(f"{select_all_node_mapped_table[1]}.{"role"} {"IN"} ('{select_all_node.unique_name}')")

            #for node distributed in its node_cover - full table view is already built in with clause temp table
            #all attributes for the node distributed in its node_cover are in the temp table - even all the mvd attributes coming from separate tables are aggregated and folded
            #hence temp table view is sufficient and complete to get all attributes
            if select_all_node.is_entity() and len(select_all_node.node_cover)>1:#can be a root or subclass in hierarchy
                for attribute in select_all_node.attribute_list:
                    assert select_all_node.unique_name != weak_entity_node.unique_name#having node distributed is not an option for a weak entity - hence 2 nodes can't be equal
                    if "pk_name" in attribute:#from other nodes need only non-pk attributes since pks are already coming from entity_relationship node itself
                        continue#avoid executing rest of the body in the loop
                    attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                    found_table_name = "temp_" + select_all_node.unique_name#full table representation view is named "temp_"+node.unique_name for node distributed in its node_cover
                    assert found_table_name==select_all_node_mapped_table[1]
                    select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")

            else:##not a node distributed in its node_cover(could be a strong or weak parent entity) - need to build the attribute list - might be coming from different tables
                for attribute in select_all_node.attribute_list:
                    if select_all_node.unique_name != weak_entity_node.unique_name:
                        if "pk_name" in attribute:#from other nodes need only non-pk attributes since pks are already coming from weak_entity node itself
                            continue#avoid executing rest of the body in the loop

                    attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                    if "pk_name" in attribute:
                        found = select_all_node_mapped_table
                        found_table_name = found[1] if found else None
                    elif "name" in attribute:
                        found = [t for t in relevant_table_attribute_lists if attr_name in relevant_table_attribute_lists[t]]
                        found_table_name = found[0][1] if found else None

                    #e.g. When section is folded in course, course has an attribute named section, and all attributes sec_id(discriminator), sec_name inside that section attribute as objects of array
                    if select_all_node.unique_name == weak_entity_node.unique_name and (attr_name not in
                                                                                        relevant_table_attribute_lists[mapped_table]):#attributes coming from folded weak entity - attributes are folded not in table
                        assert weak_entity_node.unique_name in relevant_table_attribute_lists[mapped_table]#weak_entity name as an attribute - encapsulating all attributes from weak entity as an array
                                        #mapped_table is the weak entity mapped_table - if folded in a node distributed in node_cover node mapped_table is the table_view otherwise same as weak_entity.mapped_table
                        select_clause.append(f"{weak_entity_unique_name_char} ->> '{attr_name}' AS {attr_name}")
                        continue#avoid executing rest of the body in the loop

                    if attribute["pk_type" if "pk_type" in attribute else "type"] == 'COMPOSITE':
                        if found:
                            # not split up
                            select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")
                        else:
                            # look for attr_name__ in the attribute lists
                            split_parts = []
                            for t in relevant_table_attribute_lists:
                                for a in relevant_table_attribute_lists[t]:
                                    if f"{attr_name}__" in a:
                                        split_parts.append(a)
                            select_clause.extend([f"{t} AS {t}" for t in split_parts])
                    elif attribute.get("is_multivalued", False):
                        if attribute.get("is_in_separate_table", False):
                            attribute_node = graph.get_node_by_name(attribute.get("unique_name", None))
                            assert attribute_node
                            with_table_name = attribute_node.entity.unique_name + "_" + attribute_node.name
                            mvd_with_clause_str = ""
                            mvd_select_clause = []
                            mvd_from_clause = []
                            mvd_where_clause = []
                            mvd_group_by_clause = []
                            generate_with_clause_for_mvd_table(attribute_node, tables, types, graph, mvd_select_clause, mvd_from_clause, mvd_where_clause, mvd_group_by_clause)
                            mvd_select_clause_str = ", ".join(mvd_select_clause)
                            mvd_from_clause_str = ", ".join(mvd_from_clause)
                            mvd_where_clause_str = " AND ".join(mvd_where_clause)
                            mvd_group_by_clause_str = ", ".join(mvd_group_by_clause)
                            mvd_with_clause_str += (f"{with_table_name} AS (SELECT {mvd_select_clause_str} FROM {mvd_from_clause_str} WHERE {mvd_where_clause_str} "
                                                        f"GROUP BY {mvd_group_by_clause_str})")
                            with_clause.append(mvd_with_clause_str)
                            select_clause.append(f"COALESCE({with_table_name}.{attribute_node.name}, ARRAY[]::text[]) AS {attribute_node.name}")
                        else:
                            select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")
                    else:
                        select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")

            if select_all_node.unique_name == weak_entity_node.unique_name:
                weak_entity_node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, weak_entity_node)
                cross_join_lateral_clause.append(f"CROSS JOIN LATERAL jsonb_array_elements({weak_entity_node_mapped_table[1]}.{weak_entity_node.unique_name}) "
                                                 f"AS {weak_entity_unique_name_char}")
                where_clause.append(f"jsonb_array_length({weak_entity_node_mapped_table[1]}.{weak_entity_node.unique_name}) > 0")

        with_clause_without_with = ", ".join(with_clause)
        with_clause_str = ""
        if len(with_clause) > 0:
            with_clause_str += "WITH "
        with_clause_str += with_clause_without_with
        select_clause_str = ", ".join(select_clause)
        from_clause_str = ", ".join(from_clause)
        join_clause_str = " ".join(join_clause)
        left_join_clause_str = " ".join(left_join_clause)
        where_clause_str = " AND ".join(where_clause)
        cross_join_lateral_clause_str = cross_join_lateral_clause[0]
        # check if group by is needed
        if "AGG" in select_clause_str:#the group by clause is modified to include all attributes(except AGG attributes) to do the group by - each tuple grouped by all attributes
            group_by_clause = [c.split()[0] for c in select_clause if "AGG" not in c]#group by all attributes except attributes with 'AGG' in tuple
            group_by_clause_str = ", ".join(group_by_clause)

        select_all_clause = ""
        if with_clause:
            select_all_clause += f"{with_clause_str} "
        select_all_clause += f"SELECT {select_clause_str} FROM {from_clause_str}"
        if join_clause:
            select_all_clause += f" {join_clause_str}"
        if left_join_clause:
            select_all_clause += f" {left_join_clause_str}"
        if cross_join_lateral_clause:
            select_all_clause += f" {cross_join_lateral_clause_str}"
        if where_clause:
            select_all_clause += f" WHERE {where_clause_str}"
        if group_by_clause:
            select_all_clause += f" GROUP BY {group_by_clause_str}"
        memoized_select_all_queries[weak_entity_node.unique_name] = select_all_clause
    return select_all_clause


#in sql query of select * from recursive relationship - attribute order - pks, attributes from entity1, attributes from entity2
#role_name is added to entity2 attributes set
#pk may be in order [entity1, entity2](if entity1 is M) OR [entity2, entity1](if entity2 is M) OR [entity1, entity2](if M:N)
#participating entity of recursive relationship can be strong entity/weak entity
def generate_select_query_for_recursive_relationship(entity_or_relationship_node, tables, types, graph):
    relevant_tables = []
    created_tables_by_names = {table[0]:table for table in tables}
    for sort_key, select_table in entity_or_relationship_node.select_all_tables:
        if select_table in created_tables_by_names:#if table is an actual physical table created in db
            relevant_tables.append(created_tables_by_names[select_table])
        else:#table view coming from a node distributed in node_cover - this view is not an actual physical table - a view generated from node_cover for full information
            table_node = graph.get_node_by_sort_key(sort_key)
            assert table_node.is_entity() and len(table_node.node_cover)>1#a node mapped_table is incomplete for a
                                                                          #node distributed in node_cover
            assert select_table == "temp_" + table_node.unique_name
            #mapped table of a node distributed in node_cover contains only a subset of all relevant tuples, however for the purpose of defining the attribute list for view, can use that table
            new_table_info = [select_table] + created_tables_by_names[table_node.mapped_table[1]][1:]#view has the same attribute list from mapped table
            relevant_tables.append(new_table_info)

    relevant_tables_keys_names_sorted = sorted(list(entity_or_relationship_node.select_all_tables), key=lambda x: x[0])
    relevant_table_attribute_lists = {}
    for table in relevant_tables:
        table_tuple = next((t for t in relevant_tables_keys_names_sorted if t[1] == table[0]), None)
        relevant_table_attribute_lists[table_tuple] = [attribute_info[0] for attribute_info in table[1]]

    if entity_or_relationship_node.mapped_table:#e.g. query is SELECT * from Person; but Person may not have a table - in that scenario, need to union all children
        with_clause = []
        select_clause = []
        from_clause = []
        join_clause = []
        left_join_clause = []
        where_clause = []
        group_by_clause = []

        tables_in_with_clause = []#to avoid duplicating same table view(If participating entity of a recursive relationship is distributed in node_cover)
        # or mvd table - e.g. If product has mvd table mv_attribute, and if a relationship is between phone(subclass of product)
        #and smart_watch(subclass of product) with clause for mv_attribute should be only added once

        role_name = ""
        assert entity_or_relationship_node.entity1.unique_name == entity_or_relationship_node.entity2.unique_name
        role1, role2 = entity_or_relationship_node.recursive_relationship_roles
        role_name = "_"+role2[:-3]#prereq

        #entity_relationship_node
        node_table_list = table_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.unique_name]
        node_table_list_sorted_reverse = sorted(node_table_list, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table
        node_relevant_table_attribute_lists = {}
        for table_tuple in node_table_list:
            assert table_tuple in relevant_table_attribute_lists
            node_relevant_table_attribute_lists[table_tuple] = relevant_table_attribute_lists[table_tuple]

        #entity1 side
        entity1_side_table_list = table_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.entity1.unique_name]
        entity1_side_table_list_sorted_reverse = sorted(entity1_side_table_list, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table
        if len(entity_or_relationship_node.entity1.node_cover)<=1:#entity1 is not distributed in a node_cover
            entity1_relevant_table_attribute_lists = {}
            for table_tuple in entity1_side_table_list:
                assert table_tuple in relevant_table_attribute_lists
                entity1_relevant_table_attribute_lists[table_tuple] = relevant_table_attribute_lists[table_tuple]
        else:#if entity1 is distributed in node_cover, no need to define a table list to cover entity1 attributes, since all attributes will be covered from built view
            entity1_relevant_table_attribute_lists = {}


        #entity2 side - same as entity1 side for recursive relationship
        entity2_side_table_list = table_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.entity2.unique_name]
        entity2_side_table_list_sorted_reverse = sorted(entity2_side_table_list, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table
        if len(entity_or_relationship_node.entity2.node_cover)<=1:#entity2 is not distributed in a node_cover
            entity2_relevant_table_attribute_lists = {}
            for table_tuple in entity2_side_table_list:
                assert table_tuple in relevant_table_attribute_lists
                entity2_relevant_table_attribute_lists[table_tuple] = relevant_table_attribute_lists[table_tuple]
        else:#if entity2 is distributed in node_cover, no need to define a table list to cover entity2 attributes, since all attributes will be covered from built view
            entity2_relevant_table_attribute_lists = {}


        #entity1_specifier/entity2_specifier - specifiers for table
        if check_if_relationship_is_1_N(entity_or_relationship_node):
            many_side_entity = entity_or_relationship_node.entity2 if entity_or_relationship_node.rel_dict['entity1']['one'] and not entity_or_relationship_node.rel_dict['entity2']['one'] \
                else entity_or_relationship_node.entity1
            assert many_side_entity == entity_or_relationship_node.entity1 == entity_or_relationship_node.entity2#recursive relationship
            if entity_or_relationship_node.mapped_table == many_side_entity.mapped_table:#relationship is folded
                entity1_specifier = ""
                entity2_specifier = role_name
            else:#1:M relationship is not folded
                entity1_specifier = ""
                entity2_specifier = role_name
        else:#M:N
            entity1_specifier = ""
            entity2_specifier = role_name
        #the specifiers can be summarized by setting entity1_specifier = "" and entity2_specifier = role_name


        mapped_table = get_mapped_table_for_entity_or_relationship(graph, entity_or_relationship_node)#(sort_key, mapped_table)
        from_clause.append(mapped_table[1])
        tables_sorted_reverse = sorted(relevant_tables_keys_names_sorted, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table
        if len(tables_sorted_reverse)>1 or entity_or_relationship_node.mapped_table == entity_or_relationship_node.entity1.mapped_table:#if recursive relationship is folded in
            #participating entity, and entity is a strong entity all by itself, no of joining tables would be 1.
            #but still join clause for second entity needs to be added

            def join_tables_helper(relationship_or_participating_entity, node, entity_side_table_list_sorted_reverse, node_specifier, entity_specifier, join_clause, left_join_clause):
                if not node.is_attribute():

                    #participating entity
                    if (relationship_or_participating_entity.is_entity() and relationship_or_participating_entity.is_subclass and
                            len(relationship_or_participating_entity.node_cover)==1 and
                            (relationship_or_participating_entity.is_contained_in_parent or relationship_or_participating_entity.is_partially_by_itself)):
                        #If participating entity node is a subclass with node cover 1, participating entity node's mapped_table contains all tuples - may not cover attribute set for tuples
                        #The joins can be happening with node itself, mvd attributes, and top parents to gain attribute cover.
                        #If the joining table node is not an attribute, node can be the entity node itself, or any top parent.
                        #These top parents may have a node cover. But if the participating entity node's node cover is 1, all required tuples(in full/sub set of attributes)
                        #are already in participating entity node's mapped table
                        #Participating entity node only need top parents' original mapped tables to generate full attribute cover since all inserts relevant to
                        #participating entity node will be in the top parent's original mapped table - no need to gather all tuples of top parents from views.
                        #Hence it is correct to map node_mapped_table to node.mapped_table for all nodes corresponding to joining tables
                        #parent distributed in a node cover doesn't affect to gain attribute cover for a subclass node with no node cover
                        node_mapped_table = node.mapped_table
                    elif relationship_or_participating_entity.is_entity() and relationship_or_participating_entity.is_weak_entity:
                        depending_entities = relationship_or_participating_entity.select_all_nodes
                        strong_parent_entity = graph.get_node_by_name(depending_entities[-1])#only 1 strong parent exists in depending entities - last in the list
                        assert strong_parent_entity.is_entity() and not strong_parent_entity.is_weak_entity
                        if (strong_parent_entity.is_subclass and len(strong_parent_entity.node_cover)==1 and
                                (strong_parent_entity.is_partially_by_itself or strong_parent_entity.is_contained_in_parent)):
                            #if participating entity is a weak entity whose strong parent is a subclass with node cover 1 and is partial/contained
                            #need to use node.mapped_table all nodes relevant to joining_tables
                            #non-attribute nodes coming from participating entity could other parent depending weak entities,
                            #strong parent entity, and its parents if strong parent is partial/contained
                            #for all those nodes, correct to use - node.mapped_table
                            node_mapped_table = node.mapped_table
                        else:#for all other scenarios, mapped_table is retrieved from the function
                            node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, node)
                    else:#for all other scenarios, mapped_table is retrieved from the function
                        node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, node)
                    assert node_mapped_table in tables_sorted_reverse

                    if node.key.reference_table is not None:
                        if node.key.table_key and isinstance(node.key.table_key[0], tuple):#strong entity, strong subclass entity
                            node_join_clause = []
                            assert len(node.key.table_key) == 1
                            for i in range(len(node.key.table_key)):
                                if node.key.reference_table[i] in [t[1] for t in entity_side_table_list_sorted_reverse]:
                                    if (node_mapped_table[1] != node.key.reference_table[i]) and (node.mapped_table[1] != node.key.reference_table[i]):
                                        node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][0]} {"="} "
                                                                f"{node.key.reference_table[i] + entity_specifier}.{node.key.reference_key[i][0]}")
                            node_join_clause_str = " AND ".join(node_join_clause)
                            assert len(node.key.reference_table) == 1
                            if node_join_clause_str:
                                join_clause.append(f"JOIN {node.key.reference_table[0]} AS {node.key.reference_table[0] + entity_specifier} ON " + node_join_clause_str)
                        elif node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple):#weak entity, relationship
                            assert len(node.key.table_key) == 2
                            for i in range(len(node.key.table_key)):
                                reference_entity = graph.get_node_by_name(node.key.table_key_entities[i][0])#pk_entity = [[], []]
                                reference_entity_full_view = "temp_" + reference_entity.unique_name
                                #for weak entity len(node.key.reference_table) is 1 and for relationship it is 2
                                #only for i=0(parent key), following condition is executed for weak entity,
                                if len(node.key.reference_table) >= i+1:#for weak entity reference table added for parent only, for relationship ref table added for each participating entity
                                    if ((node.key.reference_table[i] in [t[1] for t in entity_side_table_list_sorted_reverse]) or
                                            (reference_entity_full_view in [t[1] for t in entity_side_table_list_sorted_reverse])):#if entity is distributed in node_cover, its relevant
                                                                                                                                   #table is now its full table view
                                        #node_mapped_table and node.mapped_table may not be same when a node distributed in node_cover involved - affects to folded relationship/weak_entity
                                        #for folded weak entity/relationship - node.mapped_table is original mapped table with a subset of tuples and node_mapped_table is the table_view
                                        #both conditions need to be checked to see if there are join conditions since node.key.reference_table still points to original node.mapped_table
                                        if (node_mapped_table[1] != node.key.reference_table[i]) and (node.mapped_table[1] != node.key.reference_table[i]):
                                            if i==1:#second set of keys - of second participating entity
                                                entity_specifier +=  role_name #for the second entity - role_name is added - this is when relationship is recursive
                                            node_join_clause = []
                                            if reference_entity.is_entity() and len(reference_entity.node_cover)>1:
                                                #if entity from which the reference table comes from is distributed in node_cover
                                                #full table representation view is named "temp_"+node.unique_name for node distributed in node_cover
                                                reference_table_name = "temp_" + reference_entity.unique_name
                                                for j in range(len(node.key.table_key[i])):
                                                    node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                            f"{reference_table_name + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                node_join_clause_str = " AND ".join(node_join_clause)
                                                if node_join_clause_str:
                                                    join_clause.append(f"JOIN {reference_table_name} AS {reference_table_name + entity_specifier} ON " + node_join_clause_str)
                                            else:
                                                for j in range(len(node.key.table_key[i])):
                                                    node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                            f"{node.key.reference_table[i] + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                node_join_clause_str = " AND ".join(node_join_clause)
                                                if node_join_clause_str:
                                                    join_clause.append(f"JOIN {node.key.reference_table[i]} AS {node.key.reference_table[i] + entity_specifier} ON "
                                                                       + node_join_clause_str)

                                        else:#for recursive folded relationship, need to add one join clause for second entity
                                            #for recursive folded relationship, its mapped table is same as reference key table since it is folded in participating entity
                                            #e.g.#SELECT relation_12.phone_id AS phone_id, relation_12.single_bundle_phone_bundled_phone_phone_id AS single_bundle_phone_bundled_phone_phone_id,
                                            #relation_12.sku AS sku, relation_12.product_name AS product_name, relation_12.base_price AS base_price,
                                            #relation_12_single_bundle_phone.sku AS single_bundle_phone_sku, relation_12_single_bundle_phone.product_name AS single_bundle_phone_product_name,
                                            #relation_12_single_bundle_phone.base_price AS single_bundle_phone_base_price FROM relation_12
                                            #join relation_12 as relation_12_single_bundle_phone on relation_12_single_bundle_phone.phone_id = relation_12.single_bundle_phone_bundled_phone_phone_id
                                            if node.unique_name == entity_or_relationship_node.unique_name:
                                                assert node.mapped_table == node.entity1.mapped_table#folded recursive relationship
                                                if i==1:#second set of keys - of second participating entity
                                                    entity_specifier +=  role_name #for the second entity - role_name is added - this is when relationship is recursive
                                                    node_join_clause = []
                                                    if reference_entity.is_entity() and len(reference_entity.node_cover)>1:
                                                        #if entity from which the reference table comes from is distributed in node_cover
                                                        #full table representation view is named "temp_"+node.unique_name for node distributed in node_cover
                                                        reference_table_name = "temp_" + reference_entity.unique_name
                                                        for j in range(len(node.key.table_key[i])):
                                                            node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                                    f"{reference_table_name + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                        node_join_clause_str = " AND ".join(node_join_clause)
                                                        if node_join_clause_str:
                                                            join_clause.append(f"JOIN {reference_table_name} AS {reference_table_name + entity_specifier} ON " + node_join_clause_str)
                                                    else:
                                                        for j in range(len(node.key.table_key[i])):
                                                            node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                                    f"{node.key.reference_table[i] + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                        node_join_clause_str = " AND ".join(node_join_clause)
                                                        if node_join_clause_str:
                                                            join_clause.append(f"JOIN {node.key.reference_table[i]} AS {node.key.reference_table[i] + entity_specifier} ON "
                                                                               + node_join_clause_str)


            #first start from node itself
            for joining_table in node_table_list_sorted_reverse:
                node = graph.get_node_by_sort_key(joining_table[0])
                node_specifier = ""
                if not node.is_attribute():
                    #if a relationship folded to many side which is distributed in its node_cover, node's new mapped table is full table view of many side. Hence entity_or_relationship_node.mapped_table
                    #is not equal to joining_table which is the full table view of entity where full folded relationship is present
                    assert (entity_or_relationship_node.mapped_table == joining_table or len(entity_or_relationship_node.entity1.node_cover)>1)#entity1 and entity2 the same
                    assert entity1_side_table_list_sorted_reverse == entity2_side_table_list_sorted_reverse
                    join_tables_helper(entity_or_relationship_node, entity_or_relationship_node, entity1_side_table_list_sorted_reverse, node_specifier, entity1_specifier, join_clause, left_join_clause)#relationship node joining entity1/entity2
                else:#mvd in separate table
                    assert node.is_multivalued
                    assert node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple)
                    with_table_name = node.entity.unique_name + "_" + node.name
                    left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                            f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                            f"{node.key.reference_table[0] + node_specifier}.{node.key.reference_key[0][0][0]}")

            #entity_1 joining tables
            for joining_table in entity1_side_table_list_sorted_reverse:
                node = graph.get_node_by_sort_key(joining_table[0])
                node_specifier = entity1_specifier
                if not node.is_attribute():
                    join_tables_helper(entity_or_relationship_node.entity1, node, entity1_side_table_list_sorted_reverse, node_specifier, entity1_specifier, join_clause, left_join_clause)
                else:#mvd in separate table
                    assert node.is_multivalued
                    assert node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple)
                    with_table_name = node.entity.unique_name + "_" + node.name
                    if node.entity.unique_name == entity_or_relationship_node.entity1.unique_name:#mvd in separate table coming from node itself
                        left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                f"{node.key.reference_table[0] + node_specifier}.{node.key.reference_key[0][0][0]}")
                    else:#mvd in separate table coming from a differnt node - not node itself
                        if node.entity.is_weak_entity or (not node.entity.is_subclass and not len(node.entity.children)>0):#mvd coming from (weak entity) or (non-subclass non-root strong entity) - pks/joining reference table no change for mvd table
                            left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                    f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{node.key.reference_table[0] + node_specifier}.{node.key.reference_key[0][0][0]}")
                        else:##mvd coming from subclass or root strong entity - pks/joining reference table can change for mvd tables
                            #mvd from a subclass/root - pk in mvd table may not match subclass pk - e.g. mv_person table has person_id, and student has student_id
                            #mvd table's joining reference table also should be changed to student
                            #e.g. LEFT JOIN person_mv on person_mv.person_id = person.person_id -> LEFT JOIN person_mv on person_mv.person_id = student.student_id (if student on separate table)
                            #since mvd's entity belongs to a hierarchy - # of pks of the entity should be 1 - subclass/root is a strong entity
                            lowest_level_subclass_or_root_name = get_lowest_level_subclass_or_root_in_select_all_nodes_for_entity(graph, entity_or_relationship_node.entity1)
                            assert lowest_level_subclass_or_root_name
                            lowest_level_subclass = graph.get_node_by_name(lowest_level_subclass_or_root_name)
                            entity_table_to_join_with_mvd_table = lowest_level_subclass.mapped_table[1]
                            pk_of_entity_table_to_join_with_mvd_table = lowest_level_subclass.key.table_key[0][0]
                            left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                    f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{entity_table_to_join_with_mvd_table + node_specifier}.{pk_of_entity_table_to_join_with_mvd_table}")


            #entity_2 joining tables
            for joining_table in entity2_side_table_list_sorted_reverse:
                node = graph.get_node_by_sort_key(joining_table[0])
                node_specifier = entity2_specifier
                if not node.is_attribute():
                    join_tables_helper(entity_or_relationship_node.entity2, node, entity2_side_table_list_sorted_reverse, node_specifier, entity2_specifier, join_clause, left_join_clause)
                else:#mvd in separate table
                    assert node.is_multivalued
                    assert node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple)
                    with_table_name = node.entity.unique_name + "_" + node.name
                    if node.entity.unique_name == entity_or_relationship_node.entity2.unique_name:#mvd in separate table coming from node itself
                        left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                f"{node.key.reference_table[0] + node_specifier}.{node.key.reference_key[0][0][0]}")
                    else:#mvd in separate table coming from a differnt node - not node itself
                        if node.entity.is_weak_entity or (not node.entity.is_subclass and not len(node.entity.children)>0):#mvd coming from (weak entity) or (non-subclass non-root strong entity) - pks/joining reference table no change for mvd table
                            left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                    f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{node.key.reference_table[0] + node_specifier}.{node.key.reference_key[0][0][0]}")
                        else:##mvd coming from subclass or root strong entity - pks/joining reference table can change for mvd tables
                            #mvd from a subclass/root - pk in mvd table may not match subclass pk - e.g. mv_person table has person_id, and student has student_id
                            #mvd table's joining reference table also should be changed to student
                            #e.g. LEFT JOIN person_mv on person_mv.person_id = person.person_id -> LEFT JOIN person_mv on person_mv.person_id = student.student_id (if student on separate table)
                            #since mvd's entity belongs to a hierarchy - # of pks of the entity should be 1 - subclass/root is a strong entity
                            lowest_level_subclass_or_root_name = get_lowest_level_subclass_or_root_in_select_all_nodes_for_entity(graph, entity_or_relationship_node.entity2)
                            assert lowest_level_subclass_or_root_name
                            lowest_level_subclass = graph.get_node_by_name(lowest_level_subclass_or_root_name)
                            entity_table_to_join_with_mvd_table = lowest_level_subclass.mapped_table[1]
                            pk_of_entity_table_to_join_with_mvd_table = lowest_level_subclass.key.table_key[0][0]
                            left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                    f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{entity_table_to_join_with_mvd_table + node_specifier}.{pk_of_entity_table_to_join_with_mvd_table}")


        #adding attributes
        def add_attributes_helper(entity_or_relationship_node, select_all_node, table_tuples_with_relevant_attribute_lists,
                                  table_attribute_specifier, with_clause, select_clause, where_clause):

            if table_attribute_specifier == "":
                attribute_specifier = ""
            else:
                attribute_specifier = table_attribute_specifier[1:] + "_"#get underscore to back from front

            if select_all_node.is_entity() and len(select_all_node.node_cover)>1:#can be a subclass or root in hierarchy
                temp_view_name = select_all_node.unique_name + "_" + entity_or_relationship_node.unique_name
                if temp_view_name not in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover:
                    generated_view = generate_temp_view_with_clause_for_entity_with_node_cover(select_all_node, entity_or_relationship_node, tables, types, graph)
                    assert generated_view == temp_view_name
                for with_temp_table_dict in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[temp_view_name]:
                    for with_temp_table_name, with_temp_table_clause in with_temp_table_dict.items():
                        if with_temp_table_name not in tables_in_with_clause:
                            with_clause.append(with_temp_table_clause)#append the temp table view(and mvd tables) with full table construction for node
                            tables_in_with_clause.append(with_temp_table_name)

            select_all_node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, select_all_node)

            #if the folded relationship doesn't have total participation for many side - need to filter many side tuples based on if one side value is not null
            if select_all_node.is_relationship():
                assert entity_or_relationship_node.unique_name == select_all_node.unique_name
                if graph.config[select_all_node.unique_name] == "folded_to_many_side":
                    one_side_attribute = select_all_node.key.table_key[1][0][0]
                    where_clause.append(f"{select_all_node_mapped_table[1] + table_attribute_specifier}.{one_side_attribute} IS NOT NULL")


            #for an entity which belongs to a hierarchy, and contained in parent, need to consider each child by role type to get all tuples for entity
            #e.g. hierarchy Person -> Customer(20 tuples) -> Prime Customer(30) -> Family prime(10)
            #Customer, Prime Customer in same relation_1(Person table), Family prime all by itself in relation_2
            #Person - all by itself, Customer - contained in parent, Prime Customer - contained in parent, Family prime - all by itself
            #1. 20 entries with role_type 'customer' and 30 with 'primecustomer' and 10 with role_type 'familyprime' in relation_1
            #2. 10 entries in relation_2
            #e.g. If Family Prime is partially_by_itself or all_by_itself - all tuples of Family Prime
            #has a corresponding tuple in Person table - so select * from Customer == select * from relation_1 where role in ('customer','primecustomer', 'familyprime')
            #select * from primecustomer == select * from relation_1 where role in ('primecustomer', 'familyprime')
            #select * from familyprime == select * from relation_2
            #select * from person == select * from relation_1 - no need to filter by role
            #in hierarchy, if atleast one child of node is contained_in_parent - then node has role column, with each tuple identified by child name
            #in this example in relation_1 - 20 entries with role_type 'customer' and 30 with 'primecustomer' and 10 with role_type 'familyprime' in relation_1
            if select_all_node.is_entity() and select_all_node.is_subclass and select_all_node.is_contained_in_parent and len(select_all_node.node_cover)<=1:
                #only if contained_in_parent select_all_node doesn't have a view, add this - otherwise view has already filtered the tuples for select_all_node
                if len(select_all_node.children)>0:#entity_or_relationship_node can be any sub parent which is contained in parent
                    assert "role" in table_tuples_with_relevant_attribute_lists[select_all_node_mapped_table]
                    # collect entity names (entity + contained children)
                    all_entities = {select_all_node.unique_name}#add entity itself
                    #add all children rooted at node
                    find_all_children_rooted_at_node(select_all_node, all_entities)
                    all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                    where_clause.append(f"{select_all_node_mapped_table[1] + table_attribute_specifier}.{"role"} {"IN"} ({all_entities_str})")
                else:#entity itself - where clause would be just role in (entity_name)
                    #for leaf subclass contained in parent
                    assert "role" in table_tuples_with_relevant_attribute_lists[select_all_node_mapped_table]
                    where_clause.append(f"{select_all_node_mapped_table[1] + table_attribute_specifier}.{"role"} {"IN"} ('{select_all_node.unique_name}')")

            #for node distributed in its node_cover - full table view is already built in with clause temp table
            #all attributes for the node distributed in its node_cover are in the temp table - even all the mvd attributes coming from separate tables are aggregated and folded
            #hence temp table view is sufficient and complete to get all attributes
            if select_all_node.is_entity() and len(select_all_node.node_cover)>1:#can be a root or subclass in hierarchy
                for attribute in select_all_node.attribute_list:
                    if select_all_node.unique_name != entity_or_relationship_node.unique_name:
                        if "pk_name" in attribute:#from other nodes need only non-pk attributes since pks are already coming from entity_relationship node itself
                            continue#avoid executing rest of the body in the loop
                    attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                    found_table_name = "temp_" + select_all_node.unique_name#full table representation view is named "temp_"+node.unique_name for node distributed in its node_cover
                    assert found_table_name==select_all_node_mapped_table[1]
                    select_clause.append(f"{found_table_name + table_attribute_specifier}.{attr_name} AS {attribute_specifier + attr_name}")

            else:#not a node distributed in its node_cover - need to build the attribute list - might be coming from different tables
                for attribute in select_all_node.attribute_list:
                    if select_all_node.unique_name != entity_or_relationship_node.unique_name:
                        if "pk_name" in attribute:#from other nodes need only non-pk attributes since pks are already coming from entity_relationship node itself
                            continue#avoid executing rest of the body in the loop
                    attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                    if "pk_name" in attribute:
                        found = select_all_node_mapped_table
                        found_table_name = found[1] if found else None
                    elif "name" in attribute:#non pk attributes may come from node mapped table or other table - e.g. parent attributes of subclass, mvd in separate table
                        found = [table_tuple for table_tuple in table_tuples_with_relevant_attribute_lists if attr_name in table_tuples_with_relevant_attribute_lists[table_tuple]]
                        found_table_name = found[0][1] if found else None
                    if attribute["pk_type" if "pk_type" in attribute else "type"] == 'COMPOSITE':
                        if found:
                            # not split up
                            select_clause.append(f"{found_table_name + table_attribute_specifier}.{attr_name} AS {attribute_specifier + attr_name}")
                        else:
                            # look for attr_name__ in the attribute lists
                            split_parts = []
                            for t in table_tuples_with_relevant_attribute_lists:
                                for a in table_tuples_with_relevant_attribute_lists[t]:
                                    if f"{attr_name}__" in a:
                                        split_parts.append(a)
                            select_clause.extend([f"{t} AS {t}" for t in split_parts])
                    elif attribute.get("is_multivalued", False):
                        if attribute.get("is_in_separate_table", False):
                            attribute_node = graph.get_node_by_name(attribute.get("unique_name", None))
                            assert attribute_node
                            with_table_name = attribute_node.entity.unique_name + "_" + attribute_node.name
                            mvd_with_clause_str = ""
                            mvd_select_clause = []
                            mvd_from_clause = []
                            mvd_where_clause = []
                            mvd_group_by_clause = []
                            if attribute_node.unique_name not in tables_in_with_clause:
                                generate_with_clause_for_mvd_table(attribute_node, tables, types, graph, mvd_select_clause, mvd_from_clause, mvd_where_clause, mvd_group_by_clause)
                                mvd_select_clause_str = ", ".join(mvd_select_clause)
                                mvd_from_clause_str = ", ".join(mvd_from_clause)
                                mvd_where_clause_str = " AND ".join(mvd_where_clause)
                                mvd_group_by_clause_str = ", ".join(mvd_group_by_clause)
                                mvd_with_clause_str += (f"{with_table_name} AS (SELECT {mvd_select_clause_str} FROM {mvd_from_clause_str} WHERE {mvd_where_clause_str} "
                                                            f"GROUP BY {mvd_group_by_clause_str})")
                                with_clause.append(mvd_with_clause_str)
                                tables_in_with_clause.append(attribute_node.unique_name)
                            select_clause.append(f"COALESCE({with_table_name + table_attribute_specifier}.{attribute_node.name}, ARRAY[]::text[]) "
                                                 f"AS {attribute_specifier + attribute_node.name}")
                        else:
                            select_clause.append(f"{found_table_name + table_attribute_specifier}.{attr_name} AS {attribute_specifier + attr_name}")
                    else:
                        select_clause.append(f"{found_table_name + table_attribute_specifier}.{attr_name} AS {attribute_specifier + attr_name}")


        #first from node itself
        table_attribute_specifier = ""
        for node_name in attribute_node_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.unique_name]:
            select_all_node = graph.get_node_by_name(node_name)
            add_attributes_helper(entity_or_relationship_node, select_all_node, node_relevant_table_attribute_lists,
                                  table_attribute_specifier, with_clause, select_clause, where_clause)

        #entity1
        table_attribute_specifier = entity1_specifier
        for node_name in attribute_node_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.entity1.unique_name]:
            select_all_node = graph.get_node_by_name(node_name)
            add_attributes_helper(entity_or_relationship_node, select_all_node, entity1_relevant_table_attribute_lists,
                                  table_attribute_specifier, with_clause, select_clause, where_clause)

        #entity2
        table_attribute_specifier = entity2_specifier
        for node_name in attribute_node_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.entity2.unique_name]:
            select_all_node = graph.get_node_by_name(node_name)
            add_attributes_helper(entity_or_relationship_node, select_all_node, entity2_relevant_table_attribute_lists,
                                  table_attribute_specifier, with_clause, select_clause, where_clause)

        with_clause_without_with = ", ".join(with_clause)
        with_clause_str = ""
        if len(with_clause) > 0:
            with_clause_str += "WITH "
        with_clause_str += with_clause_without_with
        select_clause_str = ", ".join(select_clause)
        from_clause_str = ", ".join(from_clause)
        join_clause_str = " ".join(join_clause)
        left_join_clause_str = " ".join(left_join_clause)
        where_clause_str = " AND ".join(where_clause)
        # check if group by is needed
        if "AGG" in select_clause_str:#the group by clause is modified to include all attributes(except AGG attributes) to do the group by - each tuple grouped by all attributes
            group_by_clause = [c.split()[0] for c in select_clause if "AGG" not in c]#group by all attributes except attributes with 'AGG' in tuple
            group_by_clause_str = ", ".join(group_by_clause)

        select_all_clause = ""
        if with_clause:
            select_all_clause += f"{with_clause_str} "
        select_all_clause += f"SELECT {select_clause_str} FROM {from_clause_str}"
        if join_clause:
            select_all_clause += f" {join_clause_str}"
        if left_join_clause:
            select_all_clause += f" {left_join_clause_str}"
        if where_clause:
            select_all_clause += f" WHERE {where_clause_str}"
        if group_by_clause:
            select_all_clause += f" GROUP BY {group_by_clause_str}"
        memoized_select_all_queries[entity_or_relationship_node.unique_name] = select_all_clause

        return select_all_clause

def generate_select_query_for_relationship(entity_or_relationship_node, tables, types, graph):
    relevant_tables = []
    created_tables_by_names = {table[0]:table for table in tables}
    for sort_key, select_table in entity_or_relationship_node.select_all_tables:
        if select_table in created_tables_by_names:#if table is an actual physical table created in db
            relevant_tables.append(created_tables_by_names[select_table])
        else:#table view coming from a node distributed in node_cover - this view is not an actual physical table - a view generated from node_cover for full information
            table_node = graph.get_node_by_sort_key(sort_key)
            assert table_node.is_entity() and len(table_node.node_cover)>1
            assert select_table == "temp_" + table_node.unique_name
            #mapped table of a node distributed in node_cover contains only a subset of all relevant tuples, however for the purpose of defining the attribute list for view, can use that table
            new_table_info = [select_table] + created_tables_by_names[table_node.mapped_table[1]][1:]#view has the same attribute list from mapped table
            relevant_tables.append(new_table_info)

    relevant_tables_keys_names_sorted = sorted(list(entity_or_relationship_node.select_all_tables), key=lambda x: x[0])
    relevant_table_attribute_lists = {}
    for table in relevant_tables:
        table_tuple = next((t for t in relevant_tables_keys_names_sorted if t[1] == table[0]), None)
        relevant_table_attribute_lists[table_tuple] = [attribute_info[0] for attribute_info in table[1]]

    if entity_or_relationship_node.mapped_table:#e.g. query is SELECT * from Person; but Person may not have a table - in that scenario, need to union all children
        with_clause = []
        select_clause = []
        from_clause = []
        join_clause = []
        left_join_clause = []
        where_clause = []
        group_by_clause = []

        tables_in_with_clause = []#to avoid duplicating same table view(If participating entity of a recursive relationship is distributed in node_cover)
        # or mvd table - e.g. If product has mvd table mv_attribute, and if a relationship is between phone(subclass of product)
        #and smart_watch(subclass of product) with clause for mv_attribute should be only added once

        #entity_relationship_node
        node_table_list = table_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.unique_name]
        node_table_list_sorted_reverse = sorted(node_table_list, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table
        node_relevant_table_attribute_lists = {}
        for table_tuple in node_table_list:
            assert table_tuple in relevant_table_attribute_lists
            node_relevant_table_attribute_lists[table_tuple] = relevant_table_attribute_lists[table_tuple]

        #entity1 side
        entity1_side_table_list = table_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.entity1.unique_name]
        entity1_side_table_list_sorted_reverse = sorted(entity1_side_table_list, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table
        if len(entity_or_relationship_node.entity1.node_cover)<=1:#entity1 is not distributed in a node_cover
            entity1_relevant_table_attribute_lists = {}
            for table_tuple in entity1_side_table_list:
                assert table_tuple in relevant_table_attribute_lists
                entity1_relevant_table_attribute_lists[table_tuple] = relevant_table_attribute_lists[table_tuple]
        else:#if entity1 is distributed in node_cover, no need to define a table list to cover entity1 attributes, since all attributes will be covered from built view
            entity1_relevant_table_attribute_lists = {}

        #entity2 side
        entity2_side_table_list = table_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.entity2.unique_name]
        entity2_side_table_list_sorted_reverse = sorted(entity2_side_table_list, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table
        if len(entity_or_relationship_node.entity2.node_cover)<=1:#entity2 is not distributed in node_cover
            entity2_relevant_table_attribute_lists = {}
            for table_tuple in entity2_side_table_list:
                assert table_tuple in relevant_table_attribute_lists
                entity2_relevant_table_attribute_lists[table_tuple] = relevant_table_attribute_lists[table_tuple]
        else:#if entity2 is distributed in node_cover, no need to define a table list to cover entity2 attributes, since all attributes will be covered from built view
            entity2_relevant_table_attribute_lists = {}


        if check_if_relationship_is_1_N(entity_or_relationship_node):
            many_side_entity = entity_or_relationship_node.entity2 if entity_or_relationship_node.rel_dict['entity1']['one'] and not entity_or_relationship_node.rel_dict['entity2']['one'] \
                else entity_or_relationship_node.entity1
            if entity_or_relationship_node.mapped_table == many_side_entity.mapped_table:#relationship is folded
                if many_side_entity.unique_name == entity_or_relationship_node.entity2.unique_name:
                    entity2_specifier = ""                               #no need of specifier for table of entity2 since both entity2 and relationship in same table
                    entity1_specifier = "_" + entity_or_relationship_node.entity1.unique_name
                else:
                    assert many_side_entity.unique_name == entity_or_relationship_node.entity1.unique_name
                    entity1_specifier = ""                               #no need of specifier for table of entity1 since both entity1 and relationship in same table
                    entity2_specifier = "_" + entity_or_relationship_node.entity2.unique_name
            else:#1:M relationship is not folded
                entity1_specifier = "_" + entity_or_relationship_node.entity1.unique_name
                entity2_specifier = "_" + entity_or_relationship_node.entity2.unique_name
        else:#M:N
            entity1_specifier = "_" + entity_or_relationship_node.entity1.unique_name
            entity2_specifier = "_" + entity_or_relationship_node.entity2.unique_name

        #set entity_or_relationship node mapped_table - except for folded relationship with many side distributed in node_cover, all others are simply node.mapped_table
        mapped_table = get_mapped_table_for_entity_or_relationship(graph, entity_or_relationship_node)#(sort_key, mapped_table)

        from_clause.append(mapped_table[1])
        tables_sorted_reverse = sorted(relevant_tables_keys_names_sorted, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table
        if (len(tables_sorted_reverse)>1 or
                ((entity_or_relationship_node.mapped_table == entity_or_relationship_node.entity1.mapped_table == entity_or_relationship_node.entity2.mapped_table)
                if check_if_relationship_is_1_N(entity_or_relationship_node) else False)):#one possible scenario - relationship is 1:N and it is folded to many side, both participating
            #entities belong to a hierarchy and folded in parent
            #then len(tables_sorted_reverse) is 1 - but still a join clause need to be added for 1 side

            def join_tables_helper(relationship_or_participating_entity, node, entity_side_table_list_sorted_reverse, node_specifier, entity_specifier, join_clause, left_join_clause):
                entity_side_entity_unique_name = entity_specifier[1:]

                if not node.is_attribute():

                    #participating entity
                    if (relationship_or_participating_entity.is_entity() and relationship_or_participating_entity.is_subclass and
                            len(relationship_or_participating_entity.node_cover)==1 and
                            (relationship_or_participating_entity.is_contained_in_parent or relationship_or_participating_entity.is_partially_by_itself)):
                        #If participating entity node is a subclass with node cover 1, participating entity node's mapped_table contains all tuples - may not cover attribute set for tuples
                        #The joins can be happening with node itself, mvd attributes, and top parents to gain attribute cover.
                        #If the joining table node is not an attribute, node can be the entity node itself, or any top parent.
                        #These top parents may have a node cover. But if the participating entity node's node cover is 1, all required tuples(in full/sub set of attributes)
                        #are already in participating entity node's mapped table
                        #Participating entity node only need top parents' original mapped tables to generate full attribute cover since all inserts relevant to
                        #participating entity node will be in the top parent's original mapped table - no need to gather all tuples of top parents from views.
                        #Hence it is correct to map node_mapped_table to node.mapped_table for all nodes corresponding to joining tables
                        #parent being distributed in a node cover doesn't affect to gain attribute cover for a subclass node with no node cover
                        node_mapped_table = node.mapped_table
                    elif relationship_or_participating_entity.is_entity() and relationship_or_participating_entity.is_weak_entity:
                        depending_entities = relationship_or_participating_entity.select_all_nodes
                        strong_parent_entity = graph.get_node_by_name(depending_entities[-1])#only 1 strong parent exists in depending entities - last in the list
                        assert strong_parent_entity.is_entity() and not strong_parent_entity.is_weak_entity
                        if (strong_parent_entity.is_subclass and len(strong_parent_entity.node_cover)==1 and
                                (strong_parent_entity.is_partially_by_itself or strong_parent_entity.is_contained_in_parent)):
                            #if participating entity is a weak entity whose strong parent is a subclass with node cover 1 and is partial/contained
                            #need to use node.mapped_table all nodes relevant to joining_tables
                            #non-attribute nodes coming from participating entity could other parent depending weak entities,
                            #strong parent entity, and its parents if strong parent is partial/contained
                            #for all those nodes, correct to use - node.mapped_table
                            node_mapped_table = node.mapped_table
                        else:#for all other scenarios, mapped_table is retrieved from the function
                            node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, node)
                    else:#for all other scenarios, mapped_table is retrieved from the function
                        node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, node)
                    assert node_mapped_table in relevant_tables_keys_names_sorted

                    if node.key.reference_table is not None:
                        if node.key.table_key and isinstance(node.key.table_key[0], tuple):#strong entity, strong subclass entity
                            node_join_clause = []
                            assert len(node.key.table_key) == 1
                            for i in range(len(node.key.table_key)):
                                if node.key.reference_table[i] in [t[1] for t in entity_side_table_list_sorted_reverse]:
                                    if (node_mapped_table[1] != node.key.reference_table[i]) and (node.mapped_table[1] != node.key.reference_table[i]):
                                        node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][0]} {"="} "
                                                                f"{node.key.reference_table[i] + entity_specifier}.{node.key.reference_key[i][0]}")
                            node_join_clause_str = " AND ".join(node_join_clause)
                            assert len(node.key.reference_table) == 1
                            if node_join_clause_str:
                                join_clause.append(f"JOIN {node.key.reference_table[0]} AS {node.key.reference_table[0] + entity_specifier} ON " + node_join_clause_str)
                        elif node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple):#weak entity, relationship
                            assert len(node.key.table_key) == 2
                            for i in range(len(node.key.table_key)):
                                #for weak entity len(node.key.reference_table) is 1 and for relationship it is 2
                                #only for i=0(parent key), following condition is executed for weak entity,
                                if len(node.key.reference_table) >= i+1:#for weak entity reference table added for parent only, for relationship ref table added for each participating entity
                                    reference_entity = graph.get_node_by_name(node.key.table_key_entities[i][0])#pk_entity = [[], []]
                                    reference_entity_full_view = "temp_" + reference_entity.unique_name
                                    #a join condition exists - if reference table exists entity_side_table_list_sorted_reverse
                                    #but if reference_entity is distributed in its node_cover, only its full table view exists in entity_side_table_list_sorted_reverse, but node.key.reference_table[i] is
                                    #still referencing reference_entity's original mapped table(with tuples only from itself), not table view, hence that check has to be done explicitly
                                    if ((node.key.reference_table[i] in [t[1] for t in entity_side_table_list_sorted_reverse]) or
                                            (reference_entity_full_view in [t[1] for t in entity_side_table_list_sorted_reverse])):
                                        #since node key's reference table stil points to original node.mapped_table, checking for only node_mapped_table[1] != node.key.reference_table[i]
                                        #will be always true if node_mapped_table is set to a table view(folded cases). Hence need to explicitly check for node.mapped_table[1] != node.key.reference_table[i]
                                        if (node_mapped_table[1] != node.key.reference_table[i]) and (node.mapped_table[1] != node.key.reference_table[i]):
                                            #format for table_key_entities is [[],[]]
                                            if node.is_relationship():
                                                if node.key.table_key_entities[i][0] == entity_side_entity_unique_name:#required for relationship node
                                                    #e.g. bundled_phone_smart_watch - phone and smart_watch both contained_in_parent 'product'
                                                    #when joining bundled_phone_smart_watch(table_0) with phone(product table_1), for pks coming from both phone, and smart_watch,
                                                    #node.key.reference_table[i] in [t[1] for t in entity_side_table_list_sorted_reverse] sets true. Need to explicitly filter key for relevant entity.
                                                    node_join_clause = []
                                                    if reference_entity.is_entity() and len(reference_entity.node_cover)>1:
                                                        #if entity from which the reference table comes from is distributed in its node_cover
                                                        #full table representation view is named "temp_"+node.unique_name for the node
                                                        reference_table_name = "temp_" + reference_entity.unique_name
                                                        for j in range(len(node.key.table_key[i])):
                                                            node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                                    f"{reference_table_name + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                        node_join_clause_str = " AND ".join(node_join_clause)
                                                        if node_join_clause_str:
                                                            join_clause.append(f"JOIN {reference_table_name} AS {reference_table_name + entity_specifier} ON " + node_join_clause_str)
                                                    else:
                                                        for j in range(len(node.key.table_key[i])):
                                                            node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                                    f"{node.key.reference_table[i] + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                        node_join_clause_str = " AND ".join(node_join_clause)
                                                        if node_join_clause_str:
                                                            join_clause.append(f"JOIN {node.key.reference_table[i]} AS {node.key.reference_table[i] + entity_specifier} ON "
                                                                               + node_join_clause_str)

                                            else:#no check required for weak entity
                                                node_join_clause = []
                                                if reference_entity.is_entity() and len(reference_entity.node_cover)>1:
                                                    #if entity from which the reference table comes from is distributed in its node_cover
                                                    #full table representation view is named "temp_"+node.unique_name for the node
                                                    reference_table_name = "temp_" + reference_entity.unique_name
                                                    for j in range(len(node.key.table_key[i])):
                                                        node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                                f"{reference_table_name + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                    node_join_clause_str = " AND ".join(node_join_clause)
                                                    if node_join_clause_str:
                                                        join_clause.append(f"JOIN {reference_table_name} AS {reference_table_name + entity_specifier} ON " + node_join_clause_str)
                                                else:
                                                    for j in range(len(node.key.table_key[i])):
                                                        node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                                f"{node.key.reference_table[i] + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                    node_join_clause_str = " AND ".join(node_join_clause)
                                                    if node_join_clause_str:
                                                        join_clause.append(f"JOIN {node.key.reference_table[i]} AS {node.key.reference_table[i] + entity_specifier} ON "
                                                                       + node_join_clause_str)

                                        else:
                                            #required when both participating entities in same table(happens with contained in parent nodes in hierarchy) and
                                            # relationship also folded in table.
                                            #e.g. phone and smart_watch both contained in parent and bundled_phone_smart_watch folded into many side
                                            if node.is_relationship():
                                                if (node.entity1.mapped_table == node.entity2.mapped_table == node.mapped_table):
                                                    assert check_if_relationship_is_1_N(node)#has to be 1:N relationship
                                                    many_side_entity = node.entity2 if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one'] else node.entity1
                                                    if many_side_entity.unique_name == node.entity1.unique_name:#relationship folded in entity1 - 1 side is entity2
                                                        if node.entity2.unique_name == entity_side_entity_unique_name:#Need to explicitly filter key for relevant entity.
                                                            if node.key.table_key_entities[i][0] == entity_side_entity_unique_name:
                                                                node_join_clause = []
                                                                if reference_entity.is_entity() and len(reference_entity.node_cover)>1:
                                                                    #if entity from which the reference table comes from is distributed in its node_cover
                                                                    #full table representation view is named "temp_"+node.unique_name for the node
                                                                    reference_table_name = "temp_" + reference_entity.unique_name
                                                                    for j in range(len(node.key.table_key[i])):
                                                                        node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                                                f"{reference_table_name + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                                    node_join_clause_str = " AND ".join(node_join_clause)
                                                                    if node_join_clause_str:
                                                                        join_clause.append(f"JOIN {reference_table_name} AS {reference_table_name + entity_specifier} ON "
                                                                                           + node_join_clause_str)
                                                                else:
                                                                    for j in range(len(node.key.table_key[i])):
                                                                        node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                                                f"{node.key.reference_table[i] + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                                    node_join_clause_str = " AND ".join(node_join_clause)
                                                                    if node_join_clause_str:
                                                                        join_clause.append(f"JOIN {node.key.reference_table[i]} AS {node.key.reference_table[i] + entity_specifier} ON "
                                                                                           + node_join_clause_str)
                                                    else:
                                                        assert many_side_entity.unique_name == node.entity2.unique_name#relationship folded in entity2 - 1 side is entity1
                                                        if node.entity1.unique_name == entity_side_entity_unique_name:#Need to explicitly filter key for relevant entity.
                                                            if node.key.table_key_entities[i][0] == entity_side_entity_unique_name:
                                                                node_join_clause = []
                                                                if reference_entity.is_entity() and len(reference_entity.node_cover)>1:
                                                                    #if entity from which the reference table comes from is distributed in its node_cover
                                                                    #full table representation view is named "temp_"+node.unique_name for the node
                                                                    reference_table_name = "temp_" + reference_entity.unique_name
                                                                    for j in range(len(node.key.table_key[i])):
                                                                        node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                                                f"{reference_table_name + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                                    node_join_clause_str = " AND ".join(node_join_clause)
                                                                    if node_join_clause_str:
                                                                        join_clause.append(f"JOIN {reference_table_name} AS {reference_table_name + entity_specifier} ON "
                                                                                           + node_join_clause_str)
                                                                else:
                                                                    for j in range(len(node.key.table_key[i])):
                                                                        node_join_clause.append(f"{node_mapped_table[1] + node_specifier}.{node.key.table_key[i][j][0]} {"="} "
                                                                                                f"{node.key.reference_table[i] + entity_specifier}.{node.key.reference_key[i][j][0]}")
                                                                    node_join_clause_str = " AND ".join(node_join_clause)
                                                                    if node_join_clause_str:
                                                                        join_clause.append(f"JOIN {node.key.reference_table[i]} AS {node.key.reference_table[i] + entity_specifier} ON "
                                                                                           + node_join_clause_str)


            #first start from node itself
            for joining_table in node_table_list_sorted_reverse:
                node = graph.get_node_by_sort_key(joining_table[0])
                node_specifier = ""
                if not node.is_attribute():
                    #if a relationship folded to many side which is distributed in its node_cover, node's new mapped table is full table view of many side. Hence entity_or_relationship_node.mapped_table
                    #is not equal to joining_table which is the full table view of entity where full folded relationship is present
                    assert (entity_or_relationship_node.mapped_table == joining_table or
                            (len(entity_or_relationship_node.entity1.node_cover)>1 or len(entity_or_relationship_node.entity2.node_cover)>1))
                    join_tables_helper(entity_or_relationship_node, entity_or_relationship_node, entity1_side_table_list_sorted_reverse, node_specifier, entity1_specifier, join_clause, left_join_clause)#relationship node joining entity1
                    join_tables_helper(entity_or_relationship_node, entity_or_relationship_node, entity2_side_table_list_sorted_reverse, node_specifier, entity2_specifier, join_clause, left_join_clause)#relationship node joining entity2
                else:#mvd in separate table
                    assert node.is_multivalued
                    assert node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple)
                    with_table_name = node.entity.unique_name + "_" + node.name
                    left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                            f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                            f"{node.key.reference_table[0] + node_specifier}.{node.key.reference_key[0][0][0]}")

            #entity_1 joining tables
            for joining_table in entity1_side_table_list_sorted_reverse:
                node = graph.get_node_by_sort_key(joining_table[0])
                node_specifier = entity1_specifier
                if not node.is_attribute():
                    join_tables_helper(entity_or_relationship_node.entity1, node, entity1_side_table_list_sorted_reverse, node_specifier, entity1_specifier, join_clause, left_join_clause)
                else:#mvd in separate table
                    assert node.is_multivalued
                    assert node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple)
                    with_table_name = node.entity.unique_name + "_" + node.name
                    if node.entity.unique_name == entity_or_relationship_node.entity1.unique_name:#mvd in separate table coming from node itself
                        left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                f"{node.key.reference_table[0] + node_specifier}.{node.key.reference_key[0][0][0]}")
                    else:#mvd in separate table coming from a differnt node - not node itself
                        if node.entity.is_weak_entity or (not node.entity.is_subclass and not len(node.entity.children)>0):#mvd coming from (weak entity) or (non-subclass non-root strong entity) - pks/joining reference table no change for mvd table
                            left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                    f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{node.key.reference_table[0] + node_specifier}.{node.key.reference_key[0][0][0]}")
                        else:##mvd coming from subclass or root strong entity - pks/joining reference table can change for mvd tables
                            #mvd from a subclass/root - pk in mvd table may not match subclass pk - e.g. mv_person table has person_id, and student has student_id
                            #mvd table's joining reference table also should be changed to student
                            #e.g. LEFT JOIN person_mv on person_mv.person_id = person.person_id -> LEFT JOIN person_mv on person_mv.person_id = student.student_id (if student on separate table)
                            #since mvd's entity belongs to a hierarchy - # of pks of the entity should be 1 - subclass/root is a strong entity
                            lowest_level_subclass_or_root_name = get_lowest_level_subclass_or_root_in_select_all_nodes_for_entity(graph, entity_or_relationship_node.entity1)
                            assert lowest_level_subclass_or_root_name
                            lowest_level_subclass = graph.get_node_by_name(lowest_level_subclass_or_root_name)
                            entity_table_to_join_with_mvd_table = lowest_level_subclass.mapped_table[1]
                            pk_of_entity_table_to_join_with_mvd_table = lowest_level_subclass.key.table_key[0][0]
                            left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                    f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{entity_table_to_join_with_mvd_table + node_specifier}.{pk_of_entity_table_to_join_with_mvd_table}")


            #entity_2 joining tables
            for joining_table in entity2_side_table_list_sorted_reverse:
                node = graph.get_node_by_sort_key(joining_table[0])
                node_specifier = entity2_specifier
                if not node.is_attribute():
                    join_tables_helper(entity_or_relationship_node.entity2, node, entity2_side_table_list_sorted_reverse, node_specifier, entity2_specifier, join_clause, left_join_clause)
                else:#mvd in separate table
                    assert node.is_multivalued
                    assert node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple)
                    with_table_name = node.entity.unique_name + "_" + node.name
                    if node.entity.unique_name == entity_or_relationship_node.entity2.unique_name:#mvd in separate table coming from node itself
                        left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                f"{node.key.reference_table[0] + node_specifier}.{node.key.reference_key[0][0][0]}")
                    else:#mvd in separate table coming from a differnt node - not node itself
                        if node.entity.is_weak_entity or (not node.entity.is_subclass and not len(node.entity.children)>0):#mvd coming from (weak entity) or (non-subclass non-root strong entity) - pks/joining reference table no change for mvd table
                            left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                    f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{node.key.reference_table[0] + node_specifier}.{node.key.reference_key[0][0][0]}")
                        else:##mvd coming from subclass or root strong entity - pks/joining reference table can change for mvd tables
                            #mvd from a subclass/root - pk in mvd table may not match subclass pk - e.g. mv_person table has person_id, and student has student_id
                            #mvd table's joining reference table also should be changed to student
                            #e.g. LEFT JOIN person_mv on person_mv.person_id = person.person_id -> LEFT JOIN person_mv on person_mv.person_id = student.student_id (if student on separate table)
                            #since mvd's entity belongs to a hierarchy - # of pks of the entity should be 1 - subclass/root is a strong entity
                            lowest_level_subclass_or_root_name = get_lowest_level_subclass_or_root_in_select_all_nodes_for_entity(graph, entity_or_relationship_node.entity2)
                            assert lowest_level_subclass_or_root_name
                            lowest_level_subclass = graph.get_node_by_name(lowest_level_subclass_or_root_name)
                            entity_table_to_join_with_mvd_table = lowest_level_subclass.mapped_table[1]
                            pk_of_entity_table_to_join_with_mvd_table = lowest_level_subclass.key.table_key[0][0]# no of pks is 1
                            left_join_clause.append(f"LEFT JOIN {with_table_name} AS {with_table_name + node_specifier} ON "
                                                    f"{with_table_name + node_specifier}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{entity_table_to_join_with_mvd_table + node_specifier}.{pk_of_entity_table_to_join_with_mvd_table}")

        #adding attributes
        def add_attributes_helper(entity_or_relationship_node, select_all_node, table_tuples_with_relevant_attribute_lists,
                                  table_attribute_specifier, with_clause, select_clause, where_clause):

            if table_attribute_specifier == "":
                attribute_specifier = ""
            else:
                attribute_specifier = table_attribute_specifier[1:] + "_"#get underscore to back from front

            if select_all_node.is_entity() and len(select_all_node.node_cover)>1:#can be a subclass or root in hierarchy
                temp_view_name = select_all_node.unique_name + "_" + entity_or_relationship_node.unique_name
                if temp_view_name not in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover:
                    generated_view = generate_temp_view_with_clause_for_entity_with_node_cover(select_all_node, entity_or_relationship_node, tables, types, graph)
                    assert generated_view == temp_view_name
                for with_temp_table_dict in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[temp_view_name]:
                    for with_temp_table_name, with_temp_table_clause in with_temp_table_dict.items():
                        if with_temp_table_name not in tables_in_with_clause:
                            with_clause.append(with_temp_table_clause)#append the temp table view(including mvd tables) with full table construction for node
                            tables_in_with_clause.append(with_temp_table_name)

            select_all_node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, select_all_node)

            #if the folded relationship doesn't have total participation for many side - need to filter many side tuples based on if one side value is not null
            if select_all_node.is_relationship():
                assert entity_or_relationship_node.unique_name == select_all_node.unique_name
                #alternative way to check if relationship is folded to many side
                """
                if check_if_relationship_is_1_N(select_all_node):
                    many_side_entity = select_all_node.entity2 if select_all_node.rel_dict['entity1']['one'] and not select_all_node.rel_dict['entity2']['one'] \
                                                            else select_all_node.entity1
                    if select_all_node.mapped_table == many_side_entity.mapped_table:#relationship is folded
                        one_side_attribute = select_all_node.key.table_key[1][0][0]
                        where_clause.append(f"{select_all_node_mapped_table[1] + table_attribute_specifier}.{one_side_attribute} IS NOT NULL")
                """
                if graph.config[select_all_node.unique_name] == "folded_to_many_side":
                    one_side_attribute = select_all_node.key.table_key[1][0][0]
                    where_clause.append(f"{select_all_node_mapped_table[1] + table_attribute_specifier}.{one_side_attribute} IS NOT NULL")

            #for an entity which belongs to a hierarchy, and contained in parent, need to consider each child by role type to get all tuples for entity
            #e.g. hierarchy Person -> Customer(20 tuples) -> Prime Customer(30) -> Family prime(10)
            #Customer, Prime Customer in same relation_1(Person table), Family prime all by itself in relation_2
            #Person - all by itself, Customer - contained in parent, Prime Customer - contained in parent, Family prime - all by itself
            #1. 20 entries with role_type 'customer' and 30 with 'primecustomer' and 10 with role_type 'familyprime' in relation_1
            #2. 10 entries in relation_2
            #e.g. If Family Prime is partially_by_itself or all_by_itself - all tuples of Family Prime
            #has a corresponding tuple in Person table - so select * from Customer == select * from relation_1 where role in ('customer','primecustomer', 'familyprime')
            #select * from primecustomer == select * from relation_1 where role in ('primecustomer', 'familyprime')
            #select * from familyprime == select * from relation_2
            #select * from person == select * from relation_1 - no need to filter by role
            #in hierarchy, if atleast one child of node is contained_in_parent - then node has role column, with each tuple identified by child name
            #in this example in relation_1 - 20 entries with role_type 'customer' and 30 with 'primecustomer' and 10 with role_type 'familyprime' in relation_1
            if select_all_node.is_entity() and select_all_node.is_subclass and select_all_node.is_contained_in_parent and len(select_all_node.node_cover)<=1:
                #only if contained_in_parent select_all_node doesn't have a view, add this - otherwise view has already filtered the tuples for select_all_node
                if len(select_all_node.children)>0:#entity_or_relationship_node can be any sub parent which is contained in parent
                    assert "role" in table_tuples_with_relevant_attribute_lists[select_all_node_mapped_table]
                    # collect entity names (entity + contained children)
                    all_entities = {select_all_node.unique_name}#add entity itself
                    #add all children rooted at node
                    find_all_children_rooted_at_node(select_all_node, all_entities)
                    all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                    where_clause.append(f"{select_all_node_mapped_table[1] + table_attribute_specifier}.{"role"} {"IN"} ({all_entities_str})")
                else:#entity itself - where clause would be just role in (entity_name)
                    #for leaf subclass contained in parent
                    assert "role" in table_tuples_with_relevant_attribute_lists[select_all_node_mapped_table]
                    where_clause.append(f"{select_all_node_mapped_table[1] + table_attribute_specifier}.{"role"} {"IN"} ('{select_all_node.unique_name}')")

            #for a node distributed in node_cover - full table view is already built in with clause temp table
            #all attributes for the node are in the temp table - even all the mvd attributes coming from separate tables are aggregated and folded
            #hence temp table view is sufficient and complete to get all attributes
            if select_all_node.is_entity() and len(select_all_node.node_cover)>1:#can be a root or subclass in hierarchy
                for attribute in select_all_node.attribute_list:
                    if select_all_node.unique_name != entity_or_relationship_node.unique_name:
                        if "pk_name" in attribute:#from other nodes need only non-pk attributes since pks are already coming from entity_relationship node itself
                            continue#avoid executing rest of the body in the loop
                    attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                    found_table_name = "temp_" + select_all_node.unique_name#full table representation view is named "temp_"+node.unique_name for nodes with node_cover
                    assert found_table_name==select_all_node_mapped_table[1]
                    select_clause.append(f"{found_table_name + table_attribute_specifier}.{attr_name} AS {attribute_specifier + attr_name}")

            else:#node is not distributed in a node_cover - no view is built - need to build the attribute list - might be coming from different tables
                for attribute in select_all_node.attribute_list:
                    if select_all_node.unique_name != entity_or_relationship_node.unique_name:
                        if "pk_name" in attribute:#from other nodes need only non-pk attributes since pks are already coming from entity_relationship node itself
                            continue#avoid executing rest of the body in the loop
                    attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                    if "pk_name" in attribute:
                        found = select_all_node_mapped_table
                        found_table_name = found[1] if found else None
                    elif "name" in attribute:#non pk attributes may come from node mapped table or other table - e.g. parent attributes of subclass, mvd in separate table
                        found = [table_tuple for table_tuple in table_tuples_with_relevant_attribute_lists if attr_name in
                                 table_tuples_with_relevant_attribute_lists[table_tuple]]
                        found_table_name = found[0][1] if found else None
                    if attribute["pk_type" if "pk_type" in attribute else "type"] == 'COMPOSITE':
                        if found:
                            # not split up
                            select_clause.append(f"{found_table_name + table_attribute_specifier}.{attr_name} AS {attribute_specifier + attr_name}")
                        else:
                            # look for attr_name__ in the attribute lists
                            split_parts = []
                            for t in table_tuples_with_relevant_attribute_lists:
                                for a in table_tuples_with_relevant_attribute_lists[t]:
                                    if f"{attr_name}__" in a:
                                        split_parts.append(a)
                            select_clause.extend([f"{t} AS {t}" for t in split_parts])
                    elif attribute.get("is_multivalued", False):
                        if attribute.get("is_in_separate_table", False):
                            attribute_node = graph.get_node_by_name(attribute.get("unique_name", None))
                            assert attribute_node
                            with_table_name = attribute_node.entity.unique_name + "_" + attribute_node.name
                            mvd_with_clause_str = ""
                            mvd_select_clause = []
                            mvd_from_clause = []
                            mvd_where_clause = []
                            mvd_group_by_clause = []
                            if attribute_node.unique_name not in tables_in_with_clause:
                                generate_with_clause_for_mvd_table(attribute_node, tables, types, graph, mvd_select_clause, mvd_from_clause, mvd_where_clause, mvd_group_by_clause)
                                mvd_select_clause_str = ", ".join(mvd_select_clause)
                                mvd_from_clause_str = ", ".join(mvd_from_clause)
                                mvd_where_clause_str = " AND ".join(mvd_where_clause)
                                mvd_group_by_clause_str = ", ".join(mvd_group_by_clause)
                                mvd_with_clause_str += (f"{with_table_name} AS (SELECT {mvd_select_clause_str} FROM {mvd_from_clause_str} WHERE {mvd_where_clause_str} "
                                                            f"GROUP BY {mvd_group_by_clause_str})")
                                with_clause.append(mvd_with_clause_str)
                                tables_in_with_clause.append(attribute_node.unique_name)
                            select_clause.append(f"COALESCE({with_table_name + table_attribute_specifier}.{attribute_node.name}, ARRAY[]::text[]) "
                                                 f"AS {attribute_specifier + attribute_node.name}")
                        else:
                            select_clause.append(f"{found_table_name + table_attribute_specifier}.{attr_name} AS {attribute_specifier + attr_name}")
                    else:
                        select_clause.append(f"{found_table_name + table_attribute_specifier}.{attr_name} AS {attribute_specifier + attr_name}")


        #first from node itself
        table_attribute_specifier = ""
        for node_name in attribute_node_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.unique_name]:
            select_all_node = graph.get_node_by_name(node_name)
            add_attributes_helper(entity_or_relationship_node, select_all_node, node_relevant_table_attribute_lists,
                                  table_attribute_specifier, with_clause, select_clause, where_clause)

        #entity1
        table_attribute_specifier = entity1_specifier
        for node_name in attribute_node_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.entity1.unique_name]:
            select_all_node = graph.get_node_by_name(node_name)
            add_attributes_helper(entity_or_relationship_node, select_all_node, entity1_relevant_table_attribute_lists,
                                  table_attribute_specifier, with_clause, select_clause, where_clause)

        #entity2
        table_attribute_specifier = entity2_specifier
        for node_name in attribute_node_cover[entity_or_relationship_node.unique_name][entity_or_relationship_node.entity2.unique_name]:
            select_all_node = graph.get_node_by_name(node_name)
            add_attributes_helper(entity_or_relationship_node, select_all_node, entity2_relevant_table_attribute_lists,
                                  table_attribute_specifier, with_clause, select_clause, where_clause)

        with_clause_without_with = ", ".join(with_clause)
        with_clause_str = ""
        if len(with_clause) > 0:
            with_clause_str += "WITH "
        with_clause_str += with_clause_without_with
        select_clause_str = ", ".join(select_clause)
        from_clause_str = ", ".join(from_clause)
        join_clause_str = " ".join(join_clause)
        left_join_clause_str = " ".join(left_join_clause)
        where_clause_str = " AND ".join(where_clause)
        # check if group by is needed
        if "AGG" in select_clause_str:#the group by clause is modified to include all attributes(except AGG attributes) to do the group by - each tuple grouped by all attributes
            group_by_clause = [c.split()[0] for c in select_clause if "AGG" not in c]#group by all attributes except attributes with 'AGG' in tuple
            group_by_clause_str = ", ".join(group_by_clause)

        select_all_clause = ""
        if with_clause:
            select_all_clause += f"{with_clause_str} "
        select_all_clause += f"SELECT {select_clause_str} FROM {from_clause_str}"
        if join_clause:
            select_all_clause += f" {join_clause_str}"
        if left_join_clause:
            select_all_clause += f" {left_join_clause_str}"
        if where_clause:
            select_all_clause += f" WHERE {where_clause_str}"
        if group_by_clause:
            select_all_clause += f" GROUP BY {group_by_clause_str}"
        memoized_select_all_queries[entity_or_relationship_node.unique_name] = select_all_clause

        return select_all_clause

#generate select query for entity with all relevant tuples contained in its_mapped_table
#strong entity not belonging to a hierarchy - all by itself option
#weak entity with all by itself option
#root or a subclass in hierarchy with contained_all_descendants
#leaf nodes in hierarchy with all by itself
#or nodes in hierarchy with len(node.cover)==1 <- these nodes could be contained/partial/all
def generate_select_query_for_entity_with_no_node_cover(entity_or_relationship_node, tables, types, graph):
    assert len(entity_or_relationship_node.node_cover) <= 1#only node itself

    relevant_tables = []
    created_tables_by_names = {table[0]:table for table in tables}
    for sort_key, select_table in entity_or_relationship_node.select_all_tables:
        if select_table in created_tables_by_names:#if table is an actual physical table created in db
            relevant_tables.append(created_tables_by_names[select_table])
        else:#table view coming from a node distributed in node_cover - this view is not an actual physical table - a view generated from node_cover for full information
            #might require if entity node is a weak entity and depending strong parent is a node distributed in node cover
            assert entity_or_relationship_node.is_weak_entity#if entity node is a hierarchy node with no node cover - it doesn't require views from parent - parent's original mapped_table
                                                             #is sufficient to retrieve attribute cover if hierarchy node is contained/partial
            table_node = graph.get_node_by_sort_key(sort_key)
            assert table_node.is_entity() and len(table_node.node_cover)>1
            assert select_table == "temp_" + table_node.unique_name
            #mapped table of a node distributed in node_cover contains only a subset of all relevant tuples, however for the purpose of defining the attribute list for view, can use that table
            new_table_info = [select_table] + created_tables_by_names[table_node.mapped_table[1]][1:]#view has the same attribute list from mapped table
            relevant_tables.append(new_table_info)

    relevant_tables_keys_names_sorted = sorted(list(entity_or_relationship_node.select_all_tables), key=lambda x: x[0])
    relevant_table_attribute_lists = {}
    for table in relevant_tables:
        table_tuple = next((t for t in relevant_tables_keys_names_sorted if t[1] == table[0]), None)
        relevant_table_attribute_lists[table_tuple] = [attribute_info[0] for attribute_info in table[1]]

    if entity_or_relationship_node.mapped_table:#e.g. query is SELECT * from Person; but Person may not have a table - in that scenario, need to union all children
        with_clause = []
        select_clause = []
        from_clause = []
        join_clause = []
        left_join_clause = []
        where_clause = []
        group_by_clause = []

        mapped_table = get_mapped_table_for_entity_or_relationship(graph, entity_or_relationship_node)#(sort_key, mapped_table)
        #mapped_parent_node = graph.get_node_by_sort_key(mapped_parent_table[0])
        from_clause.append(mapped_table[1])
        #other_tables = [x for x in relevant_tables_keys_names_sorted if x != mapped_table]
        tables_sorted_reverse = sorted(relevant_tables_keys_names_sorted, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table
        if len(tables_sorted_reverse)>1:#if joins needed - add pk, fk join clauses
            for joining_table in tables_sorted_reverse:
                node = graph.get_node_by_sort_key(joining_table[0])
                if not node.is_attribute():

                    if entity_or_relationship_node.is_subclass:
                        #If entity node is a subclass, the joins can be happening with node itself, mvd attributes, and top parents to gain attribute cover.
                        #If the joining table node is not an attribute, node can be the entity node itself, or any top parent if entity node is partial/contained.
                        #Since entity node has no node cover, all required tuples for entity in full/sub set of attributes are in entity node's mapped table.
                        #To gain the attribute cover for entity node(if entity is partial/contained), only top parents' original mapped table is required.
                        #If a top parent distributed in a node cover exists, no need to create the view for parent since its original mapped table contain all tuple inserts
                        #from entity node and that is sufficient to create attribute cover
                        #No need to generate view with all tuples from parent
                        #parent being distributed in a node cover doesn't affect to gain tuple cover for a subclass node with no node cover
                        #for all nodes relevant to joining tables, it is correct to map node_mapped_table to node.mapped_table
                        node_mapped_table = node.mapped_table
                    elif entity_or_relationship_node.is_weak_entity:
                        depending_entities = entity_or_relationship_node.select_all_nodes
                        strong_parent_entity = graph.get_node_by_name(depending_entities[-1])#only 1 strong parent exists in depending entities - last in the list
                        assert strong_parent_entity.is_entity() and not strong_parent_entity.is_weak_entity
                        if (strong_parent_entity.is_subclass and len(strong_parent_entity.node_cover)==1 and
                            (strong_parent_entity.is_partially_by_itself or strong_parent_entity.is_contained_in_parent)):
                            #need to use node.mapped_table all nodes relevant to joining_tables
                            #nodes could other parent depending weak entities, strong parent entity, and its parents if strong parent is partial/contained
                            #for all those nodes, correct to use - node.mapped_table
                            node_mapped_table = node.mapped_table
                        else:
                            #if len(strong_parent_entity.node_cover)==1 and strong_parent_entity is contained_all_descendants/all - no joins with top parents -
                            #node is only itself and function gives node.mapped_table
                            #if len(strong_parent_entity.node_cover) > 1 - no joins with top parents -
                            #node is only itself and function gives node's view
                            node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, node)
                    else:
                        node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, node)

                    assert node_mapped_table in relevant_tables_keys_names_sorted

                    if node.key.reference_table is not None:
                        if node.key.table_key and isinstance(node.key.table_key[0], tuple):#strong entity, strong subclass entity
                            node_join_clause = []
                            assert len(node.key.table_key) == 1
                            for i in range(len(node.key.table_key)):
                                if node.key.reference_table[i] in [t[1] for t in relevant_tables_keys_names_sorted]:
                                    if (node_mapped_table[1] != node.key.reference_table[i]) and (node.mapped_table[1] != node.key.reference_table[i]):
                                        node_join_clause.append(f"{node_mapped_table[1]}.{node.key.table_key[i][0]} {"="} {node.key.reference_table[i]}.{node.key.reference_key[i][0]}")
                            node_join_clause_str = " AND ".join(node_join_clause)
                            assert len(node.key.reference_table) == 1
                            if node_join_clause_str:
                                join_clause.append(f"JOIN {node.key.reference_table[0]} AS {node.key.reference_table[0]} ON " + node_join_clause_str)
                        elif node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple):#weak entity, relationship
                            assert len(node.key.table_key) == 2
                            for i in range(len(node.key.table_key)):
                                #for weak entity len(node.key.reference_table) is 1 and for relationship it is 2
                                #only for i=0(parent key), following condition is executed for weak entity,
                                if len(node.key.reference_table) >= i+1:#for weak entity reference table added for parent only, for relationship ref table added for each participating entity
                                    #since node key's reference table stil points to original node.mapped_table, checking for only node_mapped_table[1] != node.key.reference_table[i]
                                    #will be always true for full table view case since node_mapped_table points to view and node.key.reference_table still points to original table(tuples coming from itself only).
                                    #Hence need to explicitly check for node.mapped_table[1] != node.key.reference_table[i] - this check makes sure to not execute join conditions
                                    #if a weak entity/relationship folded in same table
                                    if (node_mapped_table[1] != node.key.reference_table[i]) and (node.mapped_table[1] != node.key.reference_table[i]):
                                        node_join_clause = []
                                        reference_entity = graph.get_node_by_name(node.key.table_key_entities[i][0])#pk_entity = [[], []]
                                        if reference_entity.is_entity() and len(reference_entity.node_cover)>1:#if entity from which the reference table comes from is distributed in its node_cover
                                            #full table representation view is named "temp_"+node.unique_name for node distributed in node_cover
                                            reference_table_name = "temp_" + reference_entity.unique_name
                                            for j in range(len(node.key.table_key[i])):
                                                node_join_clause.append(f"{node_mapped_table[1]}.{node.key.table_key[i][j][0]} {"="} "
                                                        f"{reference_table_name}.{node.key.reference_key[i][j][0]}")
                                            node_join_clause_str = " AND ".join(node_join_clause)
                                            if node_join_clause_str:
                                                join_clause.append(f"JOIN {reference_table_name} AS {reference_table_name} ON " + node_join_clause_str)
                                        else:
                                            for j in range(len(node.key.table_key[i])):
                                                node_join_clause.append(f"{node_mapped_table[1]}.{node.key.table_key[i][j][0]} {"="} {node.key.reference_table[i]}.{node.key.reference_key[i][j][0]}")
                                            node_join_clause_str = " AND ".join(node_join_clause)
                                            if node_join_clause_str:
                                                join_clause.append(f"JOIN {node.key.reference_table[i]} AS {node.key.reference_table[i]} ON " + node_join_clause_str)
                else:#mvd in separate table
                    assert node.is_multivalued
                    assert node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple)
                    with_table_name = node.entity.unique_name + "_" + node.name
                    if node.entity.unique_name == entity_or_relationship_node.unique_name:#mvd in separate table coming from node itself
                        left_join_clause.append(f"LEFT JOIN {with_table_name} ON {with_table_name}.{node.key.table_key[0][0][0]} {"="} {node.key.reference_table[0]}.{node.key.reference_key[0][0][0]}")
                    else:#mvd in separate table coming from a differnt node - not node itself
                        if node.entity.is_weak_entity or (not node.entity.is_subclass and not len(node.entity.children)>0):#mvd coming from (weak entity) or (non-subclass non-root strong entity) - pks/joining reference table no change for mvd table
                            left_join_clause.append(f"LEFT JOIN {with_table_name} ON {with_table_name}.{node.key.table_key[0][0][0]} {"="} {node.key.reference_table[0]}.{node.key.reference_key[0][0][0]}")
                        else:##mvd coming from subclass or root strong entity - pks/joining reference table can change for mvd tables
                            #mvd from a subclass/root - pk in mvd table may not match subclass pk - e.g. mv_person table has person_id, and student has student_id
                            #mvd table's joining reference table also should be changed to student
                            #e.g. LEFT JOIN person_mv on person_mv.person_id = person.person_id -> LEFT JOIN person_mv on person_mv.person_id = student.student_id (if student on separate table)
                            #since mvd's entity belongs to a hierarchy - # of pks of the entity should be 1 - subclass/root is a strong entity
                            lowest_level_subclass_or_root_name = get_lowest_level_subclass_or_root_in_select_all_nodes_for_entity(graph, entity_or_relationship_node)
                            assert lowest_level_subclass_or_root_name
                            lowest_level_subclass = graph.get_node_by_name(lowest_level_subclass_or_root_name)
                            entity_table_to_join_with_mvd_table = lowest_level_subclass.mapped_table[1]
                            pk_of_entity_table_to_join_with_mvd_table = lowest_level_subclass.key.table_key[0][0]
                            left_join_clause.append(f"LEFT JOIN {with_table_name} ON {with_table_name}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{entity_table_to_join_with_mvd_table}.{pk_of_entity_table_to_join_with_mvd_table}")

        for node_name in entity_or_relationship_node.select_all_nodes:
            select_all_node = graph.get_node_by_name(node_name)

            #if entity_or_relationship_node is a weak entity with all by itself and has a depending entity which belongs to a hierarchy which is distributed in node_cover
            #since select * from weak_entity requires all attributes from depending entities as well, need to get the view
            if select_all_node.is_entity() and len(select_all_node.node_cover)>1:#can be a subclass or root in hierarchy
                for with_temp_table_dict in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[select_all_node.unique_name]:
                    for with_temp_table_name, with_temp_table_clause in with_temp_table_dict.items():
                        with_clause.append(with_temp_table_clause)#append the temp table view(including mvd tables) with full table construction for node

            select_all_node_mapped_table = get_mapped_table_for_entity_or_relationship(graph, select_all_node)

            #for an entity which belongs to a hierarchy, and contained in parent, need to consider each child by role type to get all tuples for entity
            #e.g. hierarchy Person -> Customer(20 tuples) -> Prime Customer(30) -> Family prime(10)
            #Customer, Prime Customer in same relation_1(Person table), Family prime all by itself in relation_2
            #Person - all by itself, Customer - contained in parent, Prime Customer - contained in parent, Family prime - all by itself
            #1. 20 entries with role_type 'customer' and 30 with 'primecustomer' and 10 with role_type 'familyprime' in relation_1
            #2. 10 entries in relation_2
            #e.g. If Family Prime is partially_by_itself or all_by_itself - all tuples of Family Prime
            #has a corresponding tuple in Person table - so select * from Customer == select * from relation_1 where role in ('customer','primecustomer', 'familyprime')
            #select * from primecustomer == select * from relation_1 where role in ('primecustomer', 'familyprime')
            #select * from familyprime == select * from relation_2
            #select * from person == select * from relation_1 - no need to filter by role
            #in hierarchy, if atleast one child of node is contained_in_parent - then node has role column, with each tuple identified by child name
            #in this example in relation_1 - 20 entries with role_type 'customer' and 30 with 'primecustomer' and 10 with role_type 'familyprime' in relation_1
            if select_all_node.is_entity() and select_all_node.is_subclass and select_all_node.is_contained_in_parent and len(select_all_node.node_cover)<=1:
                #only if contained_in_parent select_all_node doesn't have a view - add this - otherwise view has already filtered the tuples for select_all_node
                if len(select_all_node.children)>0:#entity_or_relationship_node can be any sub parent which is contained in parent
                    assert "role" in relevant_table_attribute_lists[select_all_node_mapped_table]
                    # collect entity names (entity + contained children)
                    all_entities = {select_all_node.unique_name}#add entity itself
                    #add all children rooted at node
                    find_all_children_rooted_at_node(select_all_node, all_entities)
                    all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                    where_clause.append(f"{select_all_node_mapped_table[1]}.{"role"} {"IN"} ({all_entities_str})")
                else:#entity itself - where clause would be just role in (entity_name)
                    #for leaf subclass contained in parent
                    assert "role" in relevant_table_attribute_lists[select_all_node_mapped_table]
                    where_clause.append(f"{select_all_node_mapped_table[1]}.{"role"} {"IN"} ('{select_all_node.unique_name}')")

            #for a node distributed in node_cover - full table view is already built in with clause temp table
            #all attributes for the node are in the temp table - even all the mvd attributes coming from separate tables are aggregated and folded
            #hence temp table view is sufficient and complete to get all attributes
            if select_all_node.is_entity() and len(select_all_node.node_cover)>1:#can be a root or subclass in hierarchy
                for attribute in select_all_node.attribute_list:
                    if select_all_node.unique_name != entity_or_relationship_node.unique_name:
                        if "pk_name" in attribute:#from other nodes need only non-pk attributes since pks are already coming from entity_relationship node itself
                            continue#avoid executing rest of the body in the loop
                    attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                    found_table_name = "temp_" + select_all_node.unique_name#full table representation view is named "temp_"+node.unique_name for nodes with node_cover
                    assert found_table_name==select_all_node_mapped_table[1]
                    select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")

            else:#node is not distributed in a node_cover - no view is built - need to build the attribute list - might be coming from different tables
                for attribute in select_all_node.attribute_list:
                    if select_all_node.unique_name != entity_or_relationship_node.unique_name:
                        if "pk_name" in attribute:#from other nodes need only non-pk attributes since pks are already coming from entity_relationship node itself
                            continue#avoid executing rest of the body in the loop
                    attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]

                    if "pk_name" in attribute:
                        found = select_all_node_mapped_table#pk attributes of an entity come from mapped table only
                        found_table_name = found[1] if found else None
                    elif "name" in attribute:#non pk attributes may come from node mapped table or other table - e.g. parent attributes of subclass if subclass is partially by itself, mvd in separate table
                        found = [t for t in relevant_table_attribute_lists if attr_name in relevant_table_attribute_lists[t]]
                        found_table_name = found[0][1] if found else None
                    if attribute["pk_type" if "pk_type" in attribute else "type"] == 'COMPOSITE':
                        if found:
                            # not split up
                            select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")
                        else:
                            # look for attr_name__ in the attribute lists
                            split_parts = []
                            for t in relevant_table_attribute_lists:
                                for a in relevant_table_attribute_lists[t]:
                                    if f"{attr_name}__" in a:
                                        split_parts.append(a)
                            select_clause.extend([f"{t} AS {t}" for t in split_parts])
                    elif attribute.get("is_multivalued", False):
                        if attribute.get("is_in_separate_table", False):
                            attribute_node = graph.get_node_by_name(attribute.get("unique_name", None))
                            assert attribute_node
                            with_table_name = attribute_node.entity.unique_name + "_" + attribute_node.name
                            mvd_with_clause_str = ""
                            mvd_select_clause = []
                            mvd_from_clause = []
                            mvd_where_clause = []
                            mvd_group_by_clause = []
                            generate_with_clause_for_mvd_table(attribute_node, tables, types, graph, mvd_select_clause, mvd_from_clause, mvd_where_clause, mvd_group_by_clause)
                            mvd_select_clause_str = ", ".join(mvd_select_clause)
                            mvd_from_clause_str = ", ".join(mvd_from_clause)
                            mvd_where_clause_str = " AND ".join(mvd_where_clause)
                            mvd_group_by_clause_str = ", ".join(mvd_group_by_clause)
                            mvd_with_clause_str += (f"{with_table_name} AS (SELECT {mvd_select_clause_str} FROM {mvd_from_clause_str} WHERE {mvd_where_clause_str} "
                                                        f"GROUP BY {mvd_group_by_clause_str})")
                            with_clause.append(mvd_with_clause_str)
                            if entity_or_relationship_node.unique_name not in with_clause_mvd_cte_temp_tables_for_nodes_with_no_node_cover:
                                with_clause_mvd_cte_temp_tables_for_nodes_with_no_node_cover[entity_or_relationship_node.unique_name] = [{attribute_node.unique_name : mvd_with_clause_str}]
                                #order of entering clauses matters - hence for each all by itself node - it is a list of dictionaries - e.g. mvd tables has to be put first before referencing in a query
                            else:
                                with_clause_mvd_cte_temp_tables_for_nodes_with_no_node_cover[entity_or_relationship_node.unique_name].append({attribute_node.unique_name : mvd_with_clause_str})
                            select_clause.append(f"COALESCE({with_table_name}.{attribute_node.name}, ARRAY[]::text[]) AS {attribute_node.name}")
                        else:
                            select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")
                    else:
                        select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")

        with_clause_without_with = ", ".join(with_clause)
        with_clause_str = ""
        if len(with_clause) > 0:
            with_clause_str += "WITH "
        with_clause_str += with_clause_without_with
        select_clause_str = ", ".join(select_clause)
        from_clause_str = ", ".join(from_clause)
        join_clause_str = " ".join(join_clause)
        left_join_clause_str = " ".join(left_join_clause)
        where_clause_str = " AND ".join(where_clause)
        # check if group by is needed
        if "AGG" in select_clause_str:#the group by clause is modified to include all attributes(except AGG attributes) to do the group by - each tuple grouped by all attributes
            group_by_clause = [c.split()[0] for c in select_clause if "AGG" not in c]#group by all attributes except attributes with 'AGG' in tuple
            group_by_clause_str = ", ".join(group_by_clause)

        select_all_clause = ""
        if with_clause:
            select_all_clause += f"{with_clause_str} "
        select_all_clause += f"SELECT {select_clause_str} FROM {from_clause_str}"
        if join_clause:
            select_all_clause += f" {join_clause_str}"
        if left_join_clause:
            select_all_clause += f" {left_join_clause_str}"
        if where_clause:
            select_all_clause += f" WHERE {where_clause_str}"
        if group_by_clause:
            select_all_clause += f" GROUP BY {group_by_clause_str}"
        memoized_select_all_queries[entity_or_relationship_node.unique_name] = select_all_clause

        return select_all_clause


#represnts entity with a CTE expression(with clause) created from union of node_cover
#only for entities coming from a hierarchy - could be a root or subclass
#node with type all by itself, contained in parent, partially by itself can have len(node.node_cover)>1
#if node is all by itself, for it to be len(node.node_cover)>1, it has to be a non-leaf - for a leaf node all option define all relevant tuples in the mapped_table
#all options except contained_all_descendants may induce len(node_cover)>1 for node
def generate_select_query_for_entity_with_node_cover(entity_node, tables, types, graph):
    node_cover = entity_node.node_cover
    assert len(node_cover)>1
    assert node_cover[0] == entity_node.unique_name #this matters since for union query attribute names are adhered to attribute names from entity itself(pk names can be different across node cover)
    #e.g.if entity is person and person contain person, student in node cover -  person_id in person, student_id in student - for attribute name structure, names in person are followed
    #hence node_cover is defined as a list instead of set(set doesn't maintain order)
    assert entity_node.mapped_table

    entity_node_attributes = []
    for attribute in entity_node.attribute_list:#to get own attributes for final select clause
        if "pk_name" in attribute:
            entity_node_attributes.append(attribute["pk_name"])
        elif "name" in attribute and attribute["name"] != "role":
            entity_node_attributes.append(attribute["name"])

    entity_node_mapped_table_all_attributes = entity_node_attributes.copy()#to get own attributes plus any folded weak entity/relationship attributes for temp table full view

    #commented out adding folded weak entity/relationships to temp view - since adding this is irrelavant and overhead to entity query
    #for folded weak entity/relationship - a separate view query is generated by generate_temp_view_with_clause_for_entity_with_node_cover - not same view query is reused
    """
    for table in tables:
        if table[0] == entity_node.mapped_table[1]:
            for table_attributes in table[1]:
                table_attribute_entity_unique_name = table_attributes[3]#entity from which attribute comes in
                table_attribute_node = graph.get_node_by_name(table_attribute_entity_unique_name)
                if (table_attribute_node.is_entity() and table_attribute_node.is_weak_entity and table_attribute_node.is_contained_in_parent and
                        table_attribute_node.parent_entity.unique_name == entity_node.unique_name and table_attributes[0] not in entity_node_mapped_table_all_attributes):
                    #folded weak entity only relevant to entity_node itself
                    entity_node_mapped_table_all_attributes.append(table_attributes[0])
                elif table_attribute_node.is_relationship() and table_attributes[0] not in entity_node_mapped_table_all_attributes:
                    assert check_if_relationship_is_1_N(table_attribute_node)#folded 1:N relationship
                    many_side_entity = table_attribute_node.entity2 if table_attribute_node.rel_dict['entity1']['one'] and not table_attribute_node.rel_dict['entity2']['one'] \
                        else table_attribute_node.entity1
                    if many_side_entity.unique_name == entity_node.unique_name:#folded relationship only relevant to entity_node itself
                        #if entity_node is contained_in_parent, mapped_table would have folded relationships relevant to other entities
                        #need to filter folded relationship only relevant to entity_node itself
                        entity_node_mapped_table_all_attributes.append(table_attributes[0])
            break
    """

    with_clause = []#mvd tables, temp table to aggregate all tuples across node cover for full representation of node added as with clauses
    union_clause = []
    select_all_clause = []
    from_all_clause = []



    mvd_cte_built_tables = []#mvd_tables_to_which_with_clauses_generated

    for node_name in node_cover:
        node_cover_node = graph.get_node_by_name(node_name)

        relevant_tables = [table for table in tables if table[0] in [select_table for sort_key, select_table in node_cover_node.select_all_tables]]
        relevant_tables_keys_names_sorted = sorted(list(node_cover_node.select_all_tables), key=lambda x: x[0])
        relevant_table_attribute_lists = {}
        for table in relevant_tables:
            table_tuple = next((t for t in relevant_tables_keys_names_sorted if t[1] == table[0]), None)
            relevant_table_attribute_lists[table_tuple] = [attribute_info[0] for attribute_info in table[1]]

        assert node_cover_node.mapped_table

        select_clause = []
        select_clause_without_folded_weak_entities_or_relationship_attributes = []
        from_clause = []
        join_clause = []
        left_join_clause = []
        where_clause = []

        node_cover_node_mapped_table = node_cover_node.mapped_table#consider original mapped_table
        from_clause.append(node_cover_node_mapped_table[1])
        tables_sorted_reverse = sorted(relevant_tables_keys_names_sorted, key=lambda x: x[0], reverse=True)#to make the join order - from smallest to largest table

        if len(tables_sorted_reverse)>1:#if joins needed - add pk, fk join clauses
            for joining_table in tables_sorted_reverse:
                node = graph.get_node_by_sort_key(joining_table[0])
                if not node.is_attribute():#all nodes belong to hierarchy - all nodes are strong entites

                    node_mapped_table = node.mapped_table

                    assert node_mapped_table in relevant_tables_keys_names_sorted

                    if node.key.reference_table is not None:
                        if node.key.table_key and isinstance(node.key.table_key[0], tuple):#strong entity, strong subclass entity
                            node_join_clause = []
                            assert len(node.key.table_key) == 1
                            for i in range(len(node.key.table_key)):
                                if node.key.reference_table[i] in [t[1] for t in relevant_tables_keys_names_sorted]:
                                    if (node_mapped_table[1] != node.key.reference_table[i]) and (node.mapped_table[1] != node.key.reference_table[i]):
                                        node_join_clause.append(f"{node_mapped_table[1]}.{node.key.table_key[i][0]} {"="} {node.key.reference_table[i]}.{node.key.reference_key[i][0]}")
                            node_join_clause_str = " AND ".join(node_join_clause)
                            assert len(node.key.reference_table) == 1
                            if node_join_clause_str:
                                join_clause.append(f"JOIN {node.key.reference_table[0]} AS {node.key.reference_table[0]} ON " + node_join_clause_str)

                else:#mvd in separate table
                    #a child in node_cover may have an own mvds in separate table which are not relevant attributes for parent - need to filter for those
                    #execute only if mvd in separate table coming from table_cover is relevant for entity_node
                    if node.name in entity_node_attributes:
                        assert node.is_multivalued
                        assert node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple)
                        with_table_name = node.entity.unique_name + "_" + node.name
                        if node.entity.unique_name == node_cover_node.unique_name:#mvd in separate table coming from node itself
                            left_join_clause.append(f"LEFT JOIN {with_table_name} ON {with_table_name}.{node.key.table_key[0][0][0]} {"="} {node.key.reference_table[0]}.{node.key.reference_key[0][0][0]}")
                        else:#mvd in separate table coming from a differnt node - not node itself
                            #all nodes in node_cover are nodes in hierarchy - hence any mvd table coming from a node in node_cover
                            #comes from a subclass/root in hierarchy. Hence pk/reference table may change
                            #mvd coming from subclass or root strong entity - pks/joining reference table can change for mvd tables
                            assert node.entity.is_subclass or len(node.entity.children)>0
                            #since mvd's entity belongs to a hierarchy - # of pks of the entity should be 1 - subclass/root is a strong entity
                            lowest_level_subclass_or_root_name = get_lowest_level_subclass_or_root_in_select_all_nodes_for_entity(graph, node_cover_node)
                            assert lowest_level_subclass_or_root_name
                            lowest_level_subclass = graph.get_node_by_name(lowest_level_subclass_or_root_name)
                            entity_table_to_join_with_mvd_table = lowest_level_subclass.mapped_table[1]
                            pk_of_entity_table_to_join_with_mvd_table = lowest_level_subclass.key.table_key[0][0]
                            left_join_clause.append(f"LEFT JOIN {with_table_name} ON {with_table_name}.{node.key.table_key[0][0][0]} {"="} "
                                                    f"{entity_table_to_join_with_mvd_table}.{pk_of_entity_table_to_join_with_mvd_table}")

        if node_cover_node.is_entity() and node_cover_node.is_subclass and node_cover_node.is_contained_in_parent:#only if contained_in_parent
            if len(node_cover_node.children)>0:#entity_or_relationship_node can be any sub parent which is contained in parent
                assert "role" in relevant_table_attribute_lists[node_cover_node_mapped_table]
                # collect entity names (entity + contained children)
                all_entities = {node_cover_node.unique_name}#add entity itself
                #add all children rooted at node
                find_all_children_rooted_at_node(node_cover_node, all_entities)
                all_entities_str = ", ".join(f"'{v}'" for v in all_entities)
                where_clause.append(f"{node_cover_node_mapped_table[1]}.{"role"} {"IN"} ({all_entities_str})")
            else:#entity itself - where clause would be just role in (entity_name)
                #for leaf subclass contained in parent
                assert "role" in relevant_table_attribute_lists[node_cover_node_mapped_table]
                where_clause.append(f"{node_cover_node_mapped_table[1]}.{"role"} {"IN"} ('{node_cover_node.unique_name}')")


        #node_cover for a node contains the node itself, and other child nodes which are contained_all_descendants/all_by_itself to fully cover all tuples for node
        if node_cover_node.unique_name != entity_node.unique_name:#not entity_node itself - some other child in the node_cover
            for attribute in node_cover_node.attribute_list:
                attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                #filter only required attributes from child node in node cover - child has parents' attributes + its own
                #pk, attributes coming from entity node and entity node's parents
                if ("pk_name" in attribute) or (attr_name in entity_node_attributes):
                    if not (attribute.get("is_multivalued", False) and attribute.get("is_in_separate_table", False)):#for any attribute which not a mvd in separate table - found table is node mapped table for all by itself or contained_all_descendants node
                        found = node_cover_node.mapped_table
                        found_table_name = found[1] if found else None
                    else:#mvd in separate table
                        assert attribute["is_multivalued"] and attribute["is_in_separate_table"]
                        found = [t for t in relevant_table_attribute_lists if attr_name in relevant_table_attribute_lists[t]]
                        found_table_name = found[0][1] if found else None
                        assert found[0][1] == attribute["mvd_separate_table_name"][1]

                    if attribute.get("is_multivalued", False):
                        if attribute.get("is_in_separate_table", False):
                            attribute_node = graph.get_node_by_name(attribute.get("unique_name", None))
                            assert attribute_node
                            with_table_name = attribute_node.entity.unique_name + "_" + attribute_node.name
                            if with_table_name not in mvd_cte_built_tables:
                                mvd_with_clause_str = ""
                                mvd_select_clause = []
                                mvd_from_clause = []
                                mvd_where_clause = []
                                mvd_group_by_clause = []
                                generate_with_clause_for_mvd_table(attribute_node, tables, types, graph, mvd_select_clause, mvd_from_clause, mvd_where_clause, mvd_group_by_clause)
                                mvd_select_clause_str = ", ".join(mvd_select_clause)
                                mvd_from_clause_str = ", ".join(mvd_from_clause)
                                mvd_where_clause_str = " AND ".join(mvd_where_clause)
                                mvd_group_by_clause_str = ", ".join(mvd_group_by_clause)
                                mvd_with_clause_str += (f"{with_table_name} AS (SELECT {mvd_select_clause_str} FROM {mvd_from_clause_str} WHERE {mvd_where_clause_str} "
                                                        f"GROUP BY {mvd_group_by_clause_str})")
                                with_clause.append(mvd_with_clause_str)
                                mvd_cte_built_tables.append(with_table_name)
                                if entity_node.unique_name not in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover:
                                    with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[entity_node.unique_name] = [{attribute_node.unique_name : mvd_with_clause_str}]
                                    #order of entering clauses matters - hence for each node - it is a list of dictionaries - e.g. mvd tables has to be put first before referencing in a query in union
                                else:
                                    with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[entity_node.unique_name].append({attribute_node.unique_name : mvd_with_clause_str})
                            select_clause.append(f"COALESCE({with_table_name}.{attribute_node.name}, ARRAY[]::text[]) AS {attr_name}")
                        else:#mvd stored as array
                            select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")
                    else:
                        select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")

            #commented out adding folded weak entity/relationships to temp view - since modified to genarate new views without using same view for all - overhead to keep irrelavnt attributes
            """
            node_cover_node_mapped_table = node_cover_node.mapped_table
            for attr_name in relevant_table_attribute_lists[node_cover_node_mapped_table]:
                #adding these folded attributes are required for full view of the entity when
                #writing select * queries for folded weak entities/relationships - since the same with clause table view is used
                if (attr_name not in entity_node_attributes) and (attr_name in entity_node_mapped_table_all_attributes):#folded weak entity/relationship
                    found_table_name = node_cover_node_mapped_table[1]
                    select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")
            """

        else:#node_cover_node is entity_node itself - all attributes from node itself needed except for role attribute - mvds could be in a separate table - no filtering of attributes
            for attribute in node_cover_node.attribute_list:
                attr_name = attribute["pk_name" if "pk_name" in attribute else "name"]
                if attr_name in entity_node_attributes:#filter "role" attribute in attribute_list

                    if "pk_name" in attribute:
                        found = node_cover_node.mapped_table#pk attributes of node come from mapped table
                        found_table_name = found[1] if found else None
                    elif "name" in attribute:#non pk attributes may come from node mapped table or other table - e.g. parent attributes of subclass if subclass is partially by itself, mvd in separate table
                        found = [t for t in relevant_table_attribute_lists if attr_name in relevant_table_attribute_lists[t]]
                        found_table_name = found[0][1] if found else None

                    if attribute.get("is_multivalued", False):
                        if attribute.get("is_in_separate_table", False):
                            attribute_node = graph.get_node_by_name(attribute.get("unique_name", None))
                            assert attribute_node
                            with_table_name = attribute_node.entity.unique_name + "_" + attribute_node.name
                            if with_table_name not in mvd_cte_built_tables:
                                mvd_with_clause_str = ""
                                mvd_select_clause = []
                                mvd_from_clause = []
                                mvd_where_clause = []
                                mvd_group_by_clause = []
                                generate_with_clause_for_mvd_table(attribute_node, tables, types, graph, mvd_select_clause, mvd_from_clause, mvd_where_clause, mvd_group_by_clause)
                                mvd_select_clause_str = ", ".join(mvd_select_clause)
                                mvd_from_clause_str = ", ".join(mvd_from_clause)
                                mvd_where_clause_str = " AND ".join(mvd_where_clause)
                                mvd_group_by_clause_str = ", ".join(mvd_group_by_clause)
                                mvd_with_clause_str += (f"{with_table_name} AS (SELECT {mvd_select_clause_str} FROM {mvd_from_clause_str} WHERE {mvd_where_clause_str} "
                                                        f"GROUP BY {mvd_group_by_clause_str})")
                                with_clause.append(mvd_with_clause_str)
                                mvd_cte_built_tables.append(with_table_name)
                                if entity_node.unique_name not in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover:
                                    with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[entity_node.unique_name] = [{attribute_node.unique_name : mvd_with_clause_str}]
                                else:
                                    with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[entity_node.unique_name].append({attribute_node.unique_name : mvd_with_clause_str})
                            select_clause.append(f"COALESCE({with_table_name}.{attribute_node.name}, ARRAY[]::text[]) AS {attr_name}")
                        else:#mvd stored as array
                            select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")
                    else:
                        select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")

            """
            node_cover_node_mapped_table = node_cover_node.mapped_table
            for attr_name in relevant_table_attribute_lists[node_cover_node_mapped_table]:
                #adding these folded attributes are required for full view of the entity when
                #writing select * queries for folded weak entities/relationships - since the same with clause table view is used
                if (attr_name not in entity_node_attributes) and (attr_name in entity_node_mapped_table_all_attributes):#folded weak entity/relationship
                    found_table_name = node_cover_node_mapped_table[1]
                    select_clause.append(f"{found_table_name}.{attr_name} AS {attr_name}")
            """

        select_clause_str = ", ".join(select_clause)
        from_clause_str = ", ".join(from_clause)
        join_clause_str = " ".join(join_clause)
        left_join_clause_str = " ".join(left_join_clause)
        where_clause_str = ", ".join(where_clause)

        node_cover_node_select_all_clause = ""
        node_cover_node_select_all_clause += f"SELECT {select_clause_str} FROM {from_clause_str}"

        if join_clause:
            node_cover_node_select_all_clause += f" {join_clause_str}"
        if left_join_clause:
            node_cover_node_select_all_clause += f" {left_join_clause_str}"
        if where_clause:
            node_cover_node_select_all_clause += f" WHERE {where_clause_str}"
        union_clause.append(node_cover_node_select_all_clause)

    union_clause_str = " UNION ALL ".join(union_clause)
    union_with_table_name = "temp_" + entity_node.unique_name
    union_with_clause_str = f"{union_with_table_name} AS ({union_clause_str})"
    with_clause.append(union_with_clause_str)
    #entity with folded weak entity/relationship attributes clause is saved to use for weak entity/relationship node select * query
    if entity_node.unique_name not in with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover:
        with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[entity_node.unique_name] = [{entity_node.unique_name : union_with_clause_str}]
    else:
        with_clause_cte_temp_tables_for_hierarchy_node_with_node_cover[entity_node.unique_name].append({entity_node.unique_name : union_with_clause_str})


    for attr_name in entity_node_attributes:#entity's own attributes.
        select_all_clause.append(attr_name)

    from_all_clause.append(union_with_table_name)

    with_clause_without_with = ", ".join(with_clause)
    with_clause_str = ""
    if len(with_clause) > 0:
        with_clause_str += "WITH "
    with_clause_str += with_clause_without_with
    select_all_clause_str = ", ".join(select_all_clause)
    from_all_clause_str = ", ".join(from_all_clause)

    select_all_query = ""
    if with_clause:
        select_all_query += f"{with_clause_str} "
    select_all_query += f"SELECT {select_all_clause_str} FROM {from_all_clause_str}"

    memoized_select_all_queries[entity_node.unique_name] = select_all_query
    return select_all_query

#no table node - no table option is only possible for non-leaf nodes(entities) in an inheritance hierarchy
def generate_select_query_for_no_table_entity(entity_node, tables, types, graph):
    assert entity_node.is_no_table
    select_clauses = []
    with_clause_for_no_table_entity = []
    tables_in_with_clause_for_no_table_entity = []
    entity_attribute_list = [attribute_info.get("pk_name" if "pk_name" in attribute_info else "name") for attribute_info in entity_node.attribute_list]
    all_by_itself_children_list_for_representing_entity = []
    find_all_by_itself_children_for_no_table_node(entity_node, all_by_itself_children_list_for_representing_entity)
    for child_name in all_by_itself_children_list_for_representing_entity:
        child = graph.get_node_by_name(child_name)
        child_attribute_list = []
        child_attribute_list.extend(key[0] for key in child.key.table_key)
        child_attribute_names = [attribute_info.get("pk_name" if "pk_name" in attribute_info else "name") for attribute_info in child.attribute_list]
        child_attribute_list += [attr for attr in entity_attribute_list if attr in child_attribute_names]#common attributes of parent and child
        assert len(entity_attribute_list) == len(child_attribute_list)
        if len(child.node_cover)==1:
            assert child.is_contained_all_descendants or child.is_all_by_itself
            if child.unique_name not in memoized_select_all_queries:
                generate_select_query_for_entity_with_no_node_cover(child, tables, types, graph)
            select_clauses.append(generate_select_query_for_no_table_entity_helper(entity_node, child, child_attribute_list, entity_attribute_list,
                                                                        with_clause_for_no_table_entity, tables_in_with_clause_for_no_table_entity, tables, types, graph))
        else:
            assert child.is_all_by_itself and len(child.children) > 0#non-leaf
            assert len(child.node_cover)>1
            if child.unique_name not in memoized_select_all_queries:
                generate_select_query_for_entity_with_node_cover(child, tables, types, graph)
            select_clauses.append(generate_select_query_for_no_table_entity_helper(entity_node, child, child_attribute_list, entity_attribute_list,
                                                                        with_clause_for_no_table_entity, tables_in_with_clause_for_no_table_entity, tables, types, graph))

    with_clause_without_with = ", ".join(with_clause_for_no_table_entity)
    with_clause_str = ""
    if len(with_clause_for_no_table_entity) > 0:
        with_clause_str += "WITH "
    with_clause_str += with_clause_without_with
    select_clause_str = " UNION ALL ".join(select_clauses)
    select_all_clause = ""
    if with_clause_for_no_table_entity:
        select_all_clause += f"{with_clause_str} "
    select_all_clause += f"{select_clause_str}"
    memoized_select_all_queries[entity_node.unique_name] = select_all_clause
    return select_all_clause

def generate_select_query_for_single_entity_or_relationship_helper(entity_or_relationship_node, tables, types, graph):
    if entity_or_relationship_node.unique_name in memoized_select_all_queries:
        return memoized_select_all_queries[entity_or_relationship_node.unique_name]

    if (entity_or_relationship_node.is_entity() and not len(entity_or_relationship_node.node_cover)>1 and
            not(entity_or_relationship_node.is_weak_entity and entity_or_relationship_node.is_contained_in_parent) and not entity_or_relationship_node.is_no_table):
        return generate_select_query_for_entity_with_no_node_cover(entity_or_relationship_node, tables, types, graph)
    elif entity_or_relationship_node.is_entity() and len(entity_or_relationship_node.node_cover) > 1 and not entity_or_relationship_node.is_no_table:
        return generate_select_query_for_entity_with_node_cover(entity_or_relationship_node, tables, types, graph)
    elif entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_no_table:
        return generate_select_query_for_no_table_entity(entity_or_relationship_node, tables, types, graph)
    elif entity_or_relationship_node.is_entity() and entity_or_relationship_node.is_weak_entity and entity_or_relationship_node.is_contained_in_parent:
        return generate_select_query_for_single_folded_weak_entity(entity_or_relationship_node, tables, types, graph)
    elif entity_or_relationship_node.is_relationship():
        if entity_or_relationship_node.entity1 != entity_or_relationship_node.entity2:
            return generate_select_query_for_relationship(entity_or_relationship_node, tables, types, graph)
        else:
            return generate_select_query_for_recursive_relationship(entity_or_relationship_node, tables, types, graph)

def generate_select_query_for_single_entity_or_relationship(entity_or_relationship_node, tables, types, graph):
    if len(memoized_select_all_queries) == 0:
        for node in graph.nodes:
            if node.is_entity() or node.is_relationship():
                generate_select_query_for_single_entity_or_relationship_helper(node, tables, types, graph)

    assert entity_or_relationship_node.unique_name in memoized_select_all_queries
    return memoized_select_all_queries[entity_or_relationship_node.unique_name]

