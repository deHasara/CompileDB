#this is after db initialization
#generate data for inserts in query workload - workload_insert_frequency
#these insert tuples are not inserted at db initialization - after db initialization and later when executing workload

import json
import logging
import random
from faker import Faker
from attribute_distributions import resolve_attribute_distribution, sample_distribution
from er_graph import Graph, Node
from analyze_query_workload import propagate_cardinality_for_inheritance_hierarchy

random.seed(1)
Faker.seed(1)

#insert queries

fake = Faker("en_US")
fake.seed_instance(1)

# Mapping of variable names to Faker methods
variable_to_faker = {
    'name': fake.name,
    'firstname': fake.first_name,
    'lastname': fake.last_name,
    'email': fake.email,
    'street': fake.street_address,
    'city': fake.city,
    'company': fake.company,
    'phone_numbers': fake.phone_number,
    'birth_date': fake.date_of_birth,
    # Add more mappings as needed
}

def convert_to_tuple(obj):
    if isinstance(obj, list):
        return tuple(convert_to_tuple(x) for x in obj)
    else:
        return obj

# Example: generate fake data
def generate_fake_data_for(variable_name):
    if variable_name in variable_to_faker:
        return variable_to_faker[variable_name]()
    else:
        return fake.word()#fake.catch_phrase()

def get_attribute_domain(data, node_data, attribute, name):
    return resolve_attribute_distribution(data, node_data, attribute, name)

def generate_attribute_value(attribute_domain, attribute_type, fallback_name):
    if attribute_domain is not None:
        return sample_distribution(attribute_domain, attribute_type, rng=random, faker=fake)
    if attribute_type in ("INTEGER", "INT"):
        return random.randint(1, 1000)
    return generate_fake_data_for(fallback_name)

def check_if_relationship_is_1_N(node):
    if node.rel_dict['entity1']['one'] and not node.rel_dict['entity2']['one']:
        return node.entity2.unique_name, node.entity1.unique_name
    elif not node.rel_dict['entity1']['one'] and node.rel_dict['entity2']['one']:
        return node.entity1.unique_name, node.entity2.unique_name
    else:#False for M:N relationship
        return False

def create_composite_type(attribute_info, attribute_value):
    for sub_attribute in attribute_info["sub_attributes"]:
        if sub_attribute["type"] == "composite":
            attribute_list = []
            attribute_value.append(create_composite_type(sub_attribute, attribute_list))
        elif sub_attribute["type"] == "INTEGER":
            attribute_value.append(random.randint(1,1000))
        elif sub_attribute["type"] == "VARCHAR":
            attribute_value.append(generate_fake_data_for(sub_attribute["name"]))
    return attribute_value

def stringify_as_tuple(data):
    def helper(d):
        if isinstance(d, list):
            inner = ', '.join(helper(item) for item in d)
            return f'[{inner}]'  # keep internal lists as lists
        elif isinstance(d, tuple):
            inner = ', '.join(helper(item) for item in d)
            return f'({inner})'
        else:
            if d is None:
                return "NULL"
            # Quote and SQL-escape strings.
            return f"'{d.replace(chr(39), chr(39) * 2)}'" if isinstance(d, str) else str(d)

    # Regardless of original structure, wrap final result in ( )
    if isinstance(data, (list, tuple)):
        inner = ', '.join(helper(item) for item in data)
        return f'({inner})'
    else:
        return f'({helper(data)})'

#these insert tuples are not inserted at db initialization - after db initialization and later when executing workload
#these data is not generated for db initialization - node relation size not incremented - update to relation_size is done after executing full query workload
def generate_insert_query_workload_data_entity(graph, node, load_file, workload_insert_frequency, workload_insert_file):#strong entity

    with open(load_file, "r") as f:
        data = json.load(f)

    node_name = node.unique_name
    node_data = data.get("node_data").get(node_name)

    node_generated_data_list = []
    pks = set()

    for attr in node.attribute_list:
        name = attr["pk_name" if "pk_name" in attr else "name"]
        if "pk_name" in attr:
            pks.add(name)

    if node.is_subclass:
        root = graph.get_node_by_sort_key(node.root_sort_key)
        starting_tuple_no = root.starting_tuple_no
        root.starting_tuple_no += workload_insert_frequency
    else:
        starting_tuple_no = node.starting_tuple_no

    for i in range(starting_tuple_no, starting_tuple_no+workload_insert_frequency):
        tuple_info = {}
        tuple_values= []
        for attribute in node.attribute_list:
            name = attribute["pk_name" if "pk_name" in attribute else "name"]
            attribute_domain = get_attribute_domain(data, node_data, attribute, name)
            if "pk_name" in attribute:
                tuple_info[name] = i#strong entity, single pk
            else:
                if attribute.get("type")=="COMPOSITE":
                    attribute_value = []
                    tuple_info[name] = convert_to_tuple(create_composite_type(attribute, attribute_value))
                elif attribute.get("type")=="INTEGER" or attribute.get("type")=="INT":
                    tuple_info[name] = generate_attribute_value(attribute_domain, attribute.get("type"), name)
                elif attribute.get("type")=="VARCHAR" and not attribute.get("is_multivalued"):
                    tuple_info[name] = generate_attribute_value(attribute_domain, attribute.get("type"), attribute["name"])
                elif attribute.get("type")=="VARCHAR" and attribute.get("is_multivalued"):
                    attribute_data = data.get("node_data").get(attribute.get("entity_unique_name"))#when mvd comes from parent, require this - for subclasses
                    avg_count = attribute_data.get("avg_"+name)
                    #tuple_info[name] = [generate_fake_data_for(attribute["name"]) for _ in range(random.randint(1,avg_count * 2))]
                    tuple_info[name] = []#create mvds without duplicate values - duplicates become an issue when defining pks when mvd in separate table
                    count = random.randint(1,avg_count * 2)
                    inserted_count = 0
                    while inserted_count < count:
                        value = generate_attribute_value(attribute_domain, attribute.get("type"), attribute["name"])
                        if value not in tuple_info[name]:
                            tuple_info[name].append(value)
                            inserted_count += 1
                    attribute_node = graph.get_node_by_name(attribute["unique_name"])
                    attribute_node.workload_insert_frequency += len(tuple_info[name])#if attribute_node belongs to a parent subclass, each child subclass may increase attribute's
                    #workload_insert_frequency
            tuple_values.append(tuple_info[name])
        #tuple_with_pks_only = {k: tuple_info[k] for k in pks}
        #node_generated_data_list.append(tuple_with_pks_only)
        values_str = stringify_as_tuple(tuple_values)
        sql_statement = f"INSERT INTO {node_name.capitalize()} VALUES {values_str};"
        workload_insert_file.write(sql_statement + "\n")

    node.starting_tuple_no += workload_insert_frequency
    #return node_generated_data_list

#these insert tuples are not inserted at db initialization - after db initialization and later when executing workload
#new tuples generated shouldn't be in existing tuple set generated for weak entity for db initialization
def generate_insert_query_workload_data_weak_entity(graph, node, load_file, parent_generated_data_list, weak_entity_existing_tuples_pks_for_db_initialization,
                                                    workload_insert_frequency, workload_insert_file):
    with open(load_file, "r") as f:
        data = json.load(f)
    node_name = node.unique_name
    node_data = data.get("node_data").get(node_name)

    node_generated_data_list = []
    existing_tuples_pks = weak_entity_existing_tuples_pks_for_db_initialization.copy()
    pks = set()
    mvd_attrs = []

    for attr in node.attribute_list:
        name = attr["pk_name" if "pk_name" in attr else "name"]
        if "pk_name" in attr:
            pks.add(name)
        elif "name" in attr and attr.get("is_multivalued"):
            mvd_attrs.append((attr["unique_name"], attr["name"]))#get mvd attr unique name, name for all mvd attrs

    starting_tuple_no = node.starting_tuple_no

    for i in range(starting_tuple_no, starting_tuple_no+workload_insert_frequency):
        while True:
            tuple_info = {}
            tuple_values= []
            random_parent_tuple = random.choice(parent_generated_data_list)
            for attribute in node.attribute_list:
                name = attribute["pk_name" if "pk_name" in attribute else "name"]
                attribute_domain = get_attribute_domain(data, node_data, attribute, name)
                if "pk_name" in attribute:
                    #pks.add(name)
                    pk_entity_name = attribute.get("pk_entity_name")
                    assert pk_entity_name is not None
                    if pk_entity_name == node.parent_entity.unique_name:#pks from parent
                        if name not in random_parent_tuple:#this can happen when tuple is from a child entity - primary key is child_name_id - so parent_name_id is not found
                            #e.g. Person and Weak entity Dependent - Person tuple coming from Student entity - person_id not found but student_id
                            id_keys = [k for k in random_parent_tuple if k.endswith("_id")]
                            assert len(id_keys) == 1#assumption - only primary key ends in _id in entity values
                            tuple_info[name] = random_parent_tuple[id_keys[0]]
                        else:#tuple from the parent itself - this is when parent entity of weak entity doesn't belong to any inheritance hierarchy
                            tuple_info[name] = random_parent_tuple[name]
                    elif pk_entity_name == node_name:#discriminator attributes from node
                        if attribute.get("pk_type") in ("INTEGER", "INT", "VARCHAR"):
                            tuple_info[name] = generate_attribute_value(attribute_domain, attribute.get("pk_type"), attribute["pk_name"])
                else:
                    if attribute.get("type")=="COMPOSITE":
                        attribute_value = []
                        tuple_info[name] = convert_to_tuple(create_composite_type(attribute, attribute_value))
                    elif attribute.get("type")=="INTEGER" or attribute.get("type")=="INT":
                        tuple_info[name] = generate_attribute_value(attribute_domain, attribute.get("type"), name)
                    elif attribute.get("type")=="VARCHAR" and not attribute.get("is_multivalued"):
                        tuple_info[name] = generate_attribute_value(attribute_domain, attribute.get("type"), attribute["name"])
                    elif attribute.get("type")=="VARCHAR" and attribute.get("is_multivalued"):
                        avg_count = node_data.get("avg_"+name)
                        tuple_info[name] = []
                        count = random.randint(1,avg_count * 2)
                        inserted_count = 0
                        while inserted_count < count:
                            value = generate_attribute_value(attribute_domain, attribute.get("type"), attribute["name"])
                            if value not in tuple_info[name]:
                                tuple_info[name].append(value)
                                inserted_count += 1
                        #attribute_node = graph.get_node_by_name(attribute["unique_name"])
                        #attribute_node.workload_insert_frequency += len(tuple_info[name]) #it should not be updated here - since duplicate tuple might get generated
                tuple_values.append(tuple_info[name])

            tuple_with_pks_only = {k: tuple_info[k] for k in pks}
            if tuple_with_pks_only not in existing_tuples_pks:
                #node_generated_data_list.append(tuple_info)
                existing_tuples_pks.append(tuple_with_pks_only)
                for mvd_attribute_unique_name, mvd_attribute_name in mvd_attrs:
                    attribute_node = graph.get_node_by_name(mvd_attribute_unique_name)
                    attribute_node.workload_insert_frequency += len(tuple_info[mvd_attribute_name])#mvd workload_insert_frequency should be updated only if new tuple doesn't exist in already generated
                    #and gets added
                values_str = stringify_as_tuple(tuple_values)
                sql_statement = f"INSERT INTO {node_name.capitalize()} VALUES {values_str};"
                workload_insert_file.write(sql_statement + "\n")
                break

    node.starting_tuple_no += workload_insert_frequency
    #return node_generated_data_list

#tuples from many side that participate in relationship for db initialization - side_N_entity_participating_data_list
def generate_insert_query_workload_data_relationship(graph, node, load_file, side_N_entity_unique_name,
                                                     side_N_generated_data_list, side_N_entity_participating_data_list,
                                                     side_1_entity_unique_name, side_1_entity_generated_data_list,
                                                     workload_insert_frequency, workload_insert_file):
    with open(load_file, "r") as f:
        data = json.load(f)
    node_name = node.unique_name
    node_data = data.get("node_data").get(node_name)

    node_generated_data_list = []

    # total number of tuples to select from many side should be less than or equal to many side tuples which were not used for relationship initialization at db
    #initialization
    #many side tuple can participate in relationship at most once
    assert workload_insert_frequency <= (len(side_N_generated_data_list) - len(side_N_entity_participating_data_list))

    for i in range(workload_insert_frequency):
        while True:
            value_list = random.choice(side_N_generated_data_list)#random many side tuple - many side tuple can participate at most once in relationship
            if value_list not in side_N_entity_participating_data_list:#if selected random tuple doesn't participate in db initialization,
                #and not already selected for an insert workload tuple can use as a insert workload tuple
                side_N_entity_participating_data_list.append(value_list)#pick the value_list and add to participating list, so that it is not chosen again
                break

        tuple_info = {}
        tuple_values= []

        if node.entity1.unique_name == node.entity2.unique_name:#handle data selection for recursive relationship
            #choice_pool = [v for v in side_1_entity_generated_data_list if v != value_list]#too time consuming to build the entire pool filtering - and then randomly choose

            #Instead of building the entire choice pool - get a single sample randomly in choice pool - then stop building the choice pool
            choice_pool = []
            while True:
                random_index = random.randint(0, len(side_1_entity_generated_data_list) - 1)#sampling with replacement
                if value_list != side_1_entity_generated_data_list[random_index]:
                    choice_pool.append(side_1_entity_generated_data_list[random_index])
                    break#found single sample - stop building choice pool
                else:
                    continue
        else:
            choice_pool = side_1_entity_generated_data_list

        if choice_pool:
            random_1_side_tuple = random.choice(choice_pool)

        for attribute in node.attribute_list:
            name = attribute["pk_reference_key_name" if "pk_reference_key_name" in attribute else "name"]
            attribute_domain = get_attribute_domain(data, node_data, attribute, name)
            if "pk_reference_key_name" in attribute:
                pk_entity_name = attribute.get("pk_entity_name")
                assert pk_entity_name is not None
                pk_name = attribute.get("pk_name")
                if side_N_entity_unique_name == side_1_entity_unique_name:#recursive relationship
                    entity_num = None
                    for i in range(len(node.key.table_key)):
                        for j in range(len(node.key.table_key[i])):
                            if node.key.table_key[i][j][0] == pk_name:
                                entity_num = i
                                break
                        if entity_num is not None:
                            break
                    if entity_num==0:
                        if name not in value_list:#this can happen when tuple is from a child entity - primary key is child_name_id - so parent_name_id is not found
                            id_keys = [k for k in value_list if k.endswith("_id")]
                            assert len(id_keys) == 1#assumption - only primary key ends in _id in entity values
                            tuple_info[pk_name] = value_list[id_keys[0]]
                        else:#tuple from the participating entity itself - this is when entity of relationship doesn't belong to any inheritance hierarchy
                            tuple_info[pk_name] = value_list.get(name)
                    elif entity_num==1:
                        if name not in random_1_side_tuple:#this can happen when tuple is from a child entity - primary key is child_name_id - so parent_name_id is not found
                            id_keys = [k for k in random_1_side_tuple if k.endswith("_id")]
                            assert len(id_keys) == 1#assumption - only primary key ends in _id in entity values
                            tuple_info[pk_name] = random_1_side_tuple[id_keys[0]]
                        else:#tuple from the participating entity itself - this is when entity of relationship doesn't belong to any inheritance hierarchy
                            tuple_info[pk_name] = random_1_side_tuple.get(name)
                    tuple_values.append(tuple_info[pk_name])
                else:
                    if pk_entity_name == side_N_entity_unique_name:#many side for 1:N relationship - pk
                        if name not in value_list:#this can happen when tuple is from a child entity - primary key is child_name_id - so parent_name_id is not found
                            id_keys = [k for k in value_list if k.endswith("_id")]
                            assert len(id_keys) == 1#assumption - only primary key ends in _id in entity values
                            tuple_info[pk_name] = value_list[id_keys[0]]
                        else:#tuple from the participating entity itself - this is when entity of relationship doesn't belong to any inheritance hierarchy
                            tuple_info[pk_name] = value_list.get(name)
                    else:#1 side
                        if name not in random_1_side_tuple:#this can happen when tuple is from a child entity - primary key is child_name_id - so parent_name_id is not found
                            id_keys = [k for k in random_1_side_tuple if k.endswith("_id")]
                            assert len(id_keys) == 1#assumption - only primary key ends in _id in entity values
                            tuple_info[pk_name] = random_1_side_tuple[id_keys[0]]
                        else:#tuple from the participating entity itself - this is when entity of relationship doesn't belong to any inheritance hierarchy
                            tuple_info[pk_name] = random_1_side_tuple[name]
                    tuple_values.append(tuple_info[pk_name])
            else:
                if attribute.get("type")=="COMPOSITE":
                    attribute_value = []
                    tuple_info[name] = convert_to_tuple(create_composite_type(attribute, attribute_value))
                elif attribute.get("type")=="INTEGER" or attribute.get("type")=="INT":
                    tuple_info[name] = generate_attribute_value(attribute_domain, attribute.get("type"), name)
                elif attribute.get("type")=="VARCHAR" and not attribute.get("is_multivalued"):
                    tuple_info[name] = generate_attribute_value(attribute_domain, attribute.get("type"), attribute["name"])
                elif attribute.get("type")=="VARCHAR" and attribute.get("is_multivalued"):
                    avg_count = node_data.get("avg_"+name)
                    tuple_info[name] = []
                    count = random.randint(1,avg_count * 2)
                    inserted_count = 0
                    while inserted_count < count:
                        value = generate_attribute_value(attribute_domain, attribute.get("type"), attribute["name"])
                        if value not in tuple_info[name]:
                            tuple_info[name].append(value)
                            inserted_count += 1
                    attribute_node = graph.get_node_by_name(attribute["unique_name"])
                    attribute_node.workload_insert_frequency += len(tuple_info[name])
                tuple_values.append(tuple_info[name])
        #node_generated_data_list.append(tuple_info)
        values_str = stringify_as_tuple(tuple_values)
        sql_statement = f"INSERT INTO {node_name.capitalize()} VALUES {values_str};"
        workload_insert_file.write(sql_statement + "\n")
    #return node_generated_data_list

def generate_insert_query_workload_data_relationship_M_N(graph, node, load_file, entity1_unique_name, entity1_generated_data_list, entity2_unique_name, entity2_generated_data_list,
                                                         tuple_pks_generated_for_relationship_for_db_initialization,
                                                         workload_insert_frequency, workload_insert_file):

    with open(load_file, "r") as f:
        data = json.load(f)
    node_name = node.unique_name

    node_data = data.get("node_data").get(node_name)
    node_generated_data_list = []
    node_relation_size = 0

    existing_tuples_pks = tuple_pks_generated_for_relationship_for_db_initialization.copy()
    pks = set()
    mvd_attrs = []

    for attribute in node.attribute_list:#get pks and mvd attrs
        if "pk_name" in attribute:#get pks
            pk_name = attribute.get("pk_name")
            pks.add(pk_name)
        elif "name" in attribute and attribute.get("is_multivalued"):
            mvd_attrs.append((attribute["unique_name"], attribute["name"]))#get mvd attr unique name, name for all mvd attrs

    for i in range(workload_insert_frequency):
        while True:
            tuple_info = {}
            tuple_values= []
            #random_entity1_tuple
            entity1_value_list = random.choice(entity1_generated_data_list)
            #random_entity2_tuple
            if node.entity1.unique_name == node.entity2.unique_name:#recursive relationship
                while True:
                    entity2_value_list = random.choice(entity2_generated_data_list)
                    if entity1_value_list != entity2_value_list:
                        break
                    else:
                        continue
            else:
                entity2_value_list = random.choice(entity2_generated_data_list)

            for attribute in node.attribute_list:
                name = attribute["pk_reference_key_name" if "pk_reference_key_name" in attribute else "name"]
                attribute_domain = get_attribute_domain(data, node_data, attribute, name)
                if "pk_reference_key_name" in attribute:
                    pk_entity_name = attribute.get("pk_entity_name")
                    assert pk_entity_name is not None
                    pk_name = attribute.get("pk_name")
                    if entity1_unique_name == entity2_unique_name:#recursive relationship
                        entity_num = None
                        for i in range(len(node.key.table_key)):
                            for j in range(len(node.key.table_key[i])):
                                if node.key.table_key[i][j][0] == pk_name:
                                    entity_num = i
                                    break
                            if entity_num is not None:
                                break
                        if entity_num==0:
                            if name not in entity1_value_list:#this can happen when tuple is from a child entity - primary key is child_name_id - so parent_name_id is not found
                                id_keys = [k for k in entity1_value_list if k.endswith("_id")]
                                assert len(id_keys) == 1#assumption - only primary key ends in _id in entity values
                                tuple_info[pk_name] = entity1_value_list[id_keys[0]]
                            else:#tuple from the participating entity itself - this is when entity of relationship doesn't belong to any inheritance hierarchy
                                tuple_info[pk_name] = entity1_value_list.get(name)
                        elif entity_num==1:
                            if name not in entity2_value_list:#this can happen when tuple is from a child entity - primary key is child_name_id - so parent_name_id is not found
                                id_keys = [k for k in entity2_value_list if k.endswith("_id")]
                                assert len(id_keys) == 1#assumption - only primary key ends in _id in entity values
                                tuple_info[pk_name] = entity2_value_list[id_keys[0]]
                            else:#tuple from the participating entity itself - this is when entity of relationship doesn't belong to any inheritance hierarchy
                                tuple_info[pk_name] = entity2_value_list.get(name)
                        tuple_values.append(tuple_info[pk_name])
                    else:
                        if pk_entity_name == entity1_unique_name:
                            if name not in entity1_value_list:#this can happen when tuple is from a child entity - primary key is child_name_id - so parent_name_id is not found
                                id_keys = [k for k in entity1_value_list if k.endswith("_id")]
                                assert len(id_keys) == 1#assumption - only primary key ends in _id in entity values
                                tuple_info[pk_name] = entity1_value_list[id_keys[0]]
                            else:#tuple from the participating entity itself - this is when entity of relationship doesn't belong to any inheritance hierarchy
                                tuple_info[pk_name] = entity1_value_list.get(name)
                        elif pk_entity_name == entity2_unique_name:
                            if name not in entity2_value_list:#this can happen when tuple is from a child entity - primary key is child_name_id - so parent_name_id is not found
                                id_keys = [k for k in entity2_value_list if k.endswith("_id")]
                                assert len(id_keys) == 1#assumption - only primary key ends in _id in entity values
                                tuple_info[pk_name] = entity2_value_list[id_keys[0]]
                            else:#tuple from the participating entity itself - this is when entity of relationship doesn't belong to any inheritance hierarchy
                                tuple_info[pk_name] = entity2_value_list.get(name)
                        tuple_values.append(tuple_info[pk_name])
                else:
                    if attribute.get("type")=="COMPOSITE":
                        attribute_value = []
                        tuple_info[name] = convert_to_tuple(create_composite_type(attribute, attribute_value))
                    elif attribute.get("type")=="INTEGER" or attribute.get("type")=="INT":
                        tuple_info[name] = generate_attribute_value(attribute_domain, attribute.get("type"), name)
                    elif attribute.get("type")=="VARCHAR" and not attribute.get("is_multivalued"):
                        tuple_info[name] = generate_attribute_value(attribute_domain, attribute.get("type"), attribute["name"])
                    elif attribute.get("type")=="VARCHAR" and attribute.get("is_multivalued"):
                        avg_count = node_data.get("avg_"+name)
                        tuple_info[name] = []
                        count = random.randint(1,avg_count * 2)
                        inserted_count = 0
                        while inserted_count < count:
                            value = generate_attribute_value(attribute_domain, attribute.get("type"), attribute["name"])
                            if value not in tuple_info[name]:
                                tuple_info[name].append(value)
                                inserted_count += 1
                        #attribute_node = graph.get_node_by_name(attribute["unique_name"])
                        #attribute_node.workload_insert_frequency += len(tuple_info[name])#it should not be updated here - since duplicate tuple might get generated
                    tuple_values.append(tuple_info[name])
            if tuple(tuple_info[name] for name in pks) not in existing_tuples_pks:
                #node_generated_data_list.append(tuple_info)
                existing_tuples_pks.add(tuple(tuple_info[name] for name in pks))
                for mvd_attribute_unique_name, mvd_attribute_name in mvd_attrs:
                    attribute_node = graph.get_node_by_name(mvd_attribute_unique_name)
                    attribute_node.workload_insert_frequency += len(tuple_info[mvd_attribute_name])#mvd workload_insert_frequency should be updated only if new tuple doesn't exist in already generated
                    #and gets added
                values_str = stringify_as_tuple(tuple_values)
                sql_statement = f"INSERT INTO {node_name.capitalize()} VALUES {values_str};"
                workload_insert_file.write(sql_statement + "\n")
                break
