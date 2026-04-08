import pandas as pd

# ==============================
# Config
# ==============================
input_csv = "ER-experiments - Sheet17.csv"
output_csv = "normalized_exec_time_results.csv"
raw_sum_output_csv = "raw_exec_time_sums.csv"
num_entities_per_workload = 11
num_workloads_expected = 12

# ==============================
# Load raw CSV as strings first
# ==============================
raw = pd.read_csv(input_csv, dtype=str)

# Column names from the first header
methods = list(raw.columns)

# ==============================
# Remove repeated header rows
# ==============================
repeated_header_mask = raw.eq(pd.Series(methods, index=raw.columns)).all(axis=1)

# Remove fully blank rows
blank_row_mask = raw.isna().all(axis=1)

# Keep only actual data rows
df = raw[~repeated_header_mask & ~blank_row_mask].copy()

# Convert to numeric
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Drop rows that still failed conversion completely
df = df.dropna(how="all").reset_index(drop=True)

# ==============================
# Validate shape
# ==============================
expected_rows = num_entities_per_workload * num_workloads_expected

if len(df) != expected_rows:
    raise ValueError(
        f"Expected {expected_rows} data rows "
        f"({num_workloads_expected} workloads × {num_entities_per_workload} entities), "
        f"but found {len(df)} rows after cleaning."
    )

# Assign workload ids AFTER resetting index
df["workload"] = df.index // num_entities_per_workload

# Optional: debug print each workload block
for w in range(num_workloads_expected):
    block = df[df["workload"] == w]
    print(f"\nWorkload {w}:")
    print(block.to_string(index=False))

# ==============================
# TABLE 1: Average normalized execution time
# ==============================
normalized_blocks = []

for w in range(num_workloads_expected):
    block = df[df["workload"] == w][methods].copy()
    row_min = block.min(axis=1)
    norm_block = block.div(row_min, axis=0)
    norm_block["workload"] = w
    normalized_blocks.append(norm_block)

normalized_df = pd.concat(normalized_blocks, ignore_index=True)

avg_normalized_result = (
    normalized_df.groupby("workload")[methods]
    .mean()
    .round(3)
)

avg_normalized_result.to_csv(output_csv)

print("\n=== Average Normalized Execution Time Per Workload ===")
print(avg_normalized_result.to_string())

# ==============================
# TABLE 2: Sum of raw execution time per workload
# ==============================
raw_exec_sum_result = (
    df.groupby("workload")[methods]
    .sum()
    .round(3)
)

raw_exec_sum_result.to_csv(raw_sum_output_csv)

print("\n=== Sum of Total Execution Time Per Workload ===")
print(raw_exec_sum_result.to_string())

# ==============================
# Max slowdown vs Greedy-obj-1
# ==============================

baseline_methods = [m for m in methods if m != "Greedy-obj-1"]

max_slowdowns = []

for method in baseline_methods:
    ratios = raw_exec_sum_result[method] / raw_exec_sum_result["Greedy-obj-1"]
    max_ratio = ratios.max()
    max_workload = ratios.idxmax() + 1  # +1 for 1-based indexing

    max_slowdowns.append({
        "method": method,
        "max_slowdown": round(max_ratio, 3),
        "workload": int(max_workload)
    })

max_slowdown_df = pd.DataFrame(max_slowdowns)

print("\n=== Max Slowdown vs Greedy-obj-1 for total execution time ===")
print(max_slowdown_df.to_string(index=False))

# ==============================
# LaTeX helper without pandas.to_latex()
# avoids Jinja2 dependency
# ==============================
def dataframe_to_latex_table(df_table: pd.DataFrame, caption: str, label: str) -> str:
    cols = ["workload"] + list(df_table.columns)
    col_format = "c" * len(cols)

    lines = []
    lines.append("\\begin{table}[t]")
    lines.append("\\centering")
    lines.append(f"\\caption{{{caption}}}")
    lines.append(f"\\label{{{label}}}")
    lines.append(f"\\begin{{tabular}}{{{col_format}}}")
    lines.append("\\hline")

    header = " & ".join(cols) + " \\\\"
    lines.append(header)
    lines.append("\\hline")

    for idx, row in df_table.iterrows():
        row_values = [str(idx+1)] + [f"{float(v):.3f}" for v in row.values]
        lines.append(" & ".join(row_values) + " \\\\")

    lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    return "\n".join(lines)

# ==============================
# LaTeX for normalized table
# ==============================
latex_avg_normalized = dataframe_to_latex_table(
    avg_normalized_result,
    caption="Average normalized execution time per workload",
    label="tab:avg_normalized_exec_time"
)

print("\n=== LaTeX: Average Normalized Execution Time ===")
print(latex_avg_normalized)

# ==============================
# LaTeX for raw sum table
# ==============================
latex_raw_sum = dataframe_to_latex_table(
    raw_exec_sum_result,
    caption="Sum of total execution time per workload",
    label="tab:raw_exec_time_sum"
)

print("\n=== LaTeX: Sum of Total Execution Time ===")
print(latex_raw_sum)

print(f"\nSaved normalized CSV to: {output_csv}")
print(f"Saved raw-sum CSV to: {raw_sum_output_csv}")