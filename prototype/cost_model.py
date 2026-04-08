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
    index_update_cost = 0.0 * num_indexes
    #extra cost incurred for non-folded entity/relationship inserts - since for folded entity/relationships no index update cost
    index_update_cost_for_table = search_cost(table_size) * num_indexes
    total_per_tuple = base_insert_cost + index_update_cost + index_update_cost_for_table
    return num_tuples * total_per_tuple

def search_cost(num_tuples):
    return log2(num_tuples)

def scan_folded_weak_entity(length, width, scan_cost_for_weak_entity_col=1.2):
    #except folded weak entity column, scan cost is regular
    return length * (width-1) * 1 + length * 1 * scan_cost_for_weak_entity_col #for weak entity column, cost is 1.2 by defaule

#per weak entity tuple - unfolding_cost_per_weak_entity_tuple - this cost is significant
#per weak entity tuple, cost to build the tuple - extraction_cost_per_weak_entity_tuple - this cost is not significant
#benchmarked a query in postgres
#with only filter on union view - WHERE jsonb_array_length(temp_user.browsingsession) > 0 - cost insignificant
#and
#unfolding(CROSS JOIN LATERAL jsonb_array_elements(temp_user.browsingsession) AS b WHERE jsonb_array_length(temp_user.browsingsession) > 0) - cost significant
#and
#unfolding and extracting(b ->> 'session_id' AS session_id, b ->> 'started_at' AS started_at, b ->> 'device' AS device) - not much change in significant cost in second step
def scan_folded_weak_entity_modified(parent_tuples_with_non_zero_length_for_weak_entity_array, weak_entity_tuples, unfolding_cost_per_weak_entity_tuple=25, extraction_cost_per_weak_entity_tuple=20):
    return (parent_tuples_with_non_zero_length_for_weak_entity_array + weak_entity_tuples * unfolding_cost_per_weak_entity_tuple)
    #return (parent_tuples_with_non_zero_length_for_weak_entity_array + parent_tuples_with_non_zero_length_for_weak_entity_array * unfolding_cost_per_parent_tuple +
    #        weak_entity_tuples * extraction_cost_per_weak_entity_tuple)

def scan_cost(num_tuples, selectivity=1.0, scan_cost_per_tuple=0.1):#scan_cost_per_tuple=1
    return num_tuples * selectivity * scan_cost_per_tuple

def union_all_cost(tuple_counts_in_list):#when parent entity is abstract table - union of all children
    return sum(tuple_counts_in_list)

def sort_merge_join_cost(left, right, left_sorted=False, right_sorted=False):
    """
    if left < right:
        #outer is left - lower cardinality chosen as outer
        return left + left * search_cost(right)#modified to be a index nested loop join since smj cost is an over-estimate for joins
        #left_sorted and right_sorted don't matter with this modification
    else:
        #outer is right
        return right + right * search_cost(left)
    """
    return left + left * search_cost(right)
    #hash_build_cost_per_tuple = 3
    #return left + right*hash_build_cost_per_tuple
    """
    if left_sorted and right_sorted:
        return left + right
    elif left_sorted:
        return right*search_cost(right) + left + right
    elif right_sorted:
        return left*search_cost(left) + left + right
    return left*search_cost(left) + right*search_cost(right) + left + right #sort cost for left + sort cost for right + linear scan of both for merging
    """


def index_nested_loop_join_cost(outer_rows, inner_rows):#mapping from smj to inlj -> left is outer_rows and right is inner_rows
    return outer_rows + outer_rows * search_cost(inner_rows)


outer_rows = 100000
inner_rows1 = 20000
inner_rows2 = 50000
inner_rows3 = 100000
print(index_nested_loop_join_cost(outer_rows, inner_rows1)+index_nested_loop_join_cost(outer_rows, inner_rows2)+index_nested_loop_join_cost(outer_rows, inner_rows3))
print(index_nested_loop_join_cost(outer_rows, inner_rows1+inner_rows2+inner_rows3))








"""
def join_cost(left, right, join_type, index_on_right=True, left_match_probability=1.0, right_match_probability=1.0):
    if join_type == "inner":
        if index_on_right:
            return scan_cost(left) + scan_cost(left) * search_cost(right)
        else:#HJ
            return scan_cost(left) + scan_cost(left) * scan_cost(right)
    elif join_type == "left-outer":
        matched_cost = scan_cost(left) + scan_cost(left) * search_cost(right) if index_on_right else scan_cost(left) + scan_cost(left) * scan_cost(right)
        #unmatched_cost = scan_cost(left, 1-left_match_probability)
        return matched_cost #+ unmatched_cost
    elif join_type == "right-outer":
        matched_cost = scan_cost(left) + scan_cost(left) * search_cost(right) if index_on_right else scan_cost(left) + scan_cost(left) * scan_cost(right)
        unmatched_cost = scan_cost(right, 1-right_match_probability)
        return matched_cost + unmatched_cost
    elif join_type == "full-outer":
        matched_cost = scan_cost(left) + scan_cost(left) * search_cost(right) if index_on_right else scan_cost(left) + scan_cost(left) * scan_cost(right)
        unmatched_cost = scan_cost(left, 1-left_match_probability) + scan_cost(right, 1-right_match_probability)
        return matched_cost + unmatched_cost



R = 100
S = 200
T = 100
R_m = 0.2#driver
S_m = 0.4
T_m = 0.5
#R join S join T
join1 = join_cost(R, S, "inner", index_on_right=False, left_match_probability=R_m, right_match_probability=S_m)
join2 = join_cost((join1), T, "left", index_on_right=True, left_match_probability=S_m, right_match_probability=T_m)

relations = [R, S, T]
joins = [R]
cost = 0
for i in range(1, len(relations)):
    join__cost = join_cost(joins.pop(), relations[i])
    joins.append(join__cost)
    cost += join__cost
"""