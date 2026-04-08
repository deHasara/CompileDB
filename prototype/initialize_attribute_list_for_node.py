from er_graph import Graph, Node, Entity, Relationship, Edge
def get_sub_attributes_of_composite_attribute(attribute, attribute_data):
    for attribute in attribute.children:#assume children are not of composite type
        data = {
            "name": attribute.name,
            "type": attribute.attr_type,
            "unique_name": attribute.unique_name
        }
        attribute_data.append(data)
    return attribute_data



def get_attributes_for_node_in_order_of_hierarchy(node:Node, data):#in order of from top to bottom for parents - all parents in the hierarchy and its own attributes
    if node.parent_entity is not None:                              #order of attributes insert matters to correctly map values to attribute name
        get_attributes_for_node_in_order_of_hierarchy(node.parent_entity, data)

    for attribute in node.attributes:
        if not attribute.is_primary_key and not attribute.is_discriminator:
            name = attribute.name
            type = attribute.attr_type
            unique_name = attribute.unique_name
            mapped_table_name = node.mapped_table if not attribute.is_multivalued else attribute.mapped_table
            is_multivalued = attribute.is_multivalued
            is_flattened = attribute.is_flattened if attribute.is_composite else None#for composite attributes
            sub_attributes = get_sub_attributes_of_composite_attribute(attribute, []) if attribute.is_composite else []
            is_in_separate_table = not attribute.mapped_table==attribute.entity.mapped_table if attribute.is_multivalued else None#for mvds
            mvd_separate_table_name = attribute.mapped_table if attribute.is_multivalued and not attribute.mapped_table==attribute.entity.mapped_table else None
            entity_unique_name = attribute.entity.unique_name
            node_data = {
                "name": name,
                "type": type,
                "unique_name": unique_name,
                "mapped_table": mapped_table_name,
                "is_multivalued": is_multivalued,
                "is_flattened": is_flattened,
                "sub_attributes": sub_attributes,
                "is_in_separate_table": is_in_separate_table,
                "mvd_separate_table_name": mvd_separate_table_name,
                "entity_unique_name": entity_unique_name,
            }
            data.append(node_data)
    return
def get_attribute_structure(node_data, node):#attribute structure to recreate entity/relationship - needed for mapping inserts
    data = []
    if isinstance(node.key.table_key, list):
        if node.key.table_key and isinstance(node.key.table_key[0], tuple):#strong entity, strong subclass entity
            for i in range(len(node.key.table_key)):
                pk_name = node.key.table_key[i][0]
                pk_type = node.key.table_key[i][1]
                pk_unique_name = node.key.table_key[i][2]
                pk_ER_name = node.key.table_key[i][3]
                pk_entity_name = node.key.table_key_entities[i]
                if node.key.reference_key is not None:#when a table for parent doesn't exist, sub class won't have a reference - concrete table inheritance
                    pk_reference_key_name = node.key.reference_key[i][0]
                    pk_reference_key_type = node.key.reference_key[i][1]
                    pk_reference_key_unique_name = node.key.reference_key[i][2]
                    pk_reference_node_unique_name = node.key.reference_node_unique_name[i]
                else:
                    pk_reference_key_name = None
                    pk_reference_key_type = None
                    pk_reference_key_unique_name = None
                    pk_reference_node_unique_name = None
                data.append({
                    "pk_name": pk_name,
                    "pk_type": pk_type,
                    "pk_unique_name": pk_unique_name,
                    "pk_ER_name": pk_ER_name,
                    "pk_entity_name": pk_entity_name,
                    "pk_reference_key_name": pk_reference_key_name,
                    "pk_reference_key_type": pk_reference_key_type,
                    "pk_reference_key_unique_name": pk_reference_key_unique_name,
                    "pk_reference_node_unique_name": pk_reference_node_unique_name
                })
            get_attributes_for_node_in_order_of_hierarchy(node, data)

        elif node.key.table_key and isinstance(node.key.table_key[0], list) and isinstance(node.key.table_key[0][0], tuple):#weak entity, relationship, mvds in separate table
            for i in range(len(node.key.table_key)): #todo - for 1:N relationships not all node keys are pks - only first entry - pk[0]
                for j in range(len(node.key.table_key[i])):
                    pk_name = node.key.table_key[i][j][0]
                    pk_type = node.key.table_key[i][j][1]
                    pk_unique_name = node.key.table_key[i][j][2]
                    pk_ER_name = node.key.table_key[i][j][3]
                    pk_entity_name = node.key.table_key_entities[i][0]
                    if len(node.key.reference_key[i])>0:
                        pk_reference_key_name = node.key.reference_key[i][j][0]
                        pk_reference_key_type = node.key.reference_key[i][j][1]
                        pk_reference_key_unique_name = node.key.reference_key[i][j][2]
                        pk_reference_node_unique_name = node.key.reference_node_unique_name[i] if not node.is_relationship() else None#for relationship this not defined
                    else:
                        pk_reference_key_name = None
                        pk_reference_key_type = None
                        pk_reference_key_unique_name = None
                        pk_reference_node_unique_name = None
                    data.append({
                        "pk_name": pk_name,
                        "pk_type": pk_type,
                        "pk_unique_name": pk_unique_name,
                        "pk_ER_name": pk_ER_name,
                        "pk_entity_name": pk_entity_name,
                        "pk_reference_key_name": pk_reference_key_name,
                        "pk_reference_key_type": pk_reference_key_type,
                        "pk_reference_key_unique_name": pk_reference_key_unique_name,
                        "pk_reference_node_unique_name": pk_reference_node_unique_name
                    })

            for attribute in node.attributes:
                if not attribute.is_primary_key and not attribute.is_discriminator:
                    name = attribute.name
                    type = attribute.attr_type
                    unique_name = attribute.unique_name
                    mapped_table_name = node.mapped_table if not attribute.is_multivalued else attribute.mapped_table
                    is_multivalued = attribute.is_multivalued
                    is_flattened = attribute.is_flattened if attribute.is_composite else None#for composite attributes
                    sub_attributes = get_sub_attributes_of_composite_attribute(attribute, []) if attribute.is_composite else []
                    is_in_separate_table = not attribute.mapped_table==attribute.entity.mapped_table if attribute.is_multivalued else None#for mvds
                    mvd_separate_table_name = attribute.mapped_table if attribute.is_multivalued and not attribute.mapped_table==attribute.entity.mapped_table else None
                    entity_unique_name = attribute.entity.unique_name
                    attribute_data = {
                        "name": name,
                        "type": type,
                        "unique_name": unique_name,
                        "mapped_table": mapped_table_name,
                        "is_multivalued": is_multivalued,
                        "is_flattened": is_flattened,
                        "sub_attributes": sub_attributes,
                        "is_in_separate_table": is_in_separate_table,
                        "mvd_separate_table_name": mvd_separate_table_name,
                        "entity_unique_name": entity_unique_name,
                    }
                    data.append(attribute_data)



    node_data["attribute_list"] = data

def generate_attribute_list(obj):#needed for mapping inserts, and checking attribute parameter values(e.g. is mvd attribute in separate table) when initializing select_all_tables for select * statements
    node_data = {}

    if isinstance(obj, Entity) or isinstance(obj, Relationship):
        get_attribute_structure(node_data, obj)
        obj.attribute_list = node_data["attribute_list"]
    else:
        obj.attribute_list = node_data
