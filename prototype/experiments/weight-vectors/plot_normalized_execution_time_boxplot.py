#!/usr/bin/env python3
"""Generate the normalized execution-time boxplot from the raw CSV."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


DISPLAY_LABELS = {
    "Greedy-obj-1": "Greedy-1",
    "Greedy-obj-2": "Greedy-2",
    "ABI+folded": "ABI+FIE",
    "ABI": "ABI",
    "PBI+folded": "PBI+FIE",
    "PBI": "PBI",
    "CIP+folded": "CIP+FIE",
    "CIP": "CIP",
}


def read_measurements(csv_path: Path):
    """Read numeric rows, skipping blank lines and repeated CSV headers."""
    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.reader(source)
        try:
            header = [value.strip() for value in next(reader)]
        except StopIteration as exc:
            raise ValueError(f"{csv_path} is empty") from exc

        rows = []
        for line_number, raw_row in enumerate(reader, start=2):
            if not raw_row or all(not value.strip() for value in raw_row):
                continue

            row = [value.strip() for value in raw_row]
            if row == header:  # repeated header between workload blocks
                continue
            if len(row) != len(header):
                raise ValueError(
                    f"{csv_path}:{line_number} has {len(row)} columns; "
                    f"expected {len(header)}"
                )

            try:
                rows.append([float(value) for value in row])
            except ValueError as exc:
                raise ValueError(
                    f"{csv_path}:{line_number} contains a nonnumeric value"
                ) from exc

    return header, rows


def average_normalized_times(rows, workloads: int, components: int):
    """Return one average normalized value per workload and configuration."""
    expected_rows = workloads * components
    if len(rows) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} measurements "
            f"({workloads} workloads x {components} components), "
            f"but found {len(rows)}"
        )

    workload_averages = []
    for workload in range(workloads):
        start = workload * components
        block = rows[start : start + components]

        normalized_block = []
        for component, row in enumerate(block, start=1):
            row_min = min(row)
            if row_min <= 0:
                raise ValueError(
                    f"Workload {workload + 1}, component {component} "
                    f"has a nonpositive minimum ({row_min})"
                )
            normalized_block.append([value / row_min for value in row])

        column_count = len(block[0])
        workload_averages.append(
            [
                sum(row[column] for row in normalized_block) / components
                for column in range(column_count)
            ]
        )

    return workload_averages


def draw_boxplot(header, workload_averages, output_path: Path):
    columns = list(map(list, zip(*workload_averages)))
    labels = [DISPLAY_LABELS.get(name, name) for name in header]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    boxplot = ax.boxplot(
        columns,
        tick_labels=labels,
        patch_artist=True,
        showmeans=True,
        meanline=False,
        widths=0.6,
    )

    for box in boxplot["boxes"]:
        box.set_alpha(0.7)
    for median in boxplot["medians"]:
        median.set_linewidth(2)
    for whisker in boxplot["whiskers"]:
        whisker.set_linewidth(1.2)
    for cap in boxplot["caps"]:
        cap.set_linewidth(1.2)
    for flier in boxplot["fliers"]:
        flier.set_markersize(5)
        flier.set_alpha(0.8)
    for mean in boxplot["means"]:
        mean.set_markersize(6)
        mean.set_markerfacecolor("red")

    ax.set_yscale("log")
    ax.set_ylabel("Normalized execution time", fontsize=18)
    ax.set_xlabel("Configuration", fontsize=18)
    ax.tick_params(axis="both", labelsize=14)
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")

    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Plot average normalized execution time across workloads."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("ER-experiments - Sheet17.csv"),
        help="Raw execution-time CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("normalized_execution_time_boxplot_12_workloads.png"),
        help="Output PNG path",
    )
    parser.add_argument("--workloads", type=int, default=12)
    parser.add_argument("--components-per-workload", type=int, default=11)
    args = parser.parse_args()

    header, rows = read_measurements(args.input)
    workload_averages = average_normalized_times(
        rows,
        workloads=args.workloads,
        components=args.components_per_workload,
    )
    draw_boxplot(header, workload_averages, args.output)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
