import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def read_numeric_csv(path):
    """Return the header and numeric rows from a CSV file."""
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"{path} is empty") from exc

        rows = []
        for line_number, row in enumerate(reader, start=2):
            if not row or all(not value.strip() for value in row):
                continue
            if len(row) != len(header):
                raise ValueError(
                    f"{path}:{line_number} has {len(row)} values; "
                    f"expected {len(header)}"
                )
            try:
                rows.append([float(value) for value in row])
            except ValueError as exc:
                raise ValueError(
                    f"{path}:{line_number} contains a non-numeric value"
                ) from exc

    return header, rows


def combine_configurations(greedy1_path, greedy2_path):
    """Combine Greedy-1 with Greedy-2 and the six shared baselines."""
    header1, rows1 = read_numeric_csv(greedy1_path)
    header2, rows2 = read_numeric_csv(greedy2_path)

    if header1[0] != "Greedy-1":
        raise ValueError(f"Expected Greedy-1 as the first column of {greedy1_path}")
    if header2[0] != "Greedy-2":
        raise ValueError(f"Expected Greedy-2 as the first column of {greedy2_path}")
    if header1[1:] != header2[1:]:
        raise ValueError("The baseline headers do not match between the two CSV files")
    if len(rows1) != len(rows2):
        raise ValueError("The two CSV files contain different numbers of workloads")

    combined = []
    for workload, (row1, row2) in enumerate(zip(rows1, rows2), start=1):
        if row1[1:] != row2[1:]:
            raise ValueError(
                f"The shared baseline values differ for workload {workload}"
            )
        combined.append([row1[0], row2[0], *row2[1:]])

    return [header1[0], header2[0], *header2[1:]], combined


def main():
    parser = argparse.ArgumentParser(
        description="Plot row-normalized execution times for eight configurations."
    )
    parser.add_argument(
        "--greedy1-csv",
        type=Path,
        default=Path("ER-experiments-boxplot.csv"),
        help="CSV whose first column is Greedy-1",
    )
    parser.add_argument(
        "--greedy2-csv",
        type=Path,
        default=Path("ER-experiments - boxplot-opt_obj_2.csv"),
        help="CSV whose first column is Greedy-2",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("boxplot-all-8-configurations.png"),
        help="Output plot path",
    )
    args = parser.parse_args()

    header, data = combine_configurations(args.greedy1_csv, args.greedy2_csv)

    # Normalize every workload by the best of all eight configurations.
    normalized = []
    for workload, row in enumerate(data, start=1):
        row_min = min(row)
        if row_min <= 0:
            raise ValueError(
                f"Workload {workload} has a non-positive minimum ({row_min})"
            )
        normalized.append([value / row_min for value in row])

    columns = list(map(list, zip(*normalized)))
    means = [sum(column) / len(column) for column in columns]
    for label, mean in zip(header, means):
        print(f"{label}: {mean:.6f}")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bp = ax.boxplot(
        columns,
        tick_labels=header,
        patch_artist=True,
        showmeans=True,
        meanline=False,
        widths=0.6,
    )

    # Match the style of the reference boxplot.
    for box in bp["boxes"]:
        box.set_facecolor("#1f77b4")
        box.set_edgecolor("black")
        box.set_alpha(0.7)

    for median in bp["medians"]:
        median.set_color("#ff7f0e")
        median.set_linewidth(2)
    for whisker in bp["whiskers"]:
        whisker.set_color("black")
        whisker.set_linewidth(1.2)
    for cap in bp["caps"]:
        cap.set_color("black")
        cap.set_linewidth(1.2)
    for flier in bp["fliers"]:
        flier.set_markerfacecolor("none")
        flier.set_markeredgecolor("black")
        flier.set_markersize(5)
        flier.set_alpha(0.8)
    for mean in bp["means"]:
        mean.set_marker("^")
        mean.set_markersize(10)
        mean.set_markerfacecolor("red")
        mean.set_markeredgecolor("black")
        mean.set_markeredgewidth(1.2)

    ax.set_ylabel("Normalized execution time", fontsize=18)
    ax.set_xlabel("Configuration", fontsize=18)
    ax.tick_params(axis="both", labelsize=14)
    ax.set_yscale("log")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")

    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
