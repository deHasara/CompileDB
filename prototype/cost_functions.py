import math

def log2(x):
    return math.log(x, 2) if x > 0 else 0

#no of tuples pass through each operator - c_out

#batch insert - db initialization
def insert_cost(num_tuples, num_indexes=0):
    base_insert_cost = 9.0  # insert to table
    index_update_cost = 7.0 * num_indexes
    total_per_tuple = base_insert_cost + index_update_cost
    return num_tuples * total_per_tuple

def insert_cost_for_workload_queries(num_tuples, table_size=0, num_indexes=0):
    base_insert_cost = 9.0  # insert to table
    #extra cost incurred for non-folded entity/relationship inserts - since for folded entity/relationships no index update cost
    index_update_cost_for_table = search_cost(table_size) * num_indexes
    total_per_tuple = base_insert_cost + index_update_cost_for_table
    return num_tuples * total_per_tuple

def search_cost(num_tuples):
    return log2(num_tuples)

#per weak entity tuple - unfolding_cost_per_weak_entity_tuple - this cost is significant
#benchmarked a query in postgres
#with only filter on union view - WHERE jsonb_array_length(temp_user.browsingsession) > 0 - cost insignificant
#and
#unfolding(CROSS JOIN LATERAL jsonb_array_elements(temp_user.browsingsession) AS b WHERE jsonb_array_length(temp_user.browsingsession) > 0) - cost significant
#and
#unfolding and extracting(b ->> 'session_id' AS session_id, b ->> 'started_at' AS started_at, b ->> 'device' AS device) - not much change in significant cost in second step
def scan_folded_weak_entity_modified(parent_tuples_with_non_zero_length_for_weak_entity_array, weak_entity_tuples, unfolding_cost_per_weak_entity_tuple=25):
    return (parent_tuples_with_non_zero_length_for_weak_entity_array + weak_entity_tuples * unfolding_cost_per_weak_entity_tuple)

def scan_cost(num_tuples, selectivity=1.0, scan_cost_per_tuple=0.1):#scan_cost_per_tuple=1
    return num_tuples * selectivity * scan_cost_per_tuple

def union_all_cost(tuple_counts_in_list):#when parent entity is abstract table - union of all children
    return sum(tuple_counts_in_list)

def join_cost(left, right, left_sorted=False, right_sorted=False):
    return left + left * search_cost(right)


