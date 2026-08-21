# Experiment 1: Robustness

This procedure runs six configurations: four fixed mappings and the two greedy
optimization objectives.

## Dataset

The synthetic e-commerce E/R schema contains:

- 34 entity sets;
- one 21-entity inheritance hierarchy with maximum depth 5;
- one 5-entity inheritance hierarchy with maximum depth 3;
- 13 weak entity sets;
- 20 M:1 or M:N relationship sets; and
- approximately 11 GB of relational data.

The schema definition used by the commands below is
`example2_e_commerce.json`.

## Prerequisites

- PostgreSQL 16;
- a Python environment containing the CompileDB dependencies;

Run all commands from the directory `/prototype/src/` containing `test_file-1.py`,
`helper_functions.py`, `search_algorithm_all_attributes.py`, and
`example2_e_commerce.json`.

## Database-loading method

In the `init_database` path in `test_file-1.py`, select one of the following
loading functions:

- Memory-constrained environment:
  `insert_data_in_batches_with_csv_with_templatization_parallelized`
- Environment with sufficient memory:
  `insert_data_in_batches_with_templatization_parallelized`

Only the first run should initialize with `init`. Later runs use
`test_config`; CompileDB restructures the existing relational schema for the
new mapping and reloads the data accordingly.

## Search configuration

The mapping-selection method is chosen inside
`start_search_for_schema_for_generated_workload` in `helper_functions.py`.

| Run | Configuration | Search method | Iterations |
|---:|---|---|---:|
| 1 | ABI+FIE | `greedy_search` | 0 |
| 2 | ABI | `greedy_search` | 0 |
| 3 | CIP+FIE | `greedy_search` | 0 |
| 4 | CIP | `greedy_search` | 0 |
| 5 | Greedy-1 | `greedy_search_with_random_starts` | configured value |
| 6 | Greedy-2 | `greedy_search_with_random_starts_for_obj_of_optimizing_for_normalized_costs` | configured value |

For Runs 1--4, set the number of iterations in `greedy_search` to `0`. This
prevents the search from changing the fixed configuration supplied through
`default_options`.

## Running the experiment

### Run 1: ABI+FIE

In `search_algorithm_all_attributes.py`, set:

```python
default_options = {
    "entity": ["all_by_itself"],
    "weak_entity": ["all_by_itself"],
    "sub_class": ["all_by_itself"],
    "1_N_relationship": ["folded_to_many_side"],
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["contained_in_parent"],
}
```

Use the `init` action because this is the first run:

```bash
python3 test_file-1.py init test_db example2_e_commerce.json
```

Preserve the result before starting the next run:

```bash
mkdir -p results
cp output.csv results/abi_fie.csv
```

### Run 2: ABI

Set:

```python
default_options = {
    "entity": ["all_by_itself"],
    "weak_entity": ["all_by_itself"],
    "sub_class": ["all_by_itself"],
    "1_N_relationship": ["all_by_itself"],
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["contained_in_parent"],
}
```

Run:

```bash
python3 test_file-1.py test_config test_db example2_e_commerce.json
cp output.csv results/abi.csv
```

### Run 3: CIP+FIE

Set:

```python
default_options = {
    "entity": ["all_by_itself"],
    "weak_entity": ["all_by_itself"],
    "sub_class": ["contained_in_parent"],
    "1_N_relationship": ["folded_to_many_side"],
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["contained_in_parent"],
}
```

Run:

```bash
python3 test_file-1.py test_config test_db example2_e_commerce.json
cp output.csv results/cip_fie.csv
```

### Run 4: CIP

Set:

```python
default_options = {
    "entity": ["all_by_itself"],
    "weak_entity": ["all_by_itself"],
    "sub_class": ["contained_in_parent"],
    "1_N_relationship": ["all_by_itself"],
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["contained_in_parent"],
}
```

Run:

```bash
python3 test_file-1.py test_config test_db example2_e_commerce.json
cp output.csv results/cip.csv
```

### Run 5: Greedy-1

In `helper_functions.py`, configure
`start_search_for_schema_for_generated_workload` to invoke
`greedy_search_with_random_starts`. Restore the intended nonzero iteration and
random-restart settings before running:

```bash
python3 test_file-1.py test_config test_db example2_e_commerce.json
cp output.csv results/greedy_1.csv
```

### Run 6: Greedy-2

In `helper_functions.py`, configure
`start_search_for_schema_for_generated_workload` to invoke
`greedy_search_with_random_starts_for_obj_of_optimizing_for_normalized_costs`.
Run:

```bash
python3 test_file-1.py test_config test_db example2_e_commerce.json
cp output.csv results/greedy_2.csv
```

## Outputs

Each execution writes its results to `output.csv`. The commands above preserve
the six outputs under `results/`:

```text
results/
|-- abi_fie.csv
|-- abi.csv
|-- cip_fie.csv
|-- cip.csv
|-- greedy_1.csv
`-- greedy_2.csv
```
For each of the six configurations - save execution time for each entity/relationship node as shown in ER-experiments - boxplot-opt_obj_2.csv and ER-experiments-boxplot.csv. Use boxplot_e_commerce_expt.py to draw the boxplot graph.



