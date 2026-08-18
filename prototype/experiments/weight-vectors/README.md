Change fraction parameter in generate_select_all_query_frequencies and generate_insert_query_frequencies to randomly select 1/6 th of components for each workload.
Generate each json schema with workload.
Then run python3 test_file-1.py init test_db schema.json and get total time from output.csv
Do this for each 4 fixed mappings and 2 greedy variants
Generate table with normalized execution time by running avg-normalized-times.py where you get the sum of time for normalized components
