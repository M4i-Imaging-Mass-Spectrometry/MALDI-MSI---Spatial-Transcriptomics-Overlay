#!/usr/bin/env python3
"""Validate a combined Xenium output directory using lightweight consistency checks."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate combined.csv and related outputs produced by xenium_processor.py"
    )
    parser.add_argument(
        "output_dir",
        help="Directory containing combined.csv and related output files",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=3,
        help="Number of rows to inspect from combined.csv (default: 3)",
    )
    parser.add_argument(
        "--clusters",
        help="Optional path to the original clusters.csv for label cross-checking",
    )
    return parser.parse_args()


def sample_combined_rows(combined_path: Path, sample_rows: int):
    samples = []
    with combined_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader):
            if len(samples) < sample_rows:
                samples.append((idx, row))
            else:
                break
    return samples


def load_cluster_map(clusters_path: Path | None) -> dict[str, str]:
    if clusters_path is None:
        return {}

    cluster_map = {}
    with clusters_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cluster_map[row["Barcode"]] = row["Cluster"]
    return cluster_map


def load_boundary_subset(boundaries_path: Path, barcodes: list[str]) -> dict[str, list[tuple[str, str]]]:
    boundary_points = defaultdict(list)
    wanted = set(barcodes)

    with boundaries_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            barcode = row["cell_id"]
            if barcode in wanted:
                boundary_points[barcode].append((row["vertex_x"], row["vertex_y"]))

    return boundary_points


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)

    combined_path = output_dir / "combined.csv"
    boundaries_path = output_dir / "cell_boundaries.csv"

    if not combined_path.exists():
        raise FileNotFoundError(f"Missing combined.csv in {output_dir}")

    samples = sample_combined_rows(combined_path, args.sample_rows)
    if not samples:
        raise ValueError("combined.csv is empty")

    sample_barcodes = [row["Barcode"] for _, row in samples]
    clusters = load_cluster_map(Path(args.clusters) if args.clusters else None)
    boundaries = load_boundary_subset(boundaries_path, sample_barcodes) if boundaries_path.exists() else {}

    for idx, row in samples:
        gene_columns = [
            name
            for name in row.keys()
            if name not in {"Barcode", "Cluster", "Total"}
            and not name.startswith("x")
            and not name.startswith("y")
        ]
        gene_sum = sum(int(row[name]) for name in gene_columns)
        combined_coords = [
            (row[f"x{i + 1}"], row[f"y{i + 1}"])
            for i in range(25)
        ]
        boundary_coords = boundaries.get(row["Barcode"], [])[:25]

        print("---")
        print("row_index", idx)
        print("barcode", row["Barcode"])
        print("cluster_combined", row["Cluster"])
        if clusters:
            print("cluster_source", clusters.get(row["Barcode"]))
            print("cluster_match", row["Cluster"] == clusters.get(row["Barcode"]))
        print("total_value", row["Total"])
        print("sum_gene_columns", gene_sum)
        print("total_equals_gene_sum", int(row["Total"]) == gene_sum)
        if boundary_coords:
            prefix_match = combined_coords[: len(boundary_coords)] == boundary_coords
            padded_tail = combined_coords[len(boundary_coords) :]
            tail_match = (not padded_tail) or all(point == boundary_coords[-1] for point in padded_tail)
            print("boundary_prefix_match_boundaries_csv", prefix_match)
            print("boundary_padding_match", tail_match)
            print("first_3_boundary_points_combined", combined_coords[:3])
            print("first_3_boundary_points_boundaries_csv", boundary_coords[:3])


if __name__ == "__main__":
    main()
