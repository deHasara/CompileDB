def check_conditions_for_abstract_table(node, config):
    return check_hierarchy_for_abstract_table(node, config)


#immediate children of abstract table can be no_table or all_by_itself only. Need to explore for each child. If a child is all_by_itself, no need to explore in that path.
# If a child is no_table, need to explore, for all children of that child.
#Except for any upper nodes, the leaf nodes in the hierarchy cannot be no_table
#no_table parent cannot have an immediate child with partially_by_itself or contained_in_parent
def check_hierarchy_for_abstract_table(node, config):
    #a leaf child cannot be no table
    if len(node.children)==0 and config.get(node.unique_name)=="no_table":
        return False
    for child in node.children:
        if config.get(child.unique_name)=="all_by_itself" or config.get(child.unique_name)=="strictly_all_by_itself":
            continue
        elif config.get(child.unique_name)=="no_table":
            #explore for all children of the child with no_table
            if not check_hierarchy_for_abstract_table(child, config):
                return False
        else:#returns False for any other option - partially_by_itself, contained_in_parent - no_table parent cannot have an immediate child with those 2 options
            return False
    return True

def get_many_side_of_relationship(node):
    if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:
        return node.entity2.unique_name
    elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:
        return node.entity1.unique_name

def check_if_1_N_relationship(node):
    if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:
        return True
    elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:
        return True
    else:
        return False


#if weak entity participates in a relationship, that weak entity cannot be folded into the parent entity- cannot define pk/fk constraints for relationship
#node is the folded weak entity. Returns False if it participates in a relationship (M-N) or (1-N)
def check_if_folded_weak_entity_participates_in_relationship(graph, node, config):
    for node_unique_name in config.keys():
        node_in_config = graph.get_node_by_name(node_unique_name)
        if node_in_config.is_relationship():
            if node_in_config.entity1.unique_name == node.unique_name or node_in_config.entity2.unique_name == node.unique_name:
                return False
            else:
                continue
    return True

def check_mvd_conditions_for_folded_weak_entity(node, config):
    for attribute in node.attributes:#mvd attributes of a folded weak entity cannot be all_by_itself
        if attribute.is_multivalued and config.get(attribute.unique_name)=="all_by_itself":
            return False
        else:
            continue
    return True



#if weak entity folded to strong entity and weak entity has mvds, the mvds cannot be all_by_itself
#if 1:N folded to N side and folded relationship has mvds, mvds may or may not be all_by_itself - here no restriction
#if node is all_by_itself, all attributes from all parents in hierarchy included in the node(if parents have mvds in separate tables, mvds would be still in separate table)
#if node is contained_all_descendants/all_by_itself/partiall_by_itself/contained_in_parent, its mvds may or may not be all_by_itself - no restriction

#decision for mvd attribute being consistent across the hierarchy
#If a class in hierarchy(root or subclass) has a mvd attribute - if that mvd attribute is set to be in_separate_table, for all classes child to that class has it as in_separate_table
#mapping to same separate table
# - if that mvd attribute is set to be contained_in_parent, for all classes child to that class has it as contained in its own

#If node is contained_all_descendants, its mvds may or may not be all_by_itself - no restriction
#If a subclass is contained in parent, then its own mvds may or may not be all by itself - no restriction
#Same for partially_by_itself and all_by_itself
#It is just that decision for a mvd attribute has to be consistent across the entire hierarchy

#If a node is no_table(no_table is a possibility for nodes in hierarchy only), it can still have mvds in separate_tables

#In hierarchy - except for the restrictions that root cannot be partially_by_itself/contained_in_parent, leaf nodes cannot be no_table, and immediate children of a
#no_table node can be only contained_all_descendants/all_by_itself/no_table, any node in hierarchy is free to pick from one of the 5 options - contained_all_descendants,
#all_by_itself, partially_by_itself, contained_in_parent, no_table