# Synthetic Hierarchy-Position Workloads

This directory contains the synthetic experiment used to study how the
hierarchy levels accessed by a workload affect the preferred inheritance
mapping.

## Paper correspondence

This experiment corresponds to **Section 7.2, Experiment 4**, and **Figure 10**
of *From E/R Database Abstraction to Workload-Aware Relational Realization*.

Unlike the preceding experiments, this experiment compares **estimated
component costs** rather than PostgreSQL execution times. It evaluates six
workload structures and nine mapping configurations. Within each workload,
every component cost is normalized by the lowest estimated cost observed for
that component across the nine configurations.

## Synthetic schema

The paper schema contains two binary inheritance hierarchies, `R` and `S`.
Each hierarchy has three levels:

```text
Level 0:              R                         S
                     / \                       / \
Level 1:          R1     R2                 S1     S2
                  / \    / \                 / \    / \
Level 2:        R3 R4  R5 R6              S3 S4  S5 S6
```

Each hierarchy therefore contains seven entity sets. The paper creates an M:N
relationship between every entity pair across the two hierarchies, producing:

```text
7 x 7 = 49 M:N relationship sets
```

In `example2_synthetic.json`, these relationships use the `RM_` prefix. For
example, `RM_R3_S5` connects leaf entity sets `R3` and `S5`.

### Important schema-file detail

The supplied JSON contains:

- 14 entity sets;
- 49 M:1 relationships with the `RS_` prefix;
- 49 M:N relationships with the `RM_` prefix; and
- 112 conceptual components in total.

Experiment 4 in the paper uses the 49 M:N relationships. The six workload
files must therefore assign nonzero weights only to the applicable entities
and `RM_` relationships. All `RS_` relationships must have weight zero.

The supplied JSON currently assigns select and insert frequency `1` to all 112
components, so it is a schema-and-statistics template, not any one of the six
paper workloads.

## Relevant files

| File | Purpose |
|---|---|
| `example2_synthetic.json` | Base schema and component statistics. |
| `scripts-1.py` | Generates the four mixed level-specific inheritance configurations. |
| `test_file-1.py` | Invokes schema selection and component-cost estimation. |
| `ER-experiments - Sheet19.csv` | Component-level estimated costs for six workloads and nine configurations. |
| `boxplot-costs-1.py` | Normalizes the component costs and generates the six-panel boxplot. |
| `boxplots_all_workloads_1.png` | Figure generated from the supplied raw CSV. |

The commands below use the canonical repository filenames. Downloaded copies
may contain timestamp or numeric suffixes; rename them before running the
experiment.

## Workload definitions

For every component included in a workload, set both its select weight `w_c`
and insert weight `I_c` to `1`. Set both weights to `0` for every other
component.

| Workload | Left hierarchy | Right hierarchy | Entities | M:N relationships | Total components |
|---|---|---|---:|---:|---:|
| RR | Root `R` | Root `S` | 2 | 1 | 3 |
| RL | Root `R` | Leaves `S3`--`S6` | 5 | 4 | 9 |
| LR | Leaves `R3`--`R6` | Root `S` | 5 | 4 | 9 |
| IL | Internal `R1`,`R2` | Leaves `S3`--`S6` | 6 | 8 | 14 |
| LI | Leaves `R3`--`R6` | Internal `S1`,`S2` | 6 | 8 | 14 |
| LL | Leaves `R3`--`R6` | Leaves `S3`--`S6` | 8 | 16 | 24 |

For example, RL contains:

```text
R, S3, S4, S5, S6,
RM_R_S3, RM_R_S4, RM_R_S5, RM_R_S6
```

## 1. Generate the six workload JSON files

The following command derives all six workload files from the supplied base
schema while preserving the same `node_data` in every file:

```bash
python3 - <<'PY'
import copy
import json
from pathlib import Path

base_path = Path("example2_synthetic.json")
base = json.loads(base_path.read_text())

root_r = ["r"]
internal_r = ["r1", "r2"]
leaf_r = ["r3", "r4", "r5", "r6"]

root_s = ["s"]
internal_s = ["s1", "s2"]
leaf_s = ["s3", "s4", "s5", "s6"]

def workload_components(left, right):
    relationships = {
        f"rm_{left_entity}_{right_entity}"
        for left_entity in left
        for right_entity in right
    }
    return set(left) | set(right) | relationships

workloads = {
    "rr": workload_components(root_r, root_s),
    "rl": workload_components(root_r, leaf_s),
    "lr": workload_components(leaf_r, root_s),
    "il": workload_components(internal_r, leaf_s),
    "li": workload_components(leaf_r, internal_s),
    "ll": workload_components(leaf_r, leaf_s),
}

output_dir = Path("workloads")
output_dir.mkdir(exist_ok=True)
all_components = list(base["node_data"])

for workload_name, selected in workloads.items():
    missing = selected - set(all_components)
    assert not missing, f"unknown components for {workload_name}: {missing}"

    frequencies = {
        component: 1 if component in selected else 0
        for component in all_components
    }

    workload = copy.deepcopy(base)
    workload["select_all_frequencies"] = frequencies
    workload["insert_frequencies"] = dict(frequencies)

    output_path = output_dir / f"example2_synthetic_{workload_name}.json"
    output_path.write_text(json.dumps(workload, indent=2) + "\n")
    print(f"{workload_name.upper()}: {len(selected)} components -> {output_path}")
PY
```

Expected output:

```text
RR: 3 components
RL: 9 components
LR: 9 components
IL: 14 components
LI: 14 components
LL: 24 components
```

Validate that the six files share identical statistics and contain the correct
number of nonzero weights:

```bash
python3 - <<'PY'
import glob
import json

expected = {"rr": 3, "rl": 9, "lr": 9, "il": 14, "li": 14, "ll": 24}
reference_node_data = None

for path in sorted(glob.glob("workloads/example2_synthetic_*.json")):
    name = path.rsplit("_", 1)[-1].removesuffix(".json")
    with open(path) as stream:
        data = json.load(stream)

    select_frequency = data["select_all_frequencies"]
    insert_frequency = data["insert_frequencies"]
    assert select_frequency == insert_frequency
    assert sum(value > 0 for value in select_frequency.values()) == expected[name]
    assert not any(
        component.startswith("rs_") and value > 0
        for component, value in select_frequency.items()
    )

    if reference_node_data is None:
        reference_node_data = data["node_data"]
    else:
        assert data["node_data"] == reference_node_data

print("Validated six hierarchy-position workloads")
PY
```

## 2. Enable statistics-only cost evaluation

This experiment does not require materializing and executing the generated
data. Configure the experiment path to generate statistics rather than tuples:

- In `workload_generator.py`, use the statistics-only
  `generate_test_stat_data` path instead of full test-data materialization.
- In `test_file-1.py`, use
  `load_workload_queries_node_costs_only(db_name, load_file)` to collect
  component-level estimated costs.
- Disable the normal `load_workload_queries` execution path for this
  experiment.

Every one of the 54 experiment runs must use the same `node_data` and cost
model parameters.

## 3. Configure the nine mappings

The experiment evaluates:

| Result column | Mapping/search configuration |
|---|---|
| `Greedy-1` | Greedy search with random starts using objective 1. |
| `Greedy-2` | Greedy search with random starts using objective 2. |
| `ABI` | ABI for every hierarchy node. |
| `PBI` | ABI roots and PBI for every subclass. |
| `CIP` | ABI roots and CIP for every subclass. |
| `(ABI,CIP,ABI)` | ABI roots, CIP internal nodes, ABI leaves. |
| `(ABI,PBI,ABI)` | ABI roots, PBI internal nodes, ABI leaves. |
| `(ABI,ABI,CIP)` | ABI roots and internal nodes, CIP leaves. |
| `(ABI,ABI,PBI)` | ABI roots and internal nodes, PBI leaves. |

### Greedy-1

In `start_search_for_schema_for_generated_workload` in `helper_functions.py`,
invoke:

```python
greedy_search_with_random_starts(...)
```

### Greedy-2

Invoke:

```python
greedy_search_with_random_starts_for_obj_of_optimizing_for_normalized_costs(...)
```

### Uniform ABI, PBI, and CIP mappings

For these fixed configurations, invoke `greedy_search` and set its iteration
count to `0` so that the search does not change the initial mapping.

Use the following common options in `search_algorithm_all_attributes.py`:

```python
default_options = {
    "entity": ["all_by_itself"],
    "weak_entity": ["all_by_itself"],
    "sub_class": [SUBCLASS_MAPPING],
    "1_N_relationship": ["all_by_itself"],
    "M_N_relationship": ["all_by_itself"],
    "multi_valued_attribute": ["contained_in_parent"],
}
```

Set `SUBCLASS_MAPPING` as follows:

| Configuration | `SUBCLASS_MAPPING` |
|---|---|
| ABI | `"all_by_itself"` |
| PBI | `"partially_by_itself"` |
| CIP | `"contained_in_parent"` |

### Mixed level-specific mappings

`scripts-1.py` defines the four mixed mappings:

| Script variable | Generated configuration |
|---|---|
| `level_mapping_1` | `(ABI,CIP,ABI)` |
| `level_mapping_2` | `(ABI,PBI,ABI)` |
| `level_mapping_3` | `(ABI,ABI,CIP)` |
| `level_mapping_4` | `(ABI,ABI,PBI)` |

The script does **not** provide command-line options. Its last line currently
executes only:

```python
print_config(level_mapping_4)
```

To generate each configuration, change that final argument and run the script
once per mapping. For example:

```bash
mkdir -p generated_configs
python3 scripts-1.py > generated_configs/abi_abi_pbi.txt
```

For a more robust schema path, change the script's load-file definition to:

```python
load_file = Path(__file__).with_name("example2_synthetic.json")
```

The script prints assignments of the form:

```python
config["r"] = "all_by_itself"
config["r1"] = "contained_in_parent"
config["r3"] = "all_by_itself"
```

Apply the generated assignments to the fixed starting configuration, invoke
`greedy_search`, and set the iteration count to `0`.

## 4. Run the experiment

Evaluate every workload under every mapping:

```text
6 workloads x 9 configurations = 54 runs
```

Use a fresh database name for each run, or explicitly recreate the prior
experiment database before reuse. A representative command is:

```bash
python3 test_file-1.py \
    init \
    synthetic_rr_greedy1 \
    workloads/example2_synthetic_rr.json
```

For each run, preserve the component-level estimated costs along with:

- workload name;
- mapping configuration;
- selected component name;
- estimated select cost;
- estimated insert cost; and
- estimated combined component cost.

The final raw table uses the combined component cost.

## 5. Construct the raw cost CSV

Combine the 54 runs into:

```text
ER-experiments - Sheet19.csv
```

Use this exact column order:

```text
Greedy-1,Greedy-2,ABI,PBI,CIP,(ABI,CIP,ABI),(ABI,PBI,ABI),(ABI,ABI,CIP),(ABI,ABI,PBI)
```

Create six contiguous blocks in this order:

```text
RR, RL, LR, IL, LI, LL
```

Repeat the header at the beginning of every block. A blank separator row may
appear between blocks. The component rows must be aligned across all nine
columns: each row must contain the nine estimated costs for the same
conceptual component.

The supplied raw CSV has the following verified structure:

| Workload block | Numeric component rows |
|---|---:|
| RR | 3 |
| RL | 9 |
| LR | 9 |
| IL | 14 |
| LI | 14 |
| LL | 24 |
| **Total** | **73** |

Thus, the result contains:

```text
73 components x 9 configurations = 657 estimated-cost values
```

`boxplot-costs-1.py` assigns workload names based only on block order and
assigns row identifiers based only on row position. Missing, additional, or
reordered rows will therefore invalidate the normalization.

## 6. Generate Figure 10

Place `boxplot-costs-1.py` and `ER-experiments - Sheet19.csv` in the same
directory, then run:

```bash
MPLBACKEND=Agg python3 boxplot-costs-1.py
```

The script produces:

```text
boxplots_all_workloads_1.png
```

Expected result:

![Normalized component-cost distributions for RR, RL, LR, IL, LI, and LL workloads](boxplots_all_workloads_1.png)

For every workload component `c` and configuration `s`, the script computes:

```text
normalized_cost(c,s) = cost(c,s) / min_s' cost(c,s')
```

Consequently, the lowest cost for every component is normalized to `1`. Each
subplot contains one box plot per configuration:

- the orange line is the median;
- the red triangle is the arithmetic mean;
- the box spans the interquartile range;
- the whiskers and circles show the remaining range and outliers; and
- the dashed horizontal line at `1` denotes the component-wise optimum.

All six subplots share a logarithmic y-axis.

### Matplotlib compatibility notes

Recent Matplotlib versions emit two warnings for the supplied script:

1. `labels=` in `ax.boxplot` is deprecated; use `tick_labels=configs`.
2. `global_min = 0` is invalid for a logarithmic axis. Use:

   ```python
   global_min = df_plot[configs].min().min()
   ```

These changes remove the warnings without changing the normalization method.

## Reference-result checks

Before accepting a reproduced figure, verify that:

- the raw CSV contains six blocks and nine configuration columns;
- the six blocks contain `3`, `9`, `9`, `14`, `14`, and `24` numeric rows;
- every raw cost is finite and strictly positive;
- the minimum normalized value in every component row is `1`;
- each subplot contains nine box plots in the documented order;
- the y-axis is logarithmic and shared across all subplots; and
- the figure contains RR, RL, LR, IL, LI, and LL in that order.

The supplied raw CSV successfully generates the supplied six-panel figure.

## Reproducibility checklist

Record the following information with every complete run:

- Git commit;
- schema JSON filename and checksum;
- the six workload JSON checksums;
- cost-model parameters;
- greedy-search seeds and restart counts;
- mapping selected by Greedy-1 and Greedy-2 for each workload;
- Python, NumPy, pandas, and Matplotlib versions;
- raw CSV checksum; and
- final figure checksum.
