We generate complex E/R workloads containing select, project, join, aggregate queries. Selectivities range from [0.1,0.9]

First generate the schema with distributions
python3 build_attribute_distribution_schema.py \
  example2_e_commerce.json \
  example2_e_commerce_with_distributions.json

Next generate the conceptual_data_profile.json required to generate query workloads - default sample size is 10000
python3 generate_db_initialization_workload.py \
  --schema example2_e_commerce_with_distributions.json \
  --seed 1

Generate selectivity aligned E/R query workloads
python3 generate_selectivity_aligned_query_workloads.py \
  --schema example2_small_with_distributions.json \
  --profile conceptual_data_profile.json \
  --template-workload er_query_workload_100_01.json \
  --output-dir er_query_workloads-hs-mid \
  --workload-count 1 \
  --queries-per-workload 100 \
  --targets 0.10,0.20,0.30,0.40,0.50 \
  --seed 1

python3 generate_schema_driven_selectivity_workloads.py \
  --schema example2_small_with_distributions.json \
  --profile conceptual_data_profile.json \
  --output-dir er_query_workloads-hs-mid-1 \
  --workload-count 10 \
  --queries-per-workload 100 \
  --targets 0.10,0.20,0.30,0.40,0.50 \
  --seed 1 \
  --progress-every 25

python3 generate_selectivity_aligned_query_workloads.py \
   --schema example2_small_with_distributions.json \
   --profile conceptual_data_profile.json \
   --template-workload er_query_workload_100_01.json \
   --output-dir er_query_workloads-ms
   --workload-count 10 \
   --queries-per-workload 100 \
   --targets 0.50,0.60,0.70,0.80,0.90 \
   --seed 1

 python3 generate_selectivity_aligned_query_workloads.py \
   --schema example2_small_with_distributions.json \
   --profile conceptual_data_profile.json \
   --template-workload er_query_workload_100_01.json \
   --output-dir er_query_workloads-ls
   --workload-count 10 \
   --queries-per-workload 100 \
   --targets 0.90,0.99
   --seed 1

#subclass-weight 3: subclasses are three times as likely as hierarchy roots in single-entity queries.
#endpoint-subclass-probability 0.60: a relationship endpoint declared as Product has a 60% chance of being restricted to a discovered subclass such as Phone, Camera, or Accessory.
#hub-penalty 0.75: reduces repeated selection of high-degree nodes such as Product in relationships and multi-join paths.
python3 generate_schema_driven_selectivity_workloads_subclass_biased.py \
  --schema example2_small_with_distributions.json \
  --profile conceptual_data_profile.json \
  --output-dir er_query_workloads-ms-subclass-biased \
  --workload-count 10 \
  --queries-per-workload 100 \
  --targets 0.50,0.60,0.70,0.80,0.90 \
  --seed 1 \
  --subclass-weight 3 \
  --endpoint-subclass-probability 0.60 \
  --hub-penalty 0.75

#strictly leaf nodes with mid selectivity
python3 generate_schema_driven_selectivity_workloads_leaf_biased.py \
  --schema example2_small_with_distributions.json \
  --profile conceptual_data_profile.json \
  --output-dir er_query_workloads-subclass-only \
  --workload-count 10 \
  --queries-per-workload 100 \
  --subclass-only \
  --leaf-subclass-weight 8 \
  --targets 0.50,0.60,0.70,0.80,0.90,0.99 \
  --seed 1

#The ten workloads have distinct AST-derived entity/relationship read profiles, so they are suitable for generating separate select_all_frequencies inputs.
python3 generate_node_sizes_query_freq_skew.py \
    example2_small_with_distributions.json \
    er_query_workloads/er_query_workload_100_01.json \
    --output example2_small_with_distributions_workload_100.json

Then feed example2_small_2_with_distributions_workload_100.json into your existing mapping/search process
After CompileDB creates the relational schema and saves its metadata in erdb_objects, you do not need to reload the original E/R JSON file for query rewriting.
The runtime flow is:
Load the generated mapping metadata from the database.
Construct one reusable query engine.
Submit arbitrary E/R queries to that engine.
Execute the returned relational SQL with its parameters.

cd ~/CLionProjects/ErbiumDB-Query-Rewriter/prototype-3
python3 rewrite_er_query_workloads.py \
  --db university_9 \
  --input-dir er_query_workloads \
  --pattern 'er_query_workload_100_01.json' \
  --output-dir explain_analyze_workloads \
  --explain \
  --emit-explain-analyze \
  --explain-format text

#After every database initialization, explicitly collect statistics before executing the workload:
#to avoid bad join orders
 psql -X \
  -h localhost \
  -U postgres \
  -d test_db \
  -v ON_ERROR_STOP=1 \
  -c "VACUUM (ANALYZE);" \
  --echo-all \
  -f explain_analyze_workloads-ABI/rewritten_er_query_workload_100_01.sql \
  > explain_analyze_workloads-ABI/results/explain_analyze_workload_01.log 2>&1

(venv) hasara@hasara-XPS-15-9520:~/CLionProjects/ErbiumDB-Query-Rewriter/prototype-3$
python3 explain_analyze_workloads/results/summarize_explain_analyze.py explain_analyze_workloads-ABI/results/explain_analyze_workload_01.log
