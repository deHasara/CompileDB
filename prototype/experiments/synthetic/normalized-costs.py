import pandas as pd
import numpy as np
from io import StringIO

csv_path = "ER-experiments - Sheet19.csv"

workloads = ["RR", "RL", "LR", "IL", "LI", "LL"]

configs = [
    "Greedy-1",
    "Greedy-2",
    "ABI",
    "PBI",
    "CIP",
    "(ABI,CIP,ABI)",
    "(ABI,PBI,ABI)",
    "(ABI,ABI,CIP)",
    "(ABI,ABI,PBI)",
]

# -------------------------------------------------
# Read raw lines
# -------------------------------------------------
with open(csv_path, "r") as f:
    lines = f.readlines()

# -------------------------------------------------
# Split into blocks using header lines
# -------------------------------------------------
blocks = []
current_block = []

for line in lines:
    line_stripped = line.strip()

    # detect header line
    if line_stripped.startswith("Greedy-1"):
        if current_block:
            blocks.append(current_block)
            current_block = []
        current_block.append(line)
    else:
        current_block.append(line)

if current_block:
    blocks.append(current_block)

print("Detected blocks:", len(blocks))

# -------------------------------------------------
# Parse each workload block
# -------------------------------------------------
all_dfs = []

for workload_name, block_lines in zip(workloads, blocks):
    block_text = "".join(block_lines)

    df_block = pd.read_csv(StringIO(block_text), header=0)

    # keep only needed columns
    df_block = df_block.iloc[:, :len(configs)]
    df_block.columns = configs

    # remove rows like ",,,,,"
    df_block = df_block[
        df_block.apply(lambda row: pd.to_numeric(row, errors="coerce").notna().any(), axis=1)
    ]

    # convert numeric
    for col in configs:
        df_block[col] = pd.to_numeric(df_block[col], errors="coerce")

    df_block = df_block.dropna(how="all").reset_index(drop=True)

    df_block["workload"] = workload_name

    all_dfs.append(df_block)

df = pd.concat(all_dfs, ignore_index=True)

# -------------------------------------------------
# (1) Normalize per entity row
# -------------------------------------------------
row_min = df[configs].min(axis=1)
df_norm = df.copy()
df_norm[configs] = df[configs].div(row_min, axis=0)

avg_norm_table = (
    df_norm.groupby("workload")[configs]
    .mean()
    .reindex(workloads)
)

# -------------------------------------------------
# (2) Sum raw cost
# -------------------------------------------------
sum_raw_table = (
    df.groupby("workload")[configs]
    .sum()
    .reindex(workloads)
)

sum_norm_table = sum_raw_table.div(sum_raw_table.min(axis=1), axis=0)

# -------------------------------------------------
# OUTPUT
# -------------------------------------------------
print("\n=== (1) Avg Normalized Cost ===")
print(avg_norm_table.round(3).to_string())

print("\n=== (2) Normalized Sum Cost ===")
print(sum_norm_table.round(3).to_string())

# -------------------------------------------------
# Pretty names for LaTeX columns
# -------------------------------------------------
latex_column_names = {
    "Greedy-1": "Greedy-1",
    "Greedy-2": "Greedy-2",
    "ABI": "ABI",
    "PBI": "PBI",
    "CIP": "CIP",
    "(ABI,CIP,ABI)": "$(ABI,CIP,ABI)$",
    "(ABI,PBI,ABI)": "$(ABI,PBI,ABI)$",
    "(ABI,ABI,CIP)": "$(ABI,ABI,CIP)$",
    "(ABI,ABI,PBI)": "$(ABI,ABI,PBI)$",
}

avg_norm_latex_table = avg_norm_table.rename(columns=latex_column_names).round(3)
sum_norm_latex_table = sum_norm_table.rename(columns=latex_column_names).round(3)

# -------------------------------------------------
# Print LaTeX tables
# -------------------------------------------------
print("\n=== LaTeX: Avg Normalized Cost ===")
print(
    avg_norm_latex_table.to_latex(
        index=True,
        escape=False,
        float_format="%.3f",
        caption="Average normalized cost for each workload and configuration.",
        label="tab:avg_normalized_cost",
    )
)

print("\n=== LaTeX: Normalized Sum Cost ===")
print(
    sum_norm_latex_table.to_latex(
        index=True,
        escape=False,
        float_format="%.3f",
        caption="Normalized sum of raw costs for each workload and configuration.",
        label="tab:normalized_sum_cost",
    )
)




