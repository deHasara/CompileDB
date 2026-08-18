# Cost-Model Validation

This directory contains the experiment used to evaluate whether CompileDB's
estimated workload cost predicts measured PostgreSQL execution time.

The experiment records:

1. the workload cost estimated by CompileDB's analytical cost model; and
2. the total execution time measured by PostgreSQL for the same workload.

The final figure plots estimated cost against measured execution time with
logarithmic x- and y-axes. This experiment validates the cost model.

## Dataset

The paper uses the same synthetic e-commerce schema:

- 34 entity sets;
- one 21-entity inheritance hierarchy with maximum depth 5;
- one 5-entity inheritance hierarchy with maximum depth 3;
- 13 weak entity sets;
- 20 M:1 or M:N relationship sets; and
- approximately 11 GB of relational data.

## Relevant files

| File | Purpose |
|---|---|
| `generate_node_sizes_query_freq_skew.py` | Generates cardinalities, relationship statistics, and unit query frequencies and writes them into the schema JSON. |
| `test_file-1.py` | Creates the workload and invokes `run_different_configurations` to evaluate multiple mappings. |
| `example2_e_commerce.json` | Input E/R schema. Preserve an unchanged copy of this file. |
| `output_cost_model.csv` | Raw estimated-cost and measured-time results. |



## 1. Prepare the schema input

The generator modifies its input JSON **in place**. Create a dedicated copy so
that the original schema remains unchanged:

```bash
cp example2_e_commerce.json example2_e_commerce_cost_model.json
```

At the bottom of `generate_node_sizes_query_freq_skew.py`, set:

```python
load_file = "example2_e_commerce_cost_model.json"
init_node_sizes_and_query_frequencies(load_file)
```

## 2. Generate cardinalities and workload frequencies
Run:

```bash
python3 generate_node_sizes_query_freq_skew.py
```

The script adds or replaces the following top-level fields in
`example2_e_commerce_cost_model.json`:

- `node_data`;
- `select_all_frequencies`; and
- `insert_frequencies`.

To change only query frequencies, comment out  write_node_data_to_load_file(load_file, node_data) in method `init_node_sizes_and_query_frequencies` of `generate_node_sizes_query_freq_skew.py` and run the file.

## 3. Run the validation experiment

Run the cost-model validation as follows:

```bash
python3 test_file-1.py \
    run_different_configs \
    cost_model_db \
    example2_e_commerce_cost_model.json
```

The argument order is important. `run_different_configs` is the command,
`cost_model_db` is the PostgreSQL database, and the final argument is the
generated schema JSON.

Internally, the driver performs the following steps:

1. creates the database if it does not exist;
2. constructs the E/R graph from the schema JSON;
3. generates one workload using `initialize_workload_generation`;
4. retains that workload and its relation-size metadata; and
5. calls `run_different_configurations` to estimate and measure the sampled
   mappings.

Do not regenerate the workload between configurations.

## 5. Collect and validate the results

The experiment writes its raw results to:

```text
output_cost_model.csv
```

## 6. Plot 

Run:
```
python3 log-plot.py
```

Create a scatter plot using:

- x-axis: estimated workload cost;
- y-axis: measured total PostgreSQL execution time in milliseconds;
- logarithmic scale on both axes; and
- one point for each of the sampled mappings.

