# Experiment 3: Complex E/R Query Workloads

This directory contains the procedure for evaluating fixed and
workload-aware conceptual-to-relational mappings on the synthetic e-commerce
dataset.

## Paper correspondence

This experiment corresponds most closely to **Section 7.2, Experiment 3** and
**Table 5** of *From E/R Database Abstraction to Workload-Aware Relational
Realization*.

The paper evaluates complex workloads containing selection, projection, join,
and aggregation queries over the E/R schema. Each select workload contains 100
queries with predicate selectivities ranging from 0.1 to 0.9. Insert queries
target entity or relationship sets. The access and insertion frequencies
derived from these queries are used by the mapping optimizer.

This procedure runs six configurations: four fixed mappings and the two greedy
optimization objectives. Table 5 reports only one `Greedy` column. When
producing the paper result, document explicitly whether that column uses the
`Greedy-1` or `Greedy-2` output.

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
- an empty PostgreSQL database named `test_db` for the first run; and
- the generated E/R query and insert workloads required by this experiment.

Run all commands from the directory containing `test_file-1.py`,
`helper_functions.py`, `search_algorithm_all_attributes.py`, and
`example2_e_commerce.json`.

## Database-loading method

In the `init_database` path in `test_file-1.py`, select one of the following
loading functions:

- Memory-constrained environment:
  `insert_data_in_batches_with_csv_with_templatization_parallelized`
- Environment with sufficient memory:
  `insert_data_in_batches_with_templatization_parallelized`

Only the first run should initialize and populate `test_db`. Later runs use
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

Before publishing the results, verify that every output records:

- the workload identifier;
- the selected relational mapping;
- the random seed and random-restart count;
- the PostgreSQL execution time for each query;
- the total execution time in milliseconds; and
- whether the reported time is a single measurement or the median of five
  executions.

For the Table 5 result, aggregate the total PostgreSQL execution time for each
of the ten workloads and export columns in the following order:

```text
workload,ABI+FIE,ABI,CIP+FIE,CIP,Greedy
```

## Reproducibility notes

- Record the Git commit, PostgreSQL configuration, hardware, and random seed.
- Do not regenerate the initialization data between mapping runs.
- Run the configurations on the same database contents and query workloads.
- Preserve raw `output.csv` files before running the next configuration.
- Confirm that fixed-mapping runs use zero search iterations.
- State which greedy objective supplies the paper's `Greedy` result.
