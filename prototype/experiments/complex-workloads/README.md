# Complex E/R Workload Generation and Evaluation

The pipeline creates ten structurally distinct query workloads,
derives workload-specific mapping weights, rewrites the E/R queries for each
candidate mapping, and measures their PostgreSQL execution time.

Each canonical workload contains 100 E/R queries drawn from selection,
projection, join, and aggregation patterns. Predicate selectivity targets span
0.10 through 0.90.

## Pipeline at a glance

1. Add attribute-domain distributions to the conceptual schema.
2. Generate the shared initialization workload and conceptual data profile.
3. Generate ten unique, schema-driven E/R query workloads.
4. Convert each query workload into mapping-search frequency weights.
5. Select and compile every candidate mapping using the same database contents.
6. Rewrite, execute, and summarize all 100 queries for every workload/mapping pair.

## Files

| File | Purpose |
| --- | --- |
| `build_attribute_distribution_schema.py` | Adds deterministic, predicate-independent attribute domains to the E/R schema. |
| `generate_db_initialization_workload.py` | Creates the shared insertion workload and the conceptual data profile used for selectivity calibration. |
| `generate_schema_driven_selectivity_workloads.py` | Canonical generator for ten structurally distinct SPJG workloads. |
| `generate_selectivity_aligned_query_workloads.py` | Recalibrates literals in a fixed template workload; useful for controls, but not for creating new query shapes. |
| `generate_schema_driven_selectivity_workloads_subclass_biased.py` | Optional sensitivity generator that increases subclass use and reduces repeated hub selection. |
| `generate_schema_driven_selectivity_workloads_leaf_biased.py` | Optional leaf/subclass stress-workload generator. |
| `generate_node_sizes_query_freq_skew-1.py` | Converts one query workload into the component-frequency input used by mapping search. |
| `example2_e_commerce.json` | Base E/R schema. |
| `example2_e_commerce_with_distributions.json` | Distribution-annotated E/R schema produced in Step 1. |



## 1. Add attribute distributions to the schema

```bash
python3 build_attribute_distribution_schema.py \
  example2_e_commerce.json \
  example2_e_commerce_with_distributions.json
```

The output records the domain of every non-primary attribute and includes
metadata describing the fixed seed, locale, inheritance behavior, and supported
distribution families. These domains are independent of a physical mapping, so
the same logical data can be generated for every mapping under comparison.

## 2. Generate the shared initialization workload and profile

```bash
python3 generate_db_initialization_workload.py \
  --schema example2_e_commerce_with_distributions.json \
  --output-dir db_initialization_workload \
  --seed 1 \
  --profile-sample-size 10000
```

This creates:

- `db_initialization_workload/insert_db_initialization.sql`
- `db_initialization_workload/db_initialization_workload.json`
- `db_initialization_workload/conceptual_data_profile.json`

The profile contains the schema SHA-256 digest. Query generation stops if the
profile and schema do not match. Generate this stage once and reuse the same
initialization workload, seed, and cardinalities for every candidate mapping. Example output shown in `prototype/conceptual_data_profile.json`.

## 3. Generate the ten canonical query workloads

Use the schema-driven generator for the paper experiment:

```bash
python3 generate_schema_driven_selectivity_workloads.py \
  --schema example2_e_commerce_with_distributions.json \
  --profile db_initialization_workload/conceptual_data_profile.json \
  --output-dir er_query_workloads \
  --workload-count 10 \
  --queries-per-workload 100 \
  --targets 0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90 \
  --seed 1 \
  --progress-every 25
```

The command writes `er_query_workload_100_01.json` through
`er_query_workload_100_10.json`. With the default category mix, each 100-query
workload contains:

| Query category | Count |
| --- | ---: |
| Selection and projection | 30 |
| Weak entity and owner | 20 |
| Relationship join | 20 |
| Aggregation | 15 |
| Complex multi-join | 15 |

For each candidate query, the generator:

- samples a valid shape from the E/R graph;
- calibrates predicate literals against the conceptual profile;
- parses and binds the E/R query before accepting it;
- computes an AST-derived canonical template fingerprint; and
- rejects duplicate shapes both within and across workloads.


## 4. Derive mapping-search weight vectors

Create one schema/weight-vector input for each query workload:

```bash
mkdir -p mapping_inputs

for workload in er_query_workloads/er_query_workload_100_*.json; do
  workload_id=$(basename "$workload" .json)
  python3 generate_node_sizes_query_freq_skew-1.py \
    example2_small_with_distributions.json \
    "$workload" \
    --output "mapping_inputs/example2_e_commerce_with_distributions_${workload_id}.json"
done
```

`select_all_frequencies` counts every entity and relationship referenced by a
query, not only the object named in its `FROM` clause. `insert_frequencies`
records the insertion targets. Feed the corresponding generated JSON file into
the mapping/search process for each workload.


### Subclass-biased workloads

```bash
python3 generate_schema_driven_selectivity_workloads_subclass_biased.py \
  --schema example2_e_commerce_with_distributions.json \
  --profile db_initialization_workload/conceptual_data_profile.json \
  --output-dir er_query_workloads_subclass_biased \
  --workload-count 10 \
  --queries-per-workload 100 \
  --targets 0.50,0.60,0.70,0.80,0.90 \
  --seed 1 \
  --subclass-weight 3 \
  --endpoint-subclass-probability 0.60 \
  --hub-penalty 0.75
```

- `--subclass-weight 3` makes subclasses three times as likely as roots in
  single-entity queries.
- `--endpoint-subclass-probability 0.60` specializes 60% of eligible
  relationship endpoints to a discovered subclass.
- `--hub-penalty 0.75` reduces repeated selection of high-degree graph nodes.

The supplied subclass-biased weight-vector artifact is structurally different
from the fixed-template artifacts, as expected.

### Leaf/subclass-only workloads

```bash
python3 generate_schema_driven_selectivity_workloads_leaf_biased.py \
  --schema example2_e_commerce_with_distributions.json \
  --profile db_initialization_workload/conceptual_data_profile.json \
  --output-dir er_query_workloads_subclass_only \
  --workload-count 10 \
  --queries-per-workload 100 \
  --subclass-only \
  --leaf-subclass-weight 8 \
  --targets 0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90,0.99 \
  --seed 1
```

## 5. Select and compile candidate mappings

For every workload, run the existing mapping/search process using its matching
file from `mapping_inputs/`. The paper compares:

- ABI + FIE
- ABI
- CIP + FIE
- CIP
- Greedy

Use the same initialization workload and PostgreSQL settings for every mapping.


## 6. Rewrite the E/R workloads

After the compiler creates the relational schema and saves its mapping metadata
in `erdb_objects`, the query rewriter can load that metadata directly from the
database. It does not need the original E/R JSON schema at rewrite time.

Example from the query-rewriter prototype:

```bash
cd /path/to/CompileDB/prototype

python3 rewrite_er_query_workloads.py \
  --db test_db \
  --input-dir /path/to/er_query_workloads \
  --pattern 'er_query_workload_100_*.json' \
  --output-dir explain_analyze_workloads \
  --explain \
  --emit-explain-analyze \
  --explain-format text
```

Use a separate output directory for each mapping strategy so results cannot be
overwritten.

## 7. Execute and summarize

Initialize the database with the shared insertion workload, then collect fresh
optimizer statistics before executing the rewritten queries:

```bash
psql -X \
  -h localhost \
  -U postgres \
  -d test_db \
  -v ON_ERROR_STOP=1 \
  -c 'VACUUM (ANALYZE);'

psql -X \
  -h localhost \
  -U postgres \
  -d test_db \
  -v ON_ERROR_STOP=1 \
  --echo-all \
  -f explain_analyze_workloads/rewritten_er_query_workload_100_01.sql \
  > results/explain_analyze_workload_01.log 2>&1
```

Summarize the PostgreSQL log:

```bash
python3 explain_analyze_workloads/results/summarize_explain_analyze.py \
  results/explain_analyze_workload_01.log
```

Repeat this process for all ten workloads and all mapping strategies. 


