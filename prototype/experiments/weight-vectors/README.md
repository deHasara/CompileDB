# Weight-Vector Workloads

This directory contains the workload-generation, execution, and aggregation
procedure for evaluating CompileDB across sparse component-access patterns.

## Paper correspondence

This experiment corresponds to **Section 7.2, Experiment 2**, **Table 3**, and
**Table 4** of *From E/R Database Abstraction to Workload-Aware Relational
Realization*.

The experiment asks whether workload-aware mappings remain efficient when each
workload accesses a different subset of the conceptual schema. It constructs
12 workloads. For each workload, one-sixth of the non-multi-valued conceptual
components are selected. If the selected set is denoted by `C'`, the paper
defines:

```text
w_c = 1 and I_c = 1  if c is in C'
w_c = 0 and I_c = 0  otherwise
```

Thus, a selected component contributes both a canonical select query and an
insert operation to the workload.

## Dataset

The experiment uses the synthetic e-commerce E/R schema described in
Section 7.2:

- 34 entity sets;
- one 21-entity inheritance hierarchy with maximum depth 5;
- one 5-entity inheritance hierarchy with maximum depth 3;
- 13 weak entity sets;
- 20 M:1 or M:N relationship sets; and
- approximately 11 GB of relational data.

Use the same generated `node_data` and relational contents for all 12
workloads. Only the workload weight vectors should change.

## Relevant files

| File | Purpose |
|---|---|
| `generate_node_sizes_query_freq_skew.py` | Generates cardinality metadata and component query frequencies. |
| `test_file-1.py` | Initializes a workload and evaluates a selected mapping. |
| `avg-normalized-times.py` | Cleans, validates, normalizes, aggregates, and emits the two paper tables. |
| `ER-experiments - Sheet17.csv` | Raw component-level PostgreSQL execution times for all workloads and mappings. |
| `normalized_exec_time_results.csv` | Average normalized execution times used in Table 3. |
| `raw_exec_time_sums.csv` | Total PostgreSQL execution times used in Table 4. |

The commands below use the canonical repository filenames. Downloaded copies
may contain timestamp or numeric suffixes; rename them before running the
experiment.

## Evaluated configurations

Each workload is evaluated under eight mappings, using the following column
names and order in the raw result file:

| Result column | Inheritance mapping | M:1 relationship mapping |
|---|---|---|
| `Greedy-obj-1` | Selected by Greedy-1 | Selected by Greedy-1 |
| `Greedy-obj-2` | Selected by Greedy-2 | Selected by Greedy-2 |
| `ABI+folded` | ABI | Folded into the many side |
| `ABI` | ABI | ABI |
| `PBI+folded` | PBI | Folded into the many side |
| `PBI` | PBI | ABI |
| `CIP+folded` | CIP | Folded into the many side |
| `CIP` | CIP | ABI |

For the fixed configurations, non-hierarchical entity sets and M:N
relationships use ABI, hierarchy roots use ABI, and multi-valued attributes
use CIP.

## 1. Correct the workload generator

The supplied generator is configured for the uniform workload:

```python
fraction = 1 / 1
```

For this experiment, the selected-set size must instead be:

```python
fraction = 1 / 6
k = max(1, int(len(entities_and_relationships) * fraction))
```

The supplied script requires three additional corrections before it exactly
implements Experiment 2.

### Use one subset for both weight vectors

`generate_select_all_query_frequencies` and
`generate_insert_query_frequencies` currently call `random.sample`
independently. Consequently, setting both fractions to `1 / 6` can produce one
subset for `w_c` and a different subset for `I_c`. That does not implement the
paper's definition.

Sample `selected` once per workload and pass the same collection to both
frequency-generation functions. Every selected component must have select and
insert frequency `1`; every unselected component must be absent or have
frequency `0` in both dictionaries.

### Generate 12 distinct workloads

The script currently fixes both random-number generators to seed `1`:

```python
random.seed(1)
np.random.seed(1)
```

Starting a new Python process with the same schema and seed regenerates the
same selected subset. Use a fixed data-generation seed and 12 distinct,
recorded workload-sampling seeds. Apply the workload seed only when sampling
the selected component set.

For example:

```text
data-generation seed: 1
workload-sampling seeds: 1, 2, ..., 12
```

The particular workload seeds may differ, but they must be recorded and must
produce 12 distinct selected sets.

### Keep the generated dataset fixed

The generator also regenerates `node_data`. Do not regenerate cardinalities or
relationship statistics with each workload seed. Generate `node_data` once,
then create 12 schema JSON files that reuse that exact `node_data` and differ
only in `select_all_frequencies` and `insert_frequencies`.

The generator modifies its `load_file` in place and currently hard-codes:

```python
load_file = "example2_e_com_small.json"
```

Use a copy of the intended e-commerce schema rather than modifying the
original file.

## 2. Generate and validate the workload files

Use stable names such as:

```text
workloads/
|-- example2_e_commerce_weight_01.json
|-- example2_e_commerce_weight_02.json
|-- ...
`-- example2_e_commerce_weight_12.json
```

After implementing the shared-subset and 12-workload generation changes
described above, run:

```bash
python3 generate_node_sizes_query_freq_skew.py
```

For the supplied result files, each workload contains 11 measured conceptual
components. The value `11` must equal the value of `k` produced by the schema
used for the experiment. If a different schema version produces another value,
update both the generator validation and `num_entities_per_workload` in
`avg-normalized-times.py`.

Validate the workload JSON files before executing PostgreSQL:

```bash
python3 - <<'PY'
import glob
import json

files = sorted(glob.glob("workloads/example2_e_commerce_weight_*.json"))
assert len(files) == 12, f"expected 12 workloads, found {len(files)}"

reference_node_data = None
selected_sets = []

for path in files:
    with open(path) as stream:
        data = json.load(stream)

    select_freq = data["select_all_frequencies"]
    insert_freq = data["insert_frequencies"]

    assert select_freq == insert_freq, f"weight-vector mismatch in {path}"
    assert len(select_freq) == 11, f"unexpected component count in {path}"
    assert set(select_freq.values()) == {1}, f"non-unit weight in {path}"

    if reference_node_data is None:
        reference_node_data = data["node_data"]
    else:
        assert data["node_data"] == reference_node_data, \
            f"node_data changed in {path}"

    selected_sets.append(frozenset(select_freq))

assert len(set(selected_sets)) == 12, "workload subsets are not distinct"
print("Validated 12 distinct workloads with fixed node_data")
PY
```

## 3. Execute every workload under all mappings

Use a fresh database for each workload, for example `weight_vector_w01`
through `weight_vector_w12`.

For the first mapping evaluated for a workload, initialize the database and
generate its reusable `workload.json`:

```bash
python3 test_file-1.py \
    init \
    weight_vector_w01 \
    workloads/example2_e_commerce_weight_01.json
```

Save `output.csv` immediately under a mapping-specific name. For example, if
the first configured mapping is Greedy-1:

```bash
mkdir -p results/workload_01
cp output.csv results/workload_01/greedy_obj_1.csv
```

For the remaining seven mappings, change the mapping/search configuration and
use `test_config` with the same database and schema file:

```bash
python3 test_file-1.py \
    test_config \
    weight_vector_w01 \
    workloads/example2_e_commerce_weight_01.json
```

Repeat this process for all eight configurations and all 12 workloads. The
`test_config` path must reuse the workload generated by the initial `init` run;
do not regenerate it between mappings.

For each canonical select query, follow the paper's timing protocol: execute
the query five times and retain its median PostgreSQL execution time.

The complete experiment contains:

```text
12 workloads x 8 mappings x 11 components = 1,056 measurements
```

## 4. Construct the component-level input CSV

Combine the saved mapping results into:

```text
ER-experiments - Sheet17.csv
```

Use this exact column order:

```text
Greedy-obj-1,Greedy-obj-2,ABI+folded,ABI,PBI+folded,PBI,CIP+folded,CIP
```

Each numeric row represents one conceptual component. Execution times for the
same workload component must occupy the same row across all eight columns.
Workload blocks must remain ordered and contiguous.

The supplied raw CSV has:

- 12 workload blocks;
- 11 numeric rows per block;
- 132 numeric rows in total;
- a repeated header at the beginning of every block; and
- two blank separator rows between consecutive blocks.

`avg-normalized-times.py` removes repeated headers and blank rows. It then
assigns workload IDs solely from row position, using groups of 11 rows. The raw
CSV therefore must not contain missing, extra, or reordered component rows.

## 5. Generate Tables 3 and 4

The aggregation script uses:

```python
input_csv = "ER-experiments - Sheet17.csv"
output_csv = "normalized_exec_time_results.csv"
raw_sum_output_csv = "raw_exec_time_sums.csv"
num_entities_per_workload = 11
num_workloads_expected = 12
```

Despite the variable name `num_entities_per_workload`, the 11 rows may
represent either entity or relationship components.

Run:

```bash
python3 avg-normalized-times.py
```

The script produces:

| Output | Paper result |
|---|---|
| `normalized_exec_time_results.csv` | Table 3: average normalized PostgreSQL execution time per workload. |
| `raw_exec_time_sums.csv` | Table 4: sum of total PostgreSQL execution time in milliseconds per workload. |

It also prints both tables in LaTeX format and reports each method's maximum
total-time slowdown relative to Greedy-1.

## Aggregation definitions

Let `t(w,c,s)` be the measured execution time of component `c` from workload
`w` under configuration `s`.

For Table 3, the script first normalizes every component row:

```text
normalized(w,c,s) = t(w,c,s) / min_s' t(w,c,s')
```

It then reports the arithmetic mean over the 11 workload components:

```text
average_normalized(w,s)
    = (1 / 11) * sum_c normalized(w,c,s)
```

For Table 4, it reports the unnormalized sum:

```text
total_time(w,s) = sum_c t(w,c,s)
```

All reported values are rounded to three decimal places.

## Workload numbering

The two generated CSV files use zero-based workload IDs `0` through `11`.
The printed LaTeX tables convert these to the paper's one-based labels `1`
through `12`.

## Reference-result checks

The supplied raw CSV was independently reprocessed with the supplied
`avg-normalized-times.py`. The generated files matched the supplied
`normalized_exec_time_results.csv` and `raw_exec_time_sums.csv` byte for byte.

The raw and derived files have the following expected shapes:

| File | Expected contents |
|---|---|
| `ER-experiments - Sheet17.csv` | 132 numeric rows and 8 mapping columns after cleaning. |
| `normalized_exec_time_results.csv` | 12 workload rows, one workload-ID column, and 8 mapping columns. |
| `raw_exec_time_sums.csv` | 12 workload rows, one workload-ID column, and 8 mapping columns. |

The maximum total-time slowdowns relative to Greedy-1 computed from the
supplied results are:

| Configuration | Maximum slowdown | Paper workload |
|---|---:|---:|
| Greedy-2 | 2.558x | 1 |
| ABI+folded | 3.600x | 9 |
| ABI | 3.729x | 12 |
| PBI+folded | 20.839x | 5 |
| PBI | 21.199x | 5 |
| CIP+folded | 10.023x | 1 |
| CIP | 6.290x | 5 |

## Reproducibility checklist

Record the following information with every complete run:

- Git commit;
- schema filename and checksum;
- fixed data-generation seed;
- the 12 workload-sampling seeds;
- selected component names for each workload;
- PostgreSQL and Python versions;
- PostgreSQL configuration;
- hardware configuration;
- mapping selected by each greedy objective;
- query-repetition and aggregation policy; and
- raw and derived CSV checksums.
