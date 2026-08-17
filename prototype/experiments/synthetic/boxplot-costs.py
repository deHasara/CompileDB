import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
with open(csv_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# -------------------------------------------------
# Split into blocks using repeated header rows
# -------------------------------------------------
blocks = []
current_block = []

for line in lines:
    line_stripped = line.strip()

    if line_stripped.startswith("Greedy-1"):
        if current_block:
            blocks.append(current_block)
            current_block = []
        current_block.append(line)
    else:
        current_block.append(line)

if current_block:
    blocks.append(current_block)

if len(blocks) != len(workloads):
    raise ValueError(f"Expected {len(workloads)} workload blocks, but found {len(blocks)}.")

# -------------------------------------------------
# Parse each workload block
# -------------------------------------------------
all_dfs = []

for workload_name, block_lines in zip(workloads, blocks):
    block_text = "".join(block_lines)
    df_block = pd.read_csv(StringIO(block_text), header=0)

    # keep only the first 9 columns
    df_block = df_block.iloc[:, :len(configs)].copy()
    df_block.columns = configs

    # remove empty/separator rows like ,,,,,,,,
    df_block = df_block[
        df_block.apply(lambda row: pd.to_numeric(row, errors="coerce").notna().any(), axis=1)
    ].copy()

    # convert numeric
    for col in configs:
        df_block[col] = pd.to_numeric(df_block[col], errors="coerce")

    df_block = df_block.dropna(how="all").reset_index(drop=True)
    df_block["workload"] = workload_name
    df_block["entity_id"] = np.arange(1, len(df_block) + 1)

    all_dfs.append(df_block)

df = pd.concat(all_dfs, ignore_index=True)

# -------------------------------------------------
# Normalize each entity row horizontally
# -------------------------------------------------
row_min = df[configs].min(axis=1)
df_norm = df.copy()
df_norm[configs] = df[configs].div(row_min, axis=0)

# -------------------------------------------------
# Draw one boxplot per workload
# -------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(18, 8))
axes = axes.flatten()

for ax, workload in zip(axes, workloads):
    workload_df = df_norm[df_norm["workload"] == workload]

    data_for_boxplot = [workload_df[c].dropna().values for c in configs]

    bp = ax.boxplot(
        data_for_boxplot,
        tick_labels=configs,
        patch_artist=False,  # no color fill
        showmeans=True,
        meanline=False,
        widths=0.6
    )

    # Improve line visibility
    for element in ['boxes', 'whiskers', 'caps']:
        for item in bp[element]:
            item.set_linewidth(1.2)

    # Median thicker
    for median in bp['medians']:
        median.set_linewidth(2.0)

    # Mean marker
    for mean in bp['means']:
        mean.set_marker('o')
        mean.set_markersize(4)

    # log scale
    ax.set_yscale("log")

    # reference line at best = 1
    ax.axhline(1.0, linestyle='--', linewidth=1)

    # Axis formatting
    ax.set_title(workload, fontsize=12, pad=8)
    ax.set_xticks(range(1, len(configs) + 1))
    ax.set_xticklabels(configs, rotation=35, ha="right", fontsize=8)

    # Clean look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Light grid (no color specified)
    ax.grid(True, axis='y', linestyle='--', linewidth=0.5)

# Shared labels
fig.text(0.5, 0.04, 'Configuration', ha='center', fontsize=12)
fig.text(0.06, 0.5, 'Normalized Cost', va='center', rotation='vertical', fontsize=12)

plt.tight_layout(rect=[0.06, 0.05, 1, 1])

plt.savefig("boxplots_all_workloads.png", dpi=300, bbox_inches="tight")
plt.show()