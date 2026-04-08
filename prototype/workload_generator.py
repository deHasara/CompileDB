import json
import logging
import random
from faker import Faker
from er_graph import Graph, Node
from analyze_query_workload import propagate_cardinality_for_inheritance_hierarchy
from workload_generator_helper import (generate_insert_query_workload_data_entity, generate_insert_query_workload_data_weak_entity,
                                       generate_insert_query_workload_data_relationship,generate_insert_query_workload_data_relationship_M_N)
from workload_generator_stat_only import generate_test_stat_data
random.seed(1)

#insert queries for db initialization

fake = Faker()

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
            # Quote strings
            return f"'{d}'" if isinstance(d, str) else str(d)

    # Regardless of original structure, wrap final result in ( )
    if isinstance(data, (list, tuple)):
        inner = ', '.join(helper(item) for item in data)
        return f'({inner})'
    else:
        return f'({helper(data)})'

def generate_data_entity(graph, node, load_file, insert_file):#strong entity
    with open(load_file, "r") as f:
        data = json.load(f)

    node_name = node.unique_name
    node_data = data.get("node_data").get(node_name)
    node_count = node_data.get("node_count")
    node.relation_size = node_count
    node.strict_relation_size = node_count
    node.insert_frequency = node_count
    node_generated_data_list = []
    pks = set()

    for attr in node.attribute_list:
        name = attr["pk_name" if "pk_name" in attr else "name"]
        if "pk_name" in attr:
            pks.add(name)

    if node.is_subclass:
        root = graph.get_node_by_sort_key(node.root_sort_key)
        starting_tuple_no = root.starting_tuple_no
        root.starting_tuple_no += node_count
    else:
        starting_tuple_no = node.starting_tuple_no

    for i in range(starting_tuple_no, starting_tuple_no+node_count):
        tuple_info = {}
        tuple_values= []
        for attribute in node.attribute_list:
            name = attribute["pk_name" if "pk_name" in attribute else "name"]
            attribute_domain = node_data.get("attribute_domains").get(name) if (node_data and node_data.get("attribute_domains")) else None
            if "pk_name" in attribute:
                tuple_info[name] = i#strong entity, single pk
            else:
                if attribute.get("type")=="COMPOSITE":
                    attribute_value = []
                    tuple_info[name] = convert_to_tuple(create_composite_type(attribute, attribute_value))
                elif attribute.get("type")=="INTEGER" or attribute.get("type")=="INT":
                    if attribute_domain:
                        tuple_info[name] = random.randint(attribute_domain[0],attribute_domain[1])
                    else:
                        tuple_info[name] = random.randint(1,1000)
                elif attribute.get("type")=="VARCHAR" and not attribute.get("is_multivalued"):
                    if attribute_domain:
                        tuple_info[name] = random.choice(attribute_domain)
                    else:
                        tuple_info[name] = generate_fake_data_for(attribute["name"])
                elif attribute.get("type")=="VARCHAR" and attribute.get("is_multivalued"):
                    attribute_data = data.get("node_data").get(attribute.get("entity_unique_name"))#when mvd comes from parent, require this - for subclasses
                    avg_count = attribute_data.get("avg_"+name)
                    #tuple_info[name] = [generate_fake_data_for(attribute["name"]) for _ in range(random.randint(1,avg_count * 2))]
                    tuple_info[name] = []#create mvds without duplicate values - duplicates become an issue when defining pks when mvd in separate table
                    count = random.randint(1,avg_count * 2)
                    inserted_count = 0
                    while inserted_count < count:
                        value = generate_fake_data_for(attribute["name"])
                        if value not in tuple_info[name]:
                            tuple_info[name].append(value)
                            inserted_count += 1
                    attribute_node = graph.get_node_by_name(attribute["unique_name"])
                    attribute_node.relation_size += len(tuple_info[name])
            tuple_values.append(tuple_info[name])
        #node_generated_data_list.append(tuple_info)
        tuple_with_pks_only = {k: tuple_info[k] for k in pks}#filtered non-pk attributes since only pks required to select a tuple to be a participating tuple
                                                                            #for weak entity/relationship - to save memory when dataset scales
        node_generated_data_list.append(tuple_with_pks_only)
        values_str = stringify_as_tuple(tuple_values)
        sql_statement = f"INSERT INTO {node_name.capitalize()} VALUES {values_str};"
        insert_file.write(sql_statement + "\n")

    node.starting_tuple_no += node_count
    return node_generated_data_list

def generate_data_weak_entity(graph, node, load_file, parent_generated_data_list, insert_file):
    with open(load_file, "r") as f:
        data = json.load(f)
    node_name = node.unique_name
    node_data = data.get("node_data").get(node_name)
    node_count = node_data.get("node_count")
    node.relation_size = node_count
    node.insert_frequency = node_count
    node_generated_data_list = []
    existing_tuples_pks = set()
    pks = set()
    mvd_attrs = []

    for attr in node.attribute_list:
        name = attr["pk_name" if "pk_name" in attr else "name"]
        if "pk_name" in attr:
            pks.add(name)#get pks
        elif "name" in attr and attr.get("is_multivalued"):
            mvd_attrs.append((attr["unique_name"], attr["name"]))#get mvd attr unique name, name for all mvd attrs

    starting_tuple_no = node.starting_tuple_no

    for i in range(starting_tuple_no, starting_tuple_no+node_count):
        while True:
            tuple_info = {}
            tuple_values= []
            random_parent_tuple = random.choice(parent_generated_data_list)
            for attribute in node.attribute_list:
                name = attribute["pk_name" if "pk_name" in attribute else "name"]
                attribute_domain = node_data.get("attribute_domains").get(name) if (node_data and  node_data.get("attribute_domains")) else None
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
                        if attribute.get("pk_type")=="INTEGER":
                            if attribute_domain:
                                tuple_info[name] = random.randint(attribute_domain[0],attribute_domain[1])
                            else:
                                tuple_info[name] = random.randint(1,1000)
                        elif attribute.get("pk_type")=="VARCHAR":
                            if attribute_domain:
                                tuple_info[name] = random.choice(attribute_domain)
                            else:
                                tuple_info[name] = generate_fake_data_for(attribute["pk_name"])
                else:
                    if attribute.get("type")=="COMPOSITE":
                        attribute_value = []
                        tuple_info[name] = convert_to_tuple(create_composite_type(attribute, attribute_value))
                    elif attribute.get("type")=="INTEGER" or attribute.get("type")=="INT":
                        if attribute_domain:
                            tuple_info[name] = random.randint(attribute_domain[0],attribute_domain[1])
                        else:
                            tuple_info[name] = random.randint(1,1000)
                    elif attribute.get("type")=="VARCHAR" and not attribute.get("is_multivalued"):
                        if attribute_domain:
                            tuple_info[name] = random.choice(attribute_domain)
                        else:
                            tuple_info[name] = generate_fake_data_for(attribute["name"])
                    elif attribute.get("type")=="VARCHAR" and attribute.get("is_multivalued"):
                        avg_count = node_data.get("avg_"+name)
                        tuple_info[name] = []
                        count = random.randint(1,avg_count * 2)
                        inserted_count = 0
                        while inserted_count < count:
                            value = generate_fake_data_for(attribute["name"])
                            if value not in tuple_info[name]:
                                tuple_info[name].append(value)
                                inserted_count += 1
                        #attribute_node = graph.get_node_by_name(attribute["unique_name"])
                        #attribute_node.relation_size += len(tuple_info[name]) #it should not be updated here - since duplicate tuple might get generated
                tuple_values.append(tuple_info[name])

            if tuple(tuple_info[name] for name in pks) not in existing_tuples_pks:
                #node_generated_data_list.append(tuple_info)
                tuple_with_pks_only = {k: tuple_info[k] for k in pks}#filtered non-pk attributes since only pks required to select a tuple to be a participating tuple
                                                                #for weak entity/relationship - to save memory when dataset scales
                node_generated_data_list.append(tuple_with_pks_only)
                existing_tuples_pks.add(tuple(tuple_info[name] for name in pks))
                for mvd_attribute_unique_name, mvd_attribute_name in mvd_attrs:
                    attribute_node = graph.get_node_by_name(mvd_attribute_unique_name)
                    attribute_node.relation_size += len(tuple_info[mvd_attribute_name])#mvd relation size should be updated only if new tuple doesn't exist in already generated
                                                                                       #and gets added
                values_str = stringify_as_tuple(tuple_values)
                sql_statement = f"INSERT INTO {node_name.capitalize()} VALUES {values_str};"
                insert_file.write(sql_statement + "\n")
                break

    node.starting_tuple_no += node_count
    return node_generated_data_list

def generate_data_relationship(graph, node, load_file, side_N_entity_unique_name, side_N_entity_generated_data_list,
                               side_1_entity_unique_name, side_1_entity_generated_data_list, insert_file):
    with open(load_file, "r") as f:
        data = json.load(f)
    node_name = node.unique_name
    node_data = data.get("node_data").get(node_name)
    participation_factor = node_data.get("participation_factor", 1)#factor of participation - is 1 if total participation - defaults to total participation if factor not given in node_data
    node_generated_data_list = []
    # total number of tuples to select from many side
    k = round(len(side_N_entity_generated_data_list) * participation_factor)
    # choose k tuples from many side uniformly without replacement
    selected_side_N_entity_tuples = random.sample(side_N_entity_generated_data_list, k)
    node.relation_size = k
    node.insert_frequency = k
    for value_list in selected_side_N_entity_tuples:
        tuple_info = {}
        tuple_values= []

        #if side_N_entity_generated_data_list is side_1_entity_generated_data_list:#handle data selection for recursive relationship
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
            attribute_domain = node_data.get("attribute_domains").get(name) if (node_data and  node_data.get("attribute_domains")) else None
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
                    if attribute_domain:
                        tuple_info[name] = random.randint(attribute_domain[0],attribute_domain[1])
                    else:
                        tuple_info[name] = random.randint(1,1000)
                elif attribute.get("type")=="VARCHAR" and not attribute.get("is_multivalued"):
                    if attribute_domain:
                        tuple_info[name] = random.choice(attribute_domain)
                    else:
                        tuple_info[name] = generate_fake_data_for(attribute["name"])
                elif attribute.get("type")=="VARCHAR" and attribute.get("is_multivalued"):
                    avg_count = node_data.get("avg_"+name)
                    tuple_info[name] = []
                    count = random.randint(1,avg_count * 2)
                    inserted_count = 0
                    while inserted_count < count:
                        value = generate_fake_data_for(attribute["name"])
                        if value not in tuple_info[name]:
                            tuple_info[name].append(value)
                            inserted_count += 1
                    attribute_node = graph.get_node_by_name(attribute["unique_name"])
                    attribute_node.relation_size += len(tuple_info[name])
                tuple_values.append(tuple_info[name])
        #node_generated_data_list.append(tuple_info)
        values_str = stringify_as_tuple(tuple_values)
        sql_statement = f"INSERT INTO {node_name.capitalize()} VALUES {values_str};"
        insert_file.write(sql_statement + "\n")
    #return node_generated_data_list
    return selected_side_N_entity_tuples#tracking all selected N side tuples at db initialization required when generating insert tuples for insert workload
            #a many side tuple can participte in relationship at most once - hence these tuples whch were selected for db initialization cannot be
            #used for generating insert workload tuples

def generate_data_relationship_M_N(graph, node, load_file, entity1_unique_name, entity1_generated_data_list, entity2_unique_name, entity2_generated_data_list, insert_file):

    with open(load_file, "r") as f:
        data = json.load(f)
    node_name = node.unique_name
    #node_count = data.get("node_count").get(node_name)
    node_data = data.get("node_data").get(node_name)
    participation_factor = node_data.get("participation_factor", 1)#factor of participation - is 1 if total participation - defaults to total participation if factor not given in node_data
    entity1_per_entity2_count = node_data.get(entity1_unique_name + "_to_" + entity2_unique_name)#per entity_1 tuple, on avg maps to this many entity_2 tuples - this is defined only for m:n relationships
    node_generated_data_list = []
    node_relation_size = 0
    k = round(len(entity1_generated_data_list) * participation_factor)#participation factor defined for entity1
    # choose k tuples from entity1 side uniformly without replacement
    selected_entity1_side_tuples = random.sample(entity1_generated_data_list, k)

    existing_tuples_pks = set()#tracking all generated tuples at db initialization required when generating insert tuples for insert workload
    pks = set()
    for attribute in node.attribute_list:
        if "pk_name" in attribute:
            pk_name = attribute.get("pk_name")
            pks.add(pk_name)

    #for entity1_value_list in entity1_generated_data_list:#assume total participation - entity1
    for entity1_value_list in selected_entity1_side_tuples:#modified to consider partial participation - entity1

        #if entity1_generated_data_list is entity2_generated_data_list:#recursive relationship
        if node.entity1.unique_name == node.entity2.unique_name:#handle data selection for recursive relationship
            #choice_pool = [v for v in entity2_generated_data_list if v != entity1_value_list]#too time consuming to build the entire choice pool for each entity1_value_list

            #Instead of building the entire choice pool - build upto max sample size entity1_per_entity2_count - then stop building the choice pool
            choice_pool = []
            while True:
                random_index = random.randint(0, len(entity2_generated_data_list) - 1)#sampling with replacement
                if len(choice_pool) < entity1_per_entity2_count:#max sample size is entity1_per_entity2_count
                    entity2_tuple_value_list = entity2_generated_data_list[random_index]
                    if entity1_value_list != entity2_tuple_value_list and entity2_tuple_value_list not in choice_pool:#to have unique pairs
                        choice_pool.append(entity2_tuple_value_list)
                    else:
                        continue
                else:
                    break#after max size is reached - stop building the choice pool
        else:
            choice_pool = entity2_generated_data_list
        sample_size = random.randint(1, entity1_per_entity2_count)
        if sample_size <= len(choice_pool) :
            entity2_samples = random.sample(choice_pool, sample_size)#sample uniformly without replacement
        else:
            entity2_samples = choice_pool#fallback if too few candidates

        for entity2_value_list in entity2_samples:
            tuple_info = {}
            tuple_values= []
            for attribute in node.attribute_list:
                name = attribute["pk_reference_key_name" if "pk_reference_key_name" in attribute else "name"]
                attribute_domain = node_data.get("attribute_domains").get(name) if (node_data and  node_data.get("attribute_domains")) else None
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
                        if attribute_domain:
                            tuple_info[name] = random.randint(attribute_domain[0],attribute_domain[1])
                        else:
                            tuple_info[name] = random.randint(1,1000)
                    elif attribute.get("type")=="VARCHAR" and not attribute.get("is_multivalued"):
                        if attribute_domain:
                            tuple_info[name] = random.choice(attribute_domain)
                        else:
                            tuple_info[name] = generate_fake_data_for(attribute["name"])
                    elif attribute.get("type")=="VARCHAR" and attribute.get("is_multivalued"):
                        avg_count = node_data.get("avg_"+name)
                        tuple_info[name] = []
                        count = random.randint(1,avg_count * 2)
                        inserted_count = 0
                        while inserted_count < count:
                            value = generate_fake_data_for(attribute["name"])
                            if value not in tuple_info[name]:
                                tuple_info[name].append(value)
                                inserted_count += 1
                        attribute_node = graph.get_node_by_name(attribute["unique_name"])
                        attribute_node.relation_size += len(tuple_info[name])
                    tuple_values.append(tuple_info[name])
            #node_generated_data_list.append(tuple_info)
            existing_tuples_pks.add(tuple(tuple_info[name] for name in pks))
            node_relation_size += 1
            values_str = stringify_as_tuple(tuple_values)
            sql_statement = f"INSERT INTO {node_name.capitalize()} VALUES {values_str};"
            insert_file.write(sql_statement + "\n")
    node.relation_size = node_relation_size#len(node_generated_data_list) - replaced to store count instead of all tuples - saves memory
    node.insert_frequency = node_relation_size#len(node_generated_data_list)
    #return node_generated_data_list
    return existing_tuples_pks#tracking all generated tuples at db initialization required when generating insert tuples for insert workload

def generate_select_statements_for_entity_or_relationship(entity_or_relationship_unique_name, select_frequency):
    sql_statement = f"SELECT * FROM {entity_or_relationship_unique_name};"
    return [sql_statement]*select_frequency

def update_relation_size_from_propagations_of_subclasses(graph):
    propagate_cardinality_for_inheritance_hierarchy(graph)

#For a weak entity or relationship, a tuple that gets mapped to, is randomly selected.
#when assigning parent tuples(to randomly pick from) to weak entities or relationship, if the entity is a parent in a hierarchy,
# all children tuples should be included as well(in addition to parent tuples) for random selection
#e.g. if Person has weak entity dependent, all tuples from Person, Student, Instructor should be included in the pool to which a dependent tuple is matched.
def union_tuples_of_subclasses_to_participating_parents(generated_data_dict, parent_entity, generated_data_list):
    for child_node in parent_entity.children:
        union_tuples_of_subclasses_to_participating_parents(generated_data_dict, child_node, generated_data_list)

    generated_data_list.extend(generated_data_dict[parent_entity.unique_name])

def reset_workload_file():
    empty_schema = {}

    with open("workload.json", "w") as f:
        json.dump(empty_schema, f, indent=2)

def generate_insert_data_for_db_initialization(graph, load_file):

    #generate insert data for db initializing
    generated_data_dict = {}

    many_side_participating_tuples = {}#for many-to-one relationships, a many side tuple can participte in relationship at most once -
                                #hence these tuples which were selected for db initialization cannot be
                                #used for generating insert workload tuples
    many_to_many_relationship_generated_tuples = {}#these pk combinations in tuples generated for db initialization cannot be repeated when generating tuples for insert workload

    insert_file = open("insert_db_initialization.sql", "w")#resets insert_db_initialization.sql - inserts for db initialization

    for node in graph.nodes:
        if node.is_entity() and not node.is_weak_entity:
            generated_data_dict[node.unique_name] = generate_data_entity(graph, node, load_file, insert_file)
            print(node.unique_name, "done")
        elif node.is_entity() and node.is_weak_entity:
            if len(node.parent_entity.children)>0:#need to include all tuples from entire hierarchy below parent_entity(all subclasses which are rooted by parent entity immediate and below )
                parent_generated_data_list = []
                union_tuples_of_subclasses_to_participating_parents(generated_data_dict, node.parent_entity, parent_generated_data_list)
                generated_data_dict[node.unique_name] = generate_data_weak_entity(graph, node, load_file, parent_generated_data_list, insert_file)
            else:#just include parent_entity's tuples since it doesn't have a hierarchy - only pick from entity itself for weak entity
                generated_data_dict[node.unique_name] = generate_data_weak_entity(graph, node, load_file, generated_data_dict.get(node.parent_entity.unique_name), insert_file)
            print(node.unique_name, "done")
        elif node.is_relationship():
            if check_if_relationship_is_1_N(node):
                side_N_entity_unique_name, side_1_entity_unique_name = check_if_relationship_is_1_N(node)

                side_N_entity = graph.get_node_by_name(side_N_entity_unique_name)
                side_1_entity = graph.get_node_by_name(side_1_entity_unique_name)

                if len(side_N_entity.children)>0:#need to include all tuples from all subclasses rooted from side_N_entity
                    side_N_generated_data_list = []
                    union_tuples_of_subclasses_to_participating_parents(generated_data_dict, side_N_entity, side_N_generated_data_list)
                else:#simply tuples only from entity
                    side_N_generated_data_list = generated_data_dict.get(side_N_entity_unique_name)

                if len(side_1_entity.children)>0:#need to include all tuples from all subclasses rooted from side_1_entity
                    side_1_generated_data_list = []
                    union_tuples_of_subclasses_to_participating_parents(generated_data_dict, side_1_entity, side_1_generated_data_list)
                else:#simply tuples only from entity
                    side_1_generated_data_list = generated_data_dict.get(side_1_entity_unique_name)

                many_side_participating_tuples[node.unique_name] = generate_data_relationship(graph, node, load_file, side_N_entity_unique_name,
                        side_N_generated_data_list, side_1_entity_unique_name, side_1_generated_data_list, insert_file)
                #for many-to-one relationships, a many side tuple can participte in relationship at most once - hence these tuples whch were selected
                #for db initialization cannot be used for generating insert workload tuples
            else:
                entity1_unique_name = node.entity1.unique_name
                entity2_unique_name = node.entity2.unique_name

                if len(node.entity1.children)>0:#entity1 belongs to a hierarchy - need to include all tuples from all subclasses rooted from entity_1
                    entity1_generated_data_list = []
                    union_tuples_of_subclasses_to_participating_parents(generated_data_dict, node.entity1, entity1_generated_data_list)
                else:#simply tuples only from entity
                    entity1_generated_data_list = generated_data_dict.get(entity1_unique_name)

                if len(node.entity2.children)>0:#entity2 belongs to a hierarchy - need to include all tuples from all subclasses rooted from entity_2
                    entity2_generated_data_list = []
                    union_tuples_of_subclasses_to_participating_parents(generated_data_dict, node.entity2, entity2_generated_data_list)
                else:#simply tuples only from entity
                    entity2_generated_data_list = generated_data_dict.get(entity2_unique_name)

                generated_node_tuples = generate_data_relationship_M_N(graph, node, load_file, entity1_unique_name, entity1_generated_data_list,
                                                                    entity2_unique_name, entity2_generated_data_list, insert_file)
                many_to_many_relationship_generated_tuples[node.unique_name] = generated_node_tuples

            print(node.unique_name, "done")

    insert_file.close()

    update_relation_size_from_propagations_of_subclasses(graph)#propagate relation sizes from children to parent for inheritance hierarchies

    return generated_data_dict, many_side_participating_tuples, many_to_many_relationship_generated_tuples

def generate_select_all_queries_for_query_workload(graph, load_file):
    #generate select * statements of query workload
    select_sql_statements = []
    with open(load_file, "r") as f:
        data = json.load(f)
    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            workload_select_frequency_for_node = data.get("select_all_frequencies").get(node.unique_name) if data.get("select_all_frequencies") else None
            if workload_select_frequency_for_node:
                node.workload_select_frequency += workload_select_frequency_for_node
                select_sql_statements += generate_select_statements_for_entity_or_relationship(node.unique_name, workload_select_frequency_for_node)

    return select_sql_statements

def generate_insert_queries_for_query_workload(graph, load_file, generated_data_for_db_initialization,
                                               side_N_participating_tuples, many_to_many_relationship_generated_tuples):
    #generate insert statements of query workload
    workload_insert_file =  open("insert_query_workload.sql", "w")#resets "insert_query_workload.sql"
    with open(load_file, "r") as f:
        data = json.load(f)

    for node in graph.nodes:
        if node.is_entity() or node.is_relationship():
            workload_insert_frequency_for_node = data.get("insert_frequencies").get(node.unique_name) if data.get("insert_frequencies") else None
            if workload_insert_frequency_for_node:
                node.workload_insert_frequency += workload_insert_frequency_for_node
                if node.is_entity() and not node.is_weak_entity:
                    generate_insert_query_workload_data_entity(graph, node, load_file, workload_insert_frequency_for_node, workload_insert_file)
                    #print(node.unique_name, "done")
                elif node.is_entity() and node.is_weak_entity:
                    if len(node.parent_entity.children)>0:#need to include all tuples from entire hierarchy below parent_entity(all subclasses which are rooted by parent entity immediate and below )
                        parent_generated_data_list = []
                        union_tuples_of_subclasses_to_participating_parents(generated_data_for_db_initialization, node.parent_entity, parent_generated_data_list)
                        generate_insert_query_workload_data_weak_entity(graph, node, load_file, parent_generated_data_list,
                                                                        generated_data_for_db_initialization[node.unique_name],
                                                                        workload_insert_frequency_for_node, workload_insert_file)
                    else:#just include parent_entity's tuples since it doesn't have a hierarchy - only pick from entity itself for weak entity
                        generate_insert_query_workload_data_weak_entity(graph, node, load_file, generated_data_for_db_initialization.get(node.parent_entity.unique_name),
                                                                        generated_data_for_db_initialization[node.unique_name],
                                                                        workload_insert_frequency_for_node, workload_insert_file)
                    #print(node.unique_name, "done")
                elif node.is_relationship():
                    if check_if_relationship_is_1_N(node):
                        side_N_entity_unique_name, side_1_entity_unique_name = check_if_relationship_is_1_N(node)

                        side_N_entity = graph.get_node_by_name(side_N_entity_unique_name)
                        side_1_entity = graph.get_node_by_name(side_1_entity_unique_name)

                        if len(side_N_entity.children)>0:#need to include all tuples from all subclasses rooted from side_N_entity
                            side_N_generated_data_list = []
                            union_tuples_of_subclasses_to_participating_parents(generated_data_for_db_initialization, side_N_entity, side_N_generated_data_list)
                        else:#simply tuples only from entity
                            side_N_generated_data_list = generated_data_for_db_initialization.get(side_N_entity_unique_name)

                        if len(side_1_entity.children)>0:#need to include all tuples from all subclasses rooted from side_1_entity
                            side_1_generated_data_list = []
                            union_tuples_of_subclasses_to_participating_parents(generated_data_for_db_initialization, side_1_entity, side_1_generated_data_list)
                        else:#simply tuples only from entity
                            side_1_generated_data_list = generated_data_for_db_initialization.get(side_1_entity_unique_name)

                        generate_insert_query_workload_data_relationship(graph, node, load_file, side_N_entity_unique_name,
                                                                         side_N_generated_data_list,
                                                                         side_N_participating_tuples[node.unique_name],
                                                                         side_1_entity_unique_name, side_1_generated_data_list,
                                                                         workload_insert_frequency_for_node, workload_insert_file)
                    else:
                        entity1_unique_name = node.entity1.unique_name
                        entity2_unique_name = node.entity2.unique_name

                        if len(node.entity1.children)>0:#entity1 belongs to a hierarchy - need to include all tuples from all subclasses rooted from entity_1
                            entity1_generated_data_list = []
                            union_tuples_of_subclasses_to_participating_parents(generated_data_for_db_initialization, node.entity1, entity1_generated_data_list)
                        else:#simply tuples only from entity
                            entity1_generated_data_list = generated_data_for_db_initialization.get(entity1_unique_name)

                        if len(node.entity2.children)>0:#entity2 belongs to a hierarchy - need to include all tuples from all subclasses rooted from entity_2
                            entity2_generated_data_list = []
                            union_tuples_of_subclasses_to_participating_parents(generated_data_for_db_initialization, node.entity2, entity2_generated_data_list)
                        else:#simply tuples only from entity
                            entity2_generated_data_list = generated_data_for_db_initialization.get(entity2_unique_name)

                        generate_insert_query_workload_data_relationship_M_N(graph, node, load_file, entity1_unique_name, entity1_generated_data_list,
                                                                             entity2_unique_name, entity2_generated_data_list,
                                                                             many_to_many_relationship_generated_tuples[node.unique_name],
                                                                             workload_insert_frequency_for_node, workload_insert_file)

                    #print(node.unique_name, "done")

    workload_insert_file.close()

def generate_test_data(graph, load_file):
    #return generate_test_stat_data(graph, load_file)  #only stat data without generating workload - for synthetic experiments - example2_synthetic.json
    reset_workload_file()

    #generate insert data for db initializing
    generated_data_dict, many_side_participating_tuples, many_to_many_relationship_generated_tuples = generate_insert_data_for_db_initialization(graph, load_file)
    logging.debug("---db initializing insert data generation done")

    #generate select * queries for query workload
    select_sql_statements = generate_select_all_queries_for_query_workload(graph, load_file)
    logging.debug("---select * query workload generation done")

    #generate insert queries for query workload
    generate_insert_queries_for_query_workload(graph, load_file, generated_data_dict, many_side_participating_tuples, many_to_many_relationship_generated_tuples)
    logging.debug("---insert query workload generation done")

    #write to workload file
    workload = {}
    workload["insert_statements_for_db_initializing"] = "insert_db_initialization.sql"
    workload["select_statements_of_query_workload"] = select_sql_statements
    workload["insert_statements_of_query_workload"] = "insert_query_workload.sql"
    with open('workload.json', 'w') as f:
        json.dump(workload, f, indent=4)
    return 'workload.json'


