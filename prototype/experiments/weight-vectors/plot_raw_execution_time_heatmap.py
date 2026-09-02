#!/usr/bin/env python3
"""Generate the raw execution-time heatmap from component-level CSV data.

The input CSV may contain repeated header rows and blank rows between workload
blocks. Each workload is assumed to contain the same number of components.
Execution times are summed within each workload, converted from milliseconds
to seconds, and displayed using logarithmic color normalization.
"""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


DISPLAY_LABELS = {
    "Greedy-obj-1": "Obj-1",
    "Greedy-obj-2": "Obj-2",
    "ABI+folded": "+FIE",
    "ABI": "Base",
    "PBI+folded": "+FIE",
    "PBI": "Base",
    "CIP+folded": "+FIE",
    "CIP": "Base",
}

EXPECTED_METHODS = [
    "Greedy-obj-1",
    "Greedy-obj-2",
    "ABI+folded",
    "ABI",
    "PBI+folded",
    "PBI",
    "CIP+folded",
    "CIP",
]

GROUP_LABELS = ["GREEDY", "ABI", "PBI", "CIP"]
GROUP_CENTERS = [0.5, 2.5, 4.5, 6.5]


def read_measurements(csv_path: Path):
    """Read numeric rows while skipping blank and repeated-header rows."""
    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.reader(source)
        try:
            header = [value.strip() for value in next(reader)]
        except StopIteration as exc:
            raise ValueError(f"{csv_path} is empty") from exc

        if header != EXPECTED_METHODS:
            raise ValueError(
                "Unexpected CSV columns.\n"
                f"Expected: {EXPECTED_METHODS}\n"
                f"Found:    {header}"
            )

        rows = []
        for line_number, raw_row in enumerate(reader, start=2):
            if not raw_row or all(not value.strip() for value in raw_row):
                continue

            row = [value.strip() for value in raw_row]
            if row == header:
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

    return header, np.asarray(rows, dtype=float)


def sum_by_workload(rows: np.ndarray, workloads: int, components: int):
    """Return an array containing total milliseconds per workload and method."""
    expected_rows = workloads * components
    if rows.shape != (expected_rows, len(EXPECTED_METHODS)):
        raise ValueError(
            f"Expected {expected_rows} data rows "
            f"({workloads} workloads x {components} components), "
            f"but found {rows.shape[0]}"
        )

    return rows.reshape(workloads, components, len(EXPECTED_METHODS)).sum(axis=1)


def draw_heatmap(header, raw_ms: np.ndarray, output_path: Path):
    """Draw the grouped logarithmic heatmap and save it as a PNG."""
    seconds = raw_ms / 1000.0
    if np.any(seconds <= 0):
        raise ValueError("Logarithmic coloring requires positive execution times")

    column_labels = [DISPLAY_LABELS[name] for name in header]

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "text.color": "#17212B",
            "axes.labelcolor": "#17212B",
            "xtick.color": "#26313B",
            "ytick.color": "#26313B",
        }
    )

    fig, ax = plt.subplots(figsize=(16, 9), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    cmap = mcolors.LinearSegmentedColormap.from_list(
        "execution_blues",
        ["#F3F8FC", "#D5E8F5", "#8AB9D9", "#367BAA", "#123E63"],
    )

    # Fixed limits make figures directly comparable across runs of this
    # experiment. Use --dynamic-scale for another data range.
    norm = mcolors.LogNorm(vmin=0.75, vmax=200.0)
    image = ax.imshow(
        seconds,
        cmap=cmap,
        norm=norm,
        aspect="auto",
        interpolation="nearest",
    )

    # Cell borders and stronger separators between the four mapping families.
    ax.set_xticks(np.arange(-0.5, seconds.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, seconds.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.25)
    ax.tick_params(which="minor", bottom=False, left=False)
    for boundary in [1.5, 3.5, 5.5]:
        ax.axvline(boundary, color="white", linewidth=5.0, zorder=4)
        ax.axvline(boundary, color="#43596A", linewidth=1.6, zorder=5)

    ax.set_xticks(np.arange(seconds.shape[1]))
    ax.set_xticklabels(column_labels, fontsize=17, fontweight="semibold")
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", length=0, pad=12)

    ax.set_yticks(np.arange(seconds.shape[0]))
    ax.set_yticklabels(
        [f"W{i}" for i in range(1, seconds.shape[0] + 1)],
        fontsize=16,
        fontweight="semibold",
    )
    ax.tick_params(axis="y", length=0, pad=12)
    ax.set_ylabel("Workload", fontsize=18, fontweight="bold", labelpad=18)

    for center, label in zip(GROUP_CENTERS, GROUP_LABELS):
        ax.text(
            center,
            1.105,
            label,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="bottom",
            fontsize=18,
            fontweight="bold",
            color="#155FA0" if label == "GREEDY" else "#3F4B55",
            clip_on=False,
        )

    # Display seconds to one decimal place and outline the exact row minimum.
    for row in range(seconds.shape[0]):
        winner = int(np.argmin(seconds[row]))
        for column in range(seconds.shape[1]):
            value = seconds[row, column]
            rgba = cmap(norm(value))
            luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
            text_color = "#FFFFFF" if luminance < 0.53 else "#14212C"
            ax.text(
                column,
                row,
                f"{value:.1f}",
                ha="center",
                va="center",
                fontsize=17,
                fontweight="bold" if column == winner else "semibold",
                color=text_color,
                zorder=7,
            )

        ax.add_patch(
            patches.Rectangle(
                (winner - 0.47, row - 0.47),
                0.94,
                0.94,
                fill=False,
                edgecolor="#00A6D6",
                linewidth=3.2,
                zorder=8,
            )
        )

    for spine in ax.spines.values():
        spine.set_visible(False)

    cbar = fig.colorbar(image, ax=ax, fraction=0.032, pad=0.025)
    cbar.set_label(
        "Total execution time (seconds, log scale)",
        fontsize=16,
        fontweight="semibold",
        labelpad=15,
    )
    cbar_ticks = [1, 2, 5, 10, 20, 50, 100, 200]
    cbar.set_ticks(cbar_ticks)
    cbar.ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda value, _: f"{value:g} s")
    )
    cbar.ax.tick_params(labelsize=13, length=0, pad=7)
    cbar.ax.minorticks_off()
    cbar.outline.set_edgecolor("#AEB7BF")
    cbar.outline.set_linewidth(0.8)

    fig.subplots_adjust(left=0.09, right=0.90, top=0.88, bottom=0.09)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a raw execution-time heatmap from a workload CSV."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("ER-experiments - Sheet17.csv"),
        help="Component-level execution-time CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("raw_execution_time_1_6_th_workload_heatmap.png"),
        help="Output PNG path",
    )
    parser.add_argument("--workloads", type=int, default=12)
    parser.add_argument("--components-per-workload", type=int, default=11)
    args = parser.parse_args()

    header, rows = read_measurements(args.input)
    raw_ms = sum_by_workload(
        rows,
        workloads=args.workloads,
        components=args.components_per_workload,
    )
    draw_heatmap(header, raw_ms, args.output)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
