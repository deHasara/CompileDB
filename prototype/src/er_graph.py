from email.policy import default
from enum import Enum
import json
from typing import Dict, List, Any, Optional
from sql_analyzer import EntityType

class NodeType(Enum):
    ENTITY = 1
    RELATIONSHIP = 2
    ATTRIBUTE = 3

class EdgeType(Enum):
    ENTITY_ATTRIBUTE = 1
    ATTRIBUTE_ATTRIBUTE = 2
    ENTITY_RELATIONSHIP = 3
    ENTITY_ENTITY = 4
    RELATIONSHIP_ATTRIBUTE = 5

class Key:
    def __init__(self, key, reference_key, reference_table=None, reference_node_unique_name=None, table_key_entities=None):
        self.table_key = key#pk
        self.reference_key = reference_key#fk
        self.reference_table = reference_table#fk table
        self.reference_node_unique_name = reference_node_unique_name#fk node fks come from
        self.table_key_entities = table_key_entities#pk entity node pks come from

    def __repr__(self):
        #return f"{self.node_type}({self.name})"
        return f"{self.table_key},{self.reference_key},{self.reference_table},{self.reference_node_unique_name},{self.table_key_entities}"


class Node:
    def __init__(self, name: str, unique_name: str = None):
        self.name = name
        self.unique_name = unique_name.lower() if unique_name else self.name.lower()
        self.type = None
        self.key = None#pk,fk,fk table
        self.mapped_table = None#each node(entity, relationship, mvds) is mapped to physical table - Person mapped to [Person], Person_phone_number mapped to [Person_phone_number]
        self.sort_key = None#sort key to sort nodes by the order of -> entity, sub class, weak, relationship, attribute

        self.partitioning_options = []
        self.node_type_for_partitioning_options = None

        self.mapped_tables_list = []#need for folded relationships/weak entities with participating/parent entity distributed in node cover - tables in which a node is distributed

    def is_attribute(self):
        return self.type == NodeType.ATTRIBUTE
    def is_entity(self):
        return self.type == NodeType.ENTITY
    def is_relationship(self):
        return self.type == NodeType.RELATIONSHIP

class Entity(Node):
    def __init__(self, name: str, unique_name: str = None):
        super().__init__(name, unique_name)
        self.is_subclass = False
        self.is_weak_entity = False
        self.parent_entity = None
        self.type = NodeType.ENTITY
        self.entity_dict = None
        self.node_tables = None#Each entity can be mapped to multiple physical tables -> Person - Person, Person_Phone_number - to answer query for Person, both tables needed
                            #node_tables is required to make all necessary inserts into multiple tables for an entity
        self.select_all_tables = None#tables required to answer select * from entity query
        self.select_all_nodes = None#nodes required to answer select * from entity query
        self.select_all_attributes_count = None#no of columns output in select * from entity query - for weak_entity/relationship need to get all depending/participating entities
        self.is_no_table = False
        self.is_parent_in_table = False#required for sub class/weak entity type
        self.is_immediate_parent_in_a_different_table = False#required for sub class
        self.is_contained_in_parent = False#contained in parent gives same info as is parent in table
        self.is_partially_by_itself = False#required to define the table attributes for entity - child has only its own attributes - parent has to have a table in this case
        self.is_all_by_itself = False#when node has tuples from itself(if hierarchical node, may contain child tuples based on child node option)
                                #required to define the table attributes for entity
                                #if all_by_itself true and is_immediate_parent_in_a_different_table true - child has all attributes and parent also has a table
                                #if all_by_itself true and is_immediate_parent_in_a_different_table false - child has all attributes and parent doesn't have a table
        self.is_contained_all_descendants = False#when node contains all its tuples and all tuples from all descendants under its subtree
        #is_contained_in_parent, is_partially_by_itself, is_all_by_itself, is_contained_all_descendants  - set by search algorithm
        #is_parent_in_table, is_immediate_parent_in_a_different_table - can be set by checking the mapped_table of parent and entity
        self.immediate_parent_with_all_by_itself_unique_name = None
        self.children = []#to keep the immediate children entities of the inheritance hierarchy

        # we will keep the attributes explicitly
        self.attributes = []
        self.is_mvds = False

        self.attribute_list = None#for inserts - maintain entire attribute list - all attributes from parents and its own only - extra attributes added to table not added
                                #to avoid breaking the correct mapping of insert values - e.g. "role", "advisor_id" if table is [Person, Instructor, Student, Advisor]

        self.is_total = None#for subclasses in inhertiance hierarchy - True if total participation
        self.is_option_to_be_abstract = None#if parent entity has 0 inserts and if all immediate children entities have total participation, parent entity has the option
                                            #to have no physical table - this is for inheritance hierarchies

        self.insert_frequency = 0#no of inserts for db initialization - node count
                    #required to decide if node can have no table partitioning option - this indicates direct inserts(e.g. Person entity inserts) - not for example inserts inferred from children
        self.workload_select_frequency = 0
        self.workload_insert_frequency = 0#after db is initialized, insert frequency for entity in workload queries
        self.relation_size = 0#actual no of tuples for node - e.g. for a parent, this shows total tuples from itself including all propagated from all its children
        self.strict_relation_size = 0#tuples only from itself - without all children tuples
                             #when no children(non-leaf node in hierarchy with all by itself), strict_relation_size and the relation_size the same
        self.root_sort_key = None#this is updated for children - to keep track of root of hierarchy - required for data generation for inheritance hierarchies - for other non-subclass nodes this is as same as sort key
        self.starting_tuple_no = 1#required for data generation - for inheritance hierarchies

        self.node_cover = []#minimum node cover to represent a hierarchical entity - defined for hierarchical entities only - need for folded relationships/weak entities with parent entity  having node cover > 1


class Relationship(Node):
    def __init__(self, name: str, unique_name: str = None):
        super().__init__(name, unique_name)
        self.type = NodeType.RELATIONSHIP
        self.recursive_relationship_roles = None

        # the entities that it connects to
        self.entity1 = None
        self.entity2 = None

        self.rel_dict = None

        self.attribute_list =None#for inserts - maintain entire attribute list - all attributes from parents and its own

        self.node_tables = None#Each relationship can be mapped to multiple physical tables
        self.select_all_tables = None#tables required to answer select * from relationship query
        self.select_all_nodes = None#nodes required to answer select * from entity query
        self.select_all_attributes_count = None#no of columns output in select * from entity query

        # we will keep the attributes explicitly
        self.attributes = []
        self.is_mvds = False

        self.insert_frequency = 0#no of inserts for db initialization - node count
        self.workload_select_frequency = 0#after db is initialized, select * frequency for relationship in workload queries
        self.workload_insert_frequency = 0#after db is initialized, insert frequency for relationship in workload queries
        self.relation_size = 0

class Attribute(Node):
    def __init__(self, name: str, unique_name: str, attr_type: str):
        super().__init__(name, unique_name)
        self.attr_type = attr_type
        self.is_multivalued = False
        self.is_composite = False
        self.is_primary_key = False
        self.is_discriminator = False#for weak entities
        self.is_flattened = False#for composite attributes - this decision needs to be set at partitioning phase
        self.is_in_separate_table = True#for mvds - this will be set by search algorithm
        self.children = None#for sub attributes of composite attributes
        self.entity = None#entity to which attribute belongs
        self.parent_attribute = None#parent attribute of the attribute - for composite attributes
        self.type = NodeType.ATTRIBUTE
        self.attr_dict = None

        # we will keep the attributes explicitly - this is for nested composite attributes
        self.attributes = []

        self.relation_size = 0#required when mvds in separate table
        self.workload_insert_frequency = 0#required when mvds in separate table and when insert queries in workload do inserts to mvd table
                                        #after db is initialized, insert frequency for mvd table in workload queries

class Edge:
    def __init__(self, edge_type: EdgeType, source: Node, target: Node, properties: Dict[str, Any] = None):
        self.edge_type = edge_type
        self.source = source
        self.target = target

class Graph:
    def __init__(self):
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []
        self.sort_key = 1
        self.config = None
        self.cost = None#estimated total cost for config and workload
        self.nodes_cost = None#estimated individual node cost for config

    def add_node(self, node: Node):
        self.nodes.append(node)
        return node

    def add_edge(self, edge: Edge):
        self.edges.append(edge)
        return edge

    def get_node_by_name(self, unique_name: str):
        for node in self.nodes:
            if node.unique_name == unique_name.lower():
                assert node
                return node
        assert f"Node with unique name {unique_name} not found"

    def get_node_by_sort_key(self, sort_key: int):
        for node in self.nodes:
            if node.sort_key == sort_key:
                assert node
                return node
        assert f"Node with sort key {sort_key} not found"

    def get_edges_by_node(self, node: Node) -> List[Edge]:
        return [edge for edge in self.edges if edge.source == node or edge.target == node]

    def get_neighbors(self, node: Node) -> List[Node]:
        neighbors = []
        for edge in self.get_edges_by_node(node):
            if edge.source == node:
                neighbors.append(edge.target)
            else:
                neighbors.append(edge.source)
        return neighbors

    # For an entity node, get all its attributes
    def get_attributes(self, node: Node) -> List[Node]:
        assert node.type == NodeType.ENTITY and node.attributes
        return node.attributes

    def add_entity(self, entity_dict):
        n = self.add_node(Entity(entity_dict['table_name']))

        n.entity_dict = entity_dict
        n.is_subclass = entity_dict['entity_type'] == EntityType.SUBCLASS
        n.is_weak_entity = entity_dict['entity_type'] == EntityType.WEAK
        n.attributes = []

        n.sort_key = self.sort_key
        n.root_sort_key = self.sort_key
        self.sort_key += 1

        for attr in entity_dict['attributes']:
            # Takes care of recursive composite attributes
            self.add_attribute(attr, entity_dict['table_name'], entity = n, parent_attribute = None)

        if n.is_subclass:
            n.is_total = entity_dict['total']

            n.parent_entity = self.get_node_by_name(entity_dict['parent_entity'])
            assert n.parent_entity
            n.parent_entity.children.append(n)
            n.root_sort_key = n.parent_entity.root_sort_key#root_sort_key updated if node is a child in hierarchy - directs to root of hierarchy
            self.add_edge(Edge(EdgeType.ENTITY_ENTITY, n, n.parent_entity))

        if n.is_weak_entity:
            n.parent_entity = self.get_node_by_name(entity_dict['parent_entity'])
            assert n.parent_entity
            self.add_edge(Edge(EdgeType.ENTITY_ENTITY, n, n.parent_entity))

    def add_attribute(self, attr, parent_unique_name, entity, parent_attribute):
        unique_name = (parent_unique_name + "." + attr['attr_name']).lower()

        this_node = self.add_node(Attribute(attr['attr_name'], unique_name, attr_type = attr['attr_type']))
        this_node.is_composite = (attr['attr_type'].upper() == 'COMPOSITE')
        this_node.is_multivalued = attr.get('is_multivalued', False)
        this_node.is_primary_key = attr.get('is_primary_key', False)
        this_node.is_discriminator = attr.get('is_discriminator', False)
        if parent_attribute:
            this_node.parent_attribute = parent_attribute
            parent_attribute.children.append(this_node)
        this_node.entity = entity

        entity.attributes.append(this_node)
        if entity.is_entity():
            entity.is_mvds = this_node.is_multivalued if this_node.is_multivalued else entity.is_mvds

        #this_node.attr_dict = attr

        this_node.sort_key = self.sort_key
        self.sort_key += 1

        if this_node.is_composite:
            this_node.children = []
            for sub_attr in attr['sub_attributes']:
                self.add_attribute(sub_attr, unique_name, entity=this_node, parent_attribute=this_node)

        #if attribute is mvd, add edge
        if this_node.is_multivalued:
            if this_node.entity.type == NodeType.ENTITY:
                self.add_edge(Edge(EdgeType.ENTITY_ATTRIBUTE, this_node, this_node.entity))
            elif this_node.entity.type == NodeType.RELATIONSHIP:
                self.add_edge(Edge(EdgeType.RELATIONSHIP_ATTRIBUTE, this_node, this_node.entity))


    def add_relationship(self, rel_dict):
        e1 = self.get_node_by_name(rel_dict['entity1']['name'])
        e2 = self.get_node_by_name(rel_dict['entity2']['name'])
        assert e1 and e2

        n = self.add_node(Relationship(rel_dict['table_name']))
        n.entity1 = e1
        n.entity2 = e2

        n.rel_dict = rel_dict

        n.sort_key = self.sort_key
        self.sort_key += 1

        for attr in rel_dict['attributes']:
            self.add_attribute(attr, rel_dict['table_name'], entity = n, parent_attribute = None)

        self.add_edge(Edge(EdgeType.ENTITY_RELATIONSHIP, n, e1))
        self.add_edge(Edge(EdgeType.ENTITY_RELATIONSHIP, n, e2))

        if rel_dict['entity1']['role']:
            n.recursive_relationship_roles = (rel_dict['entity1']['role'], rel_dict['entity2']['role'])


#####################################################
########### Graph Serialization and Deserialization
#####################################################

import json
from typing import Dict

class GraphEncoder(json.JSONEncoder):

    def _convert_nested_tuples(self, data):
        if isinstance(data, tuple):
            return list(data)
        elif isinstance(data, list):
            return [self._convert_nested_tuples(item) for item in data]
        else:
            return data

    def convert_entity(self, node_data, entity):
        data = {
            "is_subclass": entity.is_subclass,
            "is_weak_entity": entity.is_weak_entity,
            "parent_entity": entity.parent_entity.unique_name if entity.parent_entity else None,
            "entity_dict": entity.entity_dict,
            "node_tables": [table for table in entity.node_tables] if entity.node_tables else [],
            "select_all_tables": [table for table in entity.select_all_tables] if entity.select_all_tables else [],
            "select_all_nodes": [node_name for node_name in entity.select_all_nodes] if entity.select_all_nodes else [],
            "select_all_attributes_count": entity.select_all_attributes_count,
            "is_parent_in_table": entity.is_parent_in_table,
            "is_immediate_parent_in_a_different_table": entity.is_immediate_parent_in_a_different_table,
            "is_no_table": entity.is_no_table,
            "is_contained_in_parent": entity.is_contained_in_parent,
            "is_partially_by_itself": entity.is_partially_by_itself,
            "is_all_by_itself": entity.is_all_by_itself,
            "is_contained_all_descendants": entity.is_contained_all_descendants,
            "immediate_parent_with_all_by_itself_unique_name": entity.immediate_parent_with_all_by_itself_unique_name,
            "children": [child.unique_name for child in entity.children],
            "attributes": [attribute.unique_name for attribute in entity.attributes],
            "is_mvds": entity.is_mvds,
            "attribute_list": entity.attribute_list,
            "is_total": entity.is_total,
            "is_option_to_be_abstract": entity.is_option_to_be_abstract,
            "insert_frequency": entity.insert_frequency,
            "workload_select_frequency": entity.workload_select_frequency,
            "workload_insert_frequency": entity.workload_insert_frequency,
            "relation_size": entity.relation_size,
            "strict_relation_size": entity.strict_relation_size,
            "node_cover": [node_name for node_name in entity.node_cover] if entity.node_cover else []
        }
        return node_data.update(data)

    def convert_relationship(self, node_data, relationship):
        data = {
            "recursive_relationship_roles": relationship.recursive_relationship_roles,
            "entity1": relationship.entity1.unique_name,
            "entity2": relationship.entity2.unique_name,
            "rel_dict": relationship.rel_dict,
            "node_tables": [table for table in relationship.node_tables] if relationship.node_tables else [],
            "select_all_tables": [table for table in relationship.select_all_tables] if relationship.select_all_tables else [],
            "select_all_nodes": [node_name for node_name in relationship.select_all_nodes] if relationship.select_all_nodes else [],
            "select_all_attributes_count": relationship.select_all_attributes_count,
            "attributes": [attribute.unique_name for attribute in relationship.attributes],
            "is_mvds": relationship.is_mvds,
            "attribute_list": relationship.attribute_list,
            "insert_frequency": relationship.insert_frequency,
            "workload_select_frequency": relationship.workload_select_frequency,
            "workload_insert_frequency": relationship.workload_insert_frequency,
            "relation_size": relationship.relation_size
        }
        return node_data.update(data)

    def convert_attribute(self, node_data, attribute):
        data = {
            "attr_type": attribute.attr_type,
            "is_multivalued": attribute.is_multivalued,
            "is_composite": attribute.is_composite,
            "is_primary_key": attribute.is_primary_key,
            "is_discriminator": attribute.is_discriminator,
            "is_flattened": attribute.is_flattened,
            "is_in_separate_table": attribute.is_in_separate_table,
            "children": [child.unique_name for child in attribute.children] if attribute.children is not None else [],
            "entity": attribute.entity.unique_name,
            "parent_attribute": attribute.parent_attribute.unique_name if attribute.parent_attribute is not None else None,
            "attr_dict": attribute.attr_dict,
            "attributes": [attribute.unique_name for attribute in attribute.attributes],
            "workload_insert_frequency": attribute.workload_insert_frequency,
            "relation_size": attribute.relation_size
        }
        return node_data.update(data)


    def default(self, obj):
        if isinstance(obj, Node):
            node_data = {
                "name": obj.name,
                "unique_name": obj.unique_name,
                "type": obj.type.name,
                "key": self.default(obj.key),
                "mapped_table": obj.mapped_table,
                "mapped_tables_list": [mapped_table for mapped_table in obj.mapped_tables_list] if obj.mapped_tables_list is not None else [],
                "sort_key": obj.sort_key,
                "partitioning_options": obj.partitioning_options,
                "node_type_for_partitioning_options": obj.node_type_for_partitioning_options
            }
            if isinstance(obj, Entity):
                self.convert_entity(node_data, obj)
            elif isinstance(obj, Relationship):
                self.convert_relationship(node_data, obj)
            elif isinstance(obj, Attribute):
                self.convert_attribute(node_data, obj)
            return node_data

        elif isinstance(obj, Key):
            return {
                "table_key": self._convert_nested_tuples(obj.table_key),
                "table_key_entities": self._convert_nested_tuples(obj.table_key_entities),
                "reference_key": self._convert_nested_tuples(obj.reference_key),
                "reference_table": obj.reference_table,
                "reference_node": obj.reference_node_unique_name
            }
        elif isinstance(obj, Edge):
            return {
                "type": "edge",
                "edge_type": obj.edge_type.name,
                "source": obj.source.unique_name,
                "target": obj.target.unique_name
            }


def serialize_graph(graph: Graph) -> str:
    return json.dumps({
        "nodes": graph.nodes,
        "edges": graph.edges,
        "config": graph.config,
        "cost": graph.cost,
        "nodes_cost": graph.nodes_cost
    }, cls=GraphEncoder, indent=2)

def convert_nested_lists(data):
    if data is None:
        return None
    if all(isinstance(elem, list) for elem in data):
        if all(isinstance(sub_elem, list) for elem in data for sub_elem in elem):
            return [[tuple(inner) for inner in outer] for outer in data]
        else:
            return [tuple(inner) for inner in data]
    return data  # Return as is if not matching the above structures


def deserialize_graph(json_str: str) -> Graph:
    data = json.loads(json_str)
    graph = Graph()

    node_map: Dict[str, Node] = {}

    for node_data in data["nodes"]:
        type = node_data["type"]
        node = None
        if type == "ENTITY":
            node = Entity(
                name=node_data["name"],
                unique_name=node_data["unique_name"]
            )
            table_key = convert_nested_lists(node_data["key"]["table_key"])
            reference_key = convert_nested_lists(node_data["key"]["reference_key"])
            reference_table = convert_nested_lists(node_data["key"]["reference_table"])
            reference_node = convert_nested_lists(node_data["key"]["reference_node"])
            table_key_entities = convert_nested_lists(node_data["key"]["table_key_entities"])
            node.key = Key(table_key, reference_key, reference_table, reference_node, table_key_entities)
            node.mapped_table = tuple(node_data.get("mapped_table")) if node_data.get("mapped_table") is not None else None
            node.sort_key = node_data["sort_key"]
            node.partitioning_options = node_data["partitioning_options"]
            node.node_type_for_partitioning_options = node_data["node_type_for_partitioning_options"]
            node.is_subclass = node_data["is_subclass"]
            node.is_weak_entity = node_data["is_weak_entity"]
            node.parent_entity = node_map[node_data["parent_entity"]] if node_data["parent_entity"] is not None else None
            node.entity_dict = node_data["entity_dict"]
            node.node_tables = set(tuple(lst) for lst in node_data["node_tables"])
            node.select_all_tables = set(tuple(lst) for lst in node_data["select_all_tables"])
            node.select_all_nodes = node_data["select_all_nodes"]
            node.select_all_attributes_count = node_data["select_all_attributes_count"]
            node.is_parent_in_table = node_data["is_parent_in_table"]
            node.is_immediate_parent_in_a_different_table = node_data["is_immediate_parent_in_a_different_table"]
            node.is_no_table = node_data["is_no_table"]
            node.is_contained_in_parent = node_data["is_contained_in_parent"]
            node.is_partially_by_itself = node_data["is_partially_by_itself"]
            node.is_all_by_itself = node_data["is_all_by_itself"]
            node.is_contained_all_descendants= node_data["is_contained_all_descendants"]
            node.immediate_parent_with_all_by_itself_unique_name = node_data["immediate_parent_with_all_by_itself_unique_name"]
            #children, attributes added after all nodes initialized
            node.temp_children = node_data["children"]
            node.temp_attributes = node_data["attributes"]
            node.is_mvds = node_data["is_mvds"]
            node.attribute_list = node_data["attribute_list"]
            node.is_total = node_data["is_total"]
            node.is_option_to_be_abstract = node_data["is_option_to_be_abstract"]
            node.insert_frequency = node_data["insert_frequency"]
            node.workload_select_frequency = node_data["workload_select_frequency"]
            node.workload_insert_frequency = node_data["workload_insert_frequency"]
            node.relation_size = node_data["relation_size"]
            node.strict_relation_size = node_data["strict_relation_size"]
            node.node_cover = node_data["node_cover"]
            node.mapped_tables_list = node_data["mapped_tables_list"]

        elif type == "RELATIONSHIP":
            node = Relationship(
                name=node_data["name"],
                unique_name=node_data["unique_name"]
            )
            table_key = convert_nested_lists(node_data["key"]["table_key"])
            reference_key = convert_nested_lists(node_data["key"]["reference_key"])
            reference_table = convert_nested_lists(node_data["key"]["reference_table"])
            reference_node = convert_nested_lists(node_data["key"]["reference_node"])
            table_key_entities = convert_nested_lists(node_data["key"]["table_key_entities"])
            node.key = Key(table_key, reference_key, reference_table, reference_node, table_key_entities)
            node.mapped_table = tuple(node_data.get("mapped_table")) if node_data.get("mapped_table") is not None else None
            node.sort_key = node_data["sort_key"]
            node.partitioning_options = node_data["partitioning_options"]
            node.node_type_for_partitioning_options = node_data["node_type_for_partitioning_options"]
            node.recursive_relationship_roles = node_data["recursive_relationship_roles"]
            node.entity1 = node_map[node_data["entity1"]]
            node.entity2 = node_map[node_data["entity2"]]
            node.rel_dict = node_data["rel_dict"]
            node.node_tables = set(tuple(lst) for lst in node_data["node_tables"])
            node.select_all_tables = set(tuple(lst) for lst in node_data["select_all_tables"])
            node.select_all_nodes = node_data["select_all_nodes"]
            node.select_all_attributes_count = node_data["select_all_attributes_count"]
            node.is_mvds = node_data["is_mvds"]
            node.attribute_list = node_data["attribute_list"]
            node.insert_frequency = node_data["insert_frequency"]
            node.workload_select_frequency = node_data["workload_select_frequency"]
            node.workload_insert_frequency = node_data["workload_insert_frequency"]
            node.relation_size = node_data["relation_size"]
            node.temp_attributes = node_data["attributes"]
            node.mapped_tables_list = node_data["mapped_tables_list"]

        elif type == "ATTRIBUTE":
            node = Attribute(
                name=node_data["name"],
                unique_name=node_data["unique_name"],
                attr_type = node_data["attr_type"]
            )
            if node_data["is_multivalued"]:
                table_key = convert_nested_lists(node_data["key"]["table_key"])
                reference_key = convert_nested_lists(node_data["key"]["reference_key"])
                reference_table = convert_nested_lists(node_data["key"]["reference_table"])
                reference_node = convert_nested_lists(node_data["key"]["reference_node"])
                node.key = Key(table_key, reference_key, reference_table, reference_node)
                node.mapped_table = tuple(node_data.get("mapped_table")) if node_data.get("mapped_table") is not None else None
                node.relation_size = node_data["relation_size"]
            node.sort_key = node_data["sort_key"]
            node.partitioning_options = node_data["partitioning_options"]
            node.node_type_for_partitioning_options = node_data["node_type_for_partitioning_options"]
            node.is_multivalued = node_data["is_multivalued"]
            node.is_composite = node_data["is_composite"]
            node.is_primary_key = node_data["is_primary_key"]
            node.is_discriminator = node_data["is_discriminator"]
            node.is_flattened = node_data["is_flattened"]
            node.is_in_separate_table = node_data["is_in_separate_table"]
            node.entity = node_map[node_data["entity"]]
            node.parent_attribute = node_map.get(node_data.get("parent_attribute"))
            node.attr_dict = node_data["attr_dict"]
            node.temp_children = node_data["children"]
            node.temp_attributes = node_data["attributes"]
            node.workload_insert_frequency = node_data["workload_insert_frequency"]
            node.relation_size = node_data["relation_size"]

        graph.add_node(node)
        node_map[node.unique_name] = node

    for node in graph.nodes:
        if isinstance(node, Entity) or isinstance(node, Attribute):
            node.children = [node_map.get(unique_name) for unique_name in node.temp_children]
            node.attributes = [node_map.get(unique_name) for unique_name in node.temp_attributes]
            node.temp_children =None
            node.temp_attributes =None
        elif isinstance(node, Relationship):
            node.attributes = [node_map.get(unique_name) for unique_name in node.temp_attributes]
            node.temp_attributes =None

    for edge_data in data["edges"]:
        source = node_map[edge_data["source"]]
        target = node_map[edge_data["target"]]
        edge = Edge(
            EdgeType[edge_data["edge_type"]],
            source,
            target
        )
        graph.add_edge(edge)

    graph.config = data["config"]
    graph.cost = data["cost"]
    graph.nodes_cost = data["nodes_cost"]

    return graph

