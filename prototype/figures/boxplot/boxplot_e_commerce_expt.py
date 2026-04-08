import csv
import matplotlib.pyplot as plt

file_path = "ER-experiments - boxplot-opt_obj_2.csv"#"ER-experiments-boxplot.csv"

data = []

# Read CSV (first row is header)
with open(file_path, newline="") as f:
    reader = csv.reader(f)
    header = next(reader)

    for row in reader:
        if row:  # skip empty rows
            data.append([float(x) for x in row])

# Normalize each row by its minimum
normalized = []
for row in data:
    row_min = min(row)
    normalized.append([x / row_min for x in row])

# Transpose rows -> columns (one list per method)
cols = list(map(list, zip(*normalized)))

means = [sum(col) / len(col) for col in cols]
for mean in means:
    print(mean)

# Create plot
fig, ax = plt.subplots(figsize=(10, 5.5))

bp = ax.boxplot(
    cols,
    tick_labels=header,
    patch_artist=True,
    showmeans=True,
    meanline=False,
    widths=0.6
)

# Light styling
for box in bp["boxes"]:
    box.set_alpha(0.7)

for median in bp["medians"]:
    median.set_linewidth(2)

for whisker in bp["whiskers"]:
    whisker.set_linewidth(1.2)

for cap in bp["caps"]:
    cap.set_linewidth(1.2)

for flier in bp["fliers"]:
    flier.set_markersize(5)
    flier.set_alpha(0.8)

for mean in bp["means"]:
    mean.set_markersize(6)
    mean.set_markerfacecolor('red')

# Labels and title
ax.set_title("", fontsize=14, pad=12)
ax.set_ylabel("Normalized execution time", fontsize=12)
ax.set_xlabel("Configuration", fontsize=12)

# Improve x labels
plt.setp(ax.get_xticklabels(), rotation=25, ha="right")

# Grid and spines
ax.grid(axis="y", linestyle="--", alpha=0.5)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Optional: uncomment if the spread is too large
ax.set_yscale("log")

fig.tight_layout()

# Save before show
#fig.savefig("boxplot.png", dpi=300, bbox_inches="tight")
fig.savefig("boxplot-opt-obj-2.png", dpi=300, bbox_inches="tight")
plt.show()