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

# use normalized dataframe for plotting
df_plot = df_norm.copy()

# optional: clip only for visualization
# CLIP_MAX = 50
# df_plot[configs] = df_plot[configs].clip(upper=CLIP_MAX)

# consistent y-range across all subplots
global_min = 0#df_plot[configs].min().min()
global_max = df_plot[configs].max().max()

# -------------------------------------------------
# Draw one boxplot per workload
# -------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(18, 8), sharey=True)
axes = axes.flatten()

for ax, workload in zip(axes, workloads):
    workload_df = df_plot[df_plot["workload"] == workload]
    data_for_boxplot = [workload_df[c].dropna().values for c in configs]

    bp = ax.boxplot(
        data_for_boxplot,
        labels=configs,
        patch_artist=True,
        showmeans=True,
        widths=0.6,
        meanprops=dict(
            marker='^',
            markerfacecolor='red',
            markeredgecolor='black',
            markersize=6,
            markeredgewidth=0.5
        ),
        boxprops=dict(linewidth=1.2),
        whiskerprops=dict(linewidth=1.1),
        capprops=dict(linewidth=1.1),
        medianprops=dict(linewidth=2.0),
        flierprops=dict(
            marker="o",
            markersize=3,
            markerfacecolor="none",
            linestyle="none"
        ),
    )

    # Filled boxes
    for box in bp["boxes"]:
        box.set_alpha(0.7)

    # Slightly stronger medians
    for median in bp["medians"]:
        median.set_linewidth(2.2)

    ax.set_yscale("log")
    ax.set_ylim(global_min, global_max)

    ax.set_yticks([1, 2, 5, 10, 20, 50, 100])

    # Reference line at optimal normalized cost
    ax.axhline(1.0, linestyle="--", linewidth=1.5)

    ax.set_title(workload, fontsize=12, pad=8)
    ax.tick_params(axis="x", labelrotation=25, labelsize=8)

    ax.grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# Shared labels
fig.text(0.5, 0.04, "Configuration", ha="center", fontsize=13)
fig.text(0.06, 0.5, "Normalized Cost (log scale)", va="center", rotation="vertical", fontsize=13)

plt.tight_layout(rect=[0.07, 0.06, 1, 1])
plt.savefig("boxplots_all_workloads_1.png", dpi=300, bbox_inches="tight")
plt.show()