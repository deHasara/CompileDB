
In workload_generator.py, run generate_test_data with generate_test_stat_data since for this experiment only cost estimation is required for each relational configuration and workload. 
The schema used for this expriment is example2_synthetic.json.
For root-root workload, we set only entities and relationships corresponding to root, others are all set to 0.
For root-leaf, leaf-root, internal-leaf, leaf-internal, leaf-internal, and leaf-leaf we do the same.
We evaluate cost for 9 configurations for each workload: 
1. Greedy-1
   Run each workload with setting greedy_search_with_random_starts in method start_search_for_schema_for_generated_workload of helper_functions.py
   Get the estimated cost for each workload
2. Greedy-2
   Run each workload with setting greedy_search_with_random_starts_for_obj_of_optimizing_for_normalized_costs in method start_search_for_schema_for_generated_workload of helper_functions.py
   Get the estimated cost for each workload
4. ABI - Each entity in a hierarchy mapped with ABI
   Change default mapping options in search_algorithm_all_attributes.py
   default_options = {
    "entity": ["all_by_itself"],
    "weak_entity": ["all_by_itself"],
    "sub_class": ["all_by_itself"],  
    "1_N_relationship": ["all_by_itself"],
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["contained_in_parent"],
}
Set iterations to 0 in greedy_search in search_algorithm_all_attributes.py
Run each workload with setting greedy_search in method start_search_for_schema_for_generated_workload of helper_functions.py
Get the estimated cost for each workload
6. PBI - Root in a hierarchy mapped with ABI and all subclasses mapped with PBI
   Change default mapping options in search_algorithm_all_attributes.py
   default_options = {
    "entity": ["all_by_itself"],
    "weak_entity": ["all_by_itself"],
    "sub_class": ["partially_by_itself"],  
    "1_N_relationship": ["all_by_itself"],
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["contained_in_parent"],
}
Set iterations to 0 in greedy_search in search_algorithm_all_attributes.py
Run each workload with setting greedy_search in method start_search_for_schema_for_generated_workload of helper_functions.py
Get the estimated cost for each workload
8. CIP - Root in a hierarchy mapped with ABI and all subclasses mapped with CIP
   Change default mapping options in search_algorithm_all_attributes.py
   default_options = {
    "entity": ["all_by_itself"],
    "weak_entity": ["all_by_itself"],
    "sub_class": ["contained_in_parent"],  
    "1_N_relationship": ["all_by_itself"],
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["contained_in_parent"],
}
Set iterations to 0 in greedy_search in search_algorithm_all_attributes.py
Run each workload with setting greedy_search in method start_search_for_schema_for_generated_workload of helper_functions.py
Get the estimated cost for each workload
10. (ABI,CIP,ABI) - Root mapped with ABI, internal nodes mapped with CIP, and leaf nodes mapped with ABI
    
12. (ABI,PBI,ABI) - Root mapped with ABI, internal nodes mapped with PBI, and leaf nodes mapped with ABI
13. (ABI,ABI,CIP) - Root mapped with ABI, internal nodes mapped with ABI, and leaf nodes mapped with CIP
14. (ABI,ABI,PBI) - Root mapped with ABI, internal nodes mapped with ABI, and leaf nodes mapped with PBI

