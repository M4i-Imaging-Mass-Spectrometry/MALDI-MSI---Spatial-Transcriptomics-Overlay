#!/usr/bin/env python3
"""
Convert 10x Xenium outputs into EscDat-compatible CSV and GeoJSON overlays.

The script supports two common Xenium layouts:
1. Legacy-style outputs that include ``features.tsv.gz`` and
   ``cell_feature_matrix.zarr.zip``.
2. Newer Xenium outputs that expose feature metadata through
   ``cell_features/.zattrs`` and may require recovering polygons from the
   root ``polygon_sets/`` zarr group when CSV boundary files are unavailable.

Usage:
    python xenium_processor.py <xenium_folder> [--filter <cell_list.csv>]
                               [--output <output_dir>] [--allow-large-run]
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import zarr


BARCODE_HEX_ALPHABET = "abcdefghijklmnop"
DEFAULT_OUTPUT_DIR = "./xenium_output"
MAX_BOUNDARY_VERTICES = 25
MAX_DENSE_VALUES = 250_000_000


def decode_encoded_cell_id(encoded_pair: np.ndarray) -> str:
    """Decode Xenium uint32 barcode pairs like [27196, 1] -> aaaagkdm-1."""
    prefix, suffix = (int(encoded_pair[0]), int(encoded_pair[1]))
    hex_digits = f"{prefix:08x}"
    # Xenium stores barcodes as packed hexadecimal symbols where 0-15 map to
    # a-p. Expanding those nibbles recreates the familiar 8-letter barcode stem.
    letters = "".join(BARCODE_HEX_ALPHABET[int(digit, 16)] for digit in hex_digits)
    return f"{letters}-{suffix}"


def normalize_cell_ids(values: np.ndarray) -> list[str]:
    """Convert cell identifiers from zarr arrays into readable barcode strings."""
    arr = np.asarray(values)

    if arr.ndim == 2 and arr.shape[1] == 2 and np.issubdtype(arr.dtype, np.integer):
        return [decode_encoded_cell_id(row) for row in arr]

    normalized = []
    for value in arr:
        if isinstance(value, bytes):
            normalized.append(value.decode("utf-8"))
        else:
            normalized.append(str(value))
    return normalized


def is_dataless_placeholder(path: Path) -> bool:
    """Detect macOS/iCloud placeholder files that have a size but no local blocks."""
    try:
        stats = path.stat()
    except FileNotFoundError:
        return False

    return stats.st_size > 0 and getattr(stats, "st_blocks", 1) == 0


def deduplicate_names(names: Iterable[str]) -> list[str]:
    """Ensure feature names are unique for use as CSV column names."""
    seen = {}
    unique_names = []

    for name in names:
        count = seen.get(name, 0)
        if count == 0:
            unique_names.append(name)
        else:
            unique_names.append(f"{name}_{count + 1}")
        seen[name] = count + 1

    return unique_names


def unique_preserving_order(values: Iterable[str]) -> list[str]:
    """Deduplicate strings while preserving the first occurrence of each item."""
    seen = set()
    ordered = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def read_filter_barcodes(filter_file: str | Path) -> list[str]:
    """Read a user-provided cell list and return the requested barcodes."""
    small = pd.read_csv(filter_file, comment="#")

    if "cell_id" in small.columns:
        id_col = "cell_id"
    elif "Barcode" in small.columns:
        id_col = "Barcode"
    else:
        id_col = small.columns[0]

    return unique_preserving_order(small[id_col].dropna().astype(str).tolist())


def find_xenium_files(base_path: str | Path) -> dict[str, Path]:
    """Find all required files and compatible fallbacks in the directory tree."""
    base = Path(base_path)

    print("Searching for required files...")

    file_patterns = {
        "zarr": "cell_feature_matrix.zarr.zip",
        "boundaries": "cell_boundaries.csv.gz",
        "clusters": "clusters.csv",
        "features": "features.tsv.gz",
    }

    alt_patterns = {
        "boundaries": ["cell_boundaries.csv", "cell_boundaries.parquet"],
    }

    found_files = {}

    for name, pattern in file_patterns.items():
        print(f"  Looking for {pattern}...")
        matches = list(base.rglob(pattern))

        if not matches and name in alt_patterns:
            for alt_pattern in alt_patterns[name]:
                print(f"    Not found, trying {alt_pattern}...")
                matches = list(base.rglob(alt_pattern))
                if matches:
                    break

        if matches:
            if len(matches) > 1 and name == "clusters":
                preferred = [m for m in matches if "gene_expression_graphclust" in str(m)]
                if preferred:
                    matches = preferred

            if len(matches) > 1:
                print(f"    Warning: Found {len(matches)} matches for {pattern}, using: {matches[0]}")

            found_files[name] = matches[0]
            print(f"    ✓ Found: {matches[0].relative_to(base)}")
        else:
            print("    ✗ Not found!")

    cell_features_dir = base / "cell_features"
    if cell_features_dir.is_dir():
        found_files["cell_features_dir"] = cell_features_dir
        print("  ✓ Found compatible cell_features/ zarr directory")

    feature_attrs = base / "cell_features" / ".zattrs"
    if feature_attrs.is_file():
        found_files["feature_attrs"] = feature_attrs
        print("  ✓ Found feature metadata in cell_features/.zattrs")

    if (base / ".zgroup").is_file() and (base / "polygon_sets").is_dir():
        found_files["polygon_root"] = base
        print("  ✓ Found polygon_sets/ zarr group for boundary fallback")

    missing = []
    if "zarr" not in found_files and "cell_features_dir" not in found_files:
        missing.append("cell_feature_matrix.zarr.zip or cell_features/")
    if "boundaries" not in found_files and "polygon_root" not in found_files:
        missing.append("cell_boundaries.csv(.gz/.parquet) or polygon_sets/")
    if "clusters" not in found_files:
        missing.append("clusters.csv")
    if "features" not in found_files and "feature_attrs" not in found_files:
        missing.append("features.tsv.gz or cell_features/.zattrs")

    if missing:
        print("\nERROR: Could not find required files:")
        for item in missing:
            print(f"  - {item}")
        print(f"\nSearched in: {base}")
        print("Please ensure all required files are present somewhere in the directory tree.")
        sys.exit(1)

    return found_files


def write_feature_metadata(work_dir: Path, feature_rows: list[int], feature_names: list[str]) -> None:
    """Persist the row-selection manifest used to build dense output tables."""
    pd.DataFrame({"row_index": feature_rows, "feature_name": feature_names}).to_csv(
        work_dir / "feature_metadata.csv",
        index=False,
    )
    with open(work_dir / "feature_list.csv", "w") as handle:
        for name in feature_names:
            handle.write(f"{name}\n")


def load_feature_metadata(xenium_files: dict[str, Path]) -> tuple[list[int], list[str]]:
    """Load feature names and matrix row indices for gene features plus total counts."""
    if "feature_attrs" in xenium_files:
        with open(xenium_files["feature_attrs"], "r") as handle:
            attrs = json.load(handle)

        feature_keys = attrs.get("feature_keys", attrs.get("feature_ids", []))
        feature_types = attrs.get("feature_types", ["gene"] * len(feature_keys))

        selected_rows = []
        selected_names = []
        for index, (name, feature_type) in enumerate(zip(feature_keys, feature_types)):
            # Ignore negative controls and codeword-only channels so the dense
            # matrix matches the biological feature set used downstream.
            if feature_type not in {"gene", "aggregate_gene"}:
                continue

            if feature_type == "aggregate_gene" and "total" in name.lower():
                selected_names.append("Total")
            else:
                selected_names.append(name)
            selected_rows.append(index)

        if not selected_rows:
            raise ValueError("No gene features were found in cell_features/.zattrs.")

        return selected_rows, deduplicate_names(selected_names)

    with gzip.open(xenium_files["features"], "rt") as handle:
        lines = handle.readlines()

    gene_names = [line.split("\t")[1].strip() for line in lines]
    gene_names.append("Total")
    return list(range(len(gene_names))), deduplicate_names(gene_names)


def choose_polygon_group(polygon_sets: zarr.hierarchy.Group) -> zarr.hierarchy.Group:
    """Prefer the full cell boundary polygon set when multiple sets exist."""
    if "1" in polygon_sets:
        return polygon_sets["1"]

    return max(
        (polygon_sets[key] for key in polygon_sets.keys()),
        key=lambda group: group["cell_index"].shape[0],
    )


def write_boundaries_from_polygon_sets(
    root_path: str | Path,
    output_path: Path,
    selected_barcodes: list[str] | None = None,
) -> None:
    """Materialize cell boundaries from the local Xenium zarr tree."""
    root = zarr.open(Path(root_path), mode="r")
    polygon_group = choose_polygon_group(root["polygon_sets"])

    all_cell_ids = normalize_cell_ids(np.array(root["cell_id"]))
    cell_index = np.array(polygon_group["cell_index"])
    num_vertices = np.array(polygon_group["num_vertices"])
    vertices = np.array(polygon_group["vertices"])

    selected_set = set(selected_barcodes) if selected_barcodes else None
    rows = []

    for polygon_cell_index, vertex_count, flattened_vertices in zip(cell_index, num_vertices, vertices):
        barcode = all_cell_ids[int(polygon_cell_index)]
        if selected_set is not None and barcode not in selected_set:
            continue

        coords = flattened_vertices[: vertex_count * 2].reshape(-1, 2)
        for vertex_x, vertex_y in coords:
            rows.append(
                {
                    "cell_id": barcode,
                    "vertex_x": float(vertex_x),
                    "vertex_y": float(vertex_y),
                }
            )

    pd.DataFrame(rows).to_csv(output_path, index=False)


def load_boundary_table(boundaries_path: Path) -> pd.DataFrame:
    """Load boundary coordinates from CSV, gzipped CSV, or parquet."""
    if boundaries_path.suffix == ".gz":
        with gzip.open(boundaries_path, "rb") as f_in:
            return pd.read_csv(f_in)

    if boundaries_path.suffix == ".parquet":
        try:
            return pd.read_parquet(boundaries_path)
        except ImportError as exc:
            raise ImportError(
                "Reading .parquet boundary files requires the optional 'pyarrow' "
                "dependency. Install it with 'pip install pyarrow' or provide a "
                "CSV boundary file instead."
            ) from exc

    return pd.read_csv(boundaries_path)


def prepare_working_directory(
    xenium_files: dict[str, Path],
    output_dir: str | Path,
    selected_barcodes: list[str] | None = None,
) -> Path:
    """Copy or extract inputs into the working directory."""
    work_dir = Path(output_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    print("\nPreparing files...")

    feature_rows, feature_names = load_feature_metadata(xenium_files)
    write_feature_metadata(work_dir, feature_rows, feature_names)

    boundaries_path = xenium_files.get("boundaries")
    use_polygon_fallback = (
        "polygon_root" in xenium_files
        and (
            boundaries_path is None
            or is_dataless_placeholder(boundaries_path)
        )
    )

    if use_polygon_fallback:
        print("  Building cell_boundaries.csv from polygon_sets/...")
        write_boundaries_from_polygon_sets(
            xenium_files["polygon_root"],
            work_dir / "cell_boundaries.csv",
            selected_barcodes=selected_barcodes,
        )
    else:
        load_boundary_table(boundaries_path).to_csv(work_dir / "cell_boundaries.csv", index=False)

    shutil.copy2(xenium_files["clusters"], work_dir / "clusters.csv")
    return work_dir


def open_cell_feature_group(xenium_files: dict[str, Path]):
    """Open the sparse cell-feature matrix from either a zarr directory or zipped zarr."""
    if "cell_features_dir" in xenium_files:
        return zarr.open(xenium_files["cell_features_dir"], mode="r")

    result = zarr.open(xenium_files["zarr"], mode="r")
    if hasattr(result, "keys") and "cell_features" in result:
        return result["cell_features"]
    return result.cell_features


def estimate_dense_matrix_size_gib(feature_count: int, cell_count: int) -> float:
    """Estimate RAM required for a uint32 dense matrix."""
    return (feature_count * cell_count * 4) / (1024 ** 3)


def run_zarr_reader(
    work_dir: Path,
    xenium_files: dict[str, Path],
    selected_barcodes: list[str] | None = None,
    allow_large_run: bool = False,
) -> None:
    """Read the sparse Xenium matrix and materialize the selected dense subset."""
    print("\nStep 1/3: Reading zarr file...")

    cell_features = open_cell_feature_group(xenium_files)
    feature_rows = pd.read_csv(work_dir / "feature_metadata.csv")["row_index"].tolist()

    data = np.array(cell_features["data"])
    indices = np.array(cell_features["indices"])
    indptr = np.array(cell_features["indptr"])
    cell_ids = normalize_cell_ids(np.array(cell_features["cell_id"]))

    if selected_barcodes:
        requested = set(selected_barcodes)
        selected_global_indices = [i for i, barcode in enumerate(cell_ids) if barcode in requested]
        selected_cell_ids = [cell_ids[i] for i in selected_global_indices]

        missing = sorted(requested - set(selected_cell_ids))
        if missing:
            print(f"  Warning: {len(missing)} requested barcodes were not found in the matrix.")

        if not selected_global_indices:
            raise ValueError("No requested barcodes were found in the cell-feature matrix.")
    else:
        selected_global_indices = list(range(len(cell_ids)))
        selected_cell_ids = cell_ids

    estimated_values = len(feature_rows) * len(selected_global_indices)
    if estimated_values > MAX_DENSE_VALUES and not allow_large_run:
        approx_gb = estimate_dense_matrix_size_gib(len(feature_rows), len(selected_global_indices))
        raise MemoryError(
            "This Xenium dataset is too large for the script's dense export path "
            f"({len(feature_rows):,} features x {len(selected_global_indices):,} cells, "
            f"about {approx_gb:.1f} GiB just for the count matrix). "
            "Please run with --filter to limit cells for debugging, or rerun with "
            "--allow-large-run if you intentionally want the full dense export."
        )

    dense = np.zeros((len(feature_rows), len(selected_global_indices)), dtype=np.uint32)
    global_to_local = np.full(len(cell_ids), -1, dtype=np.int64)
    global_to_local[selected_global_indices] = np.arange(len(selected_global_indices), dtype=np.int64)

    for out_row, feature_row in enumerate(feature_rows):
        if out_row % 250 == 0:
            print(f"  Processing feature row {out_row + 1}/{len(feature_rows)}")

        start = int(indptr[feature_row])
        end = int(indptr[feature_row + 1])
        index_slice = indices[start:end]
        data_slice = data[start:end]
        local_indices = global_to_local[index_slice]
        mask = local_indices >= 0

        if np.any(mask):
            np.add.at(dense[out_row], local_indices[mask], data_slice[mask])

    np.savetxt(work_dir / "gene_features.csv", dense.T, fmt="%u", delimiter=",")
    pd.DataFrame({"Barcode": selected_cell_ids}).to_csv(work_dir / "cell_ids.csv", index=False)
    print("  ✓ gene_features.csv created")
    print("  ✓ cell_ids.csv created")


def run_combiner(work_dir: Path) -> None:
    """Combine features, clusters, and boundary coordinates into one table."""
    print("\nStep 2/3: Combining data...")

    boundaries = pd.read_csv(work_dir / "cell_boundaries.csv")
    features = pd.read_csv(work_dir / "gene_features.csv", header=None)
    clusters = pd.read_csv(work_dir / "clusters.csv")
    cell_ids = pd.read_csv(work_dir / "cell_ids.csv")

    with open(work_dir / "feature_list.csv", "r") as handle:
        feature_names = [line.strip() for line in handle.readlines()]
        features.columns = feature_names

    if len(cell_ids) != len(features):
        raise ValueError(
            f"Barcode count ({len(cell_ids)}) does not match feature rows ({len(features)})."
        )

    boundaries["cell_id"] = boundaries["cell_id"].astype(str)
    clusters["Barcode"] = clusters["Barcode"].astype(str)
    features = pd.concat(
        [cell_ids["Barcode"].astype(str).rename("Barcode"), features],
        axis=1,
    )

    assigned = set(clusters["Barcode"])
    unassigned = set(features["Barcode"]) - assigned

    features = features[~features["Barcode"].isin(unassigned)].reset_index(drop=True)
    boundaries = boundaries[~boundaries["cell_id"].isin(unassigned)].reset_index(drop=True)

    clusters = clusters[["Barcode", "Cluster"]].drop_duplicates(subset="Barcode", keep="first")
    features = features.merge(clusters, on="Barcode", how="left")
    features = features[["Barcode", "Cluster", *feature_names]]

    n_cells = features.shape[0]
    max_verts = MAX_BOUNDARY_VERTICES

    x_zeros = np.zeros((n_cells, max_verts))
    y_zeros = np.zeros((n_cells, max_verts))

    cell_to_idx = {cell_id: idx for idx, cell_id in enumerate(features["Barcode"])}

    print("  Processing cell boundaries...")
    for cell_id, group in boundaries.groupby("cell_id"):
        if cell_id not in cell_to_idx:
            continue

        idx = cell_to_idx[cell_id]
        coords = group[["vertex_x", "vertex_y"]].values
        n_coords = coords.shape[0]

        if n_coords >= max_verts:
            x_zeros[idx, :] = coords[:max_verts, 0]
            y_zeros[idx, :] = coords[:max_verts, 1]
        else:
            x_zeros[idx, :n_coords] = coords[:, 0]
            y_zeros[idx, :n_coords] = coords[:, 1]
            x_zeros[idx, n_coords:] = coords[-1, 0]
            y_zeros[idx, n_coords:] = coords[-1, 1]

    coordinate_columns = {}
    for index in range(max_verts):
        coordinate_columns[f"x{index + 1}"] = x_zeros[:, index]
        coordinate_columns[f"y{index + 1}"] = y_zeros[:, index]

    features = pd.concat([features, pd.DataFrame(coordinate_columns)], axis=1)

    features.to_csv(work_dir / "combined.csv", index=False)
    print("  ✓ combined.csv created")


def run_geojson_maker(
    work_dir: Path,
    input_file: str = "combined.csv",
    output_file: str = "combined.geojson",
) -> None:
    """Convert combined CSV output into GeoJSON."""
    print(f"\nStep 3/3: Creating GeoJSON from {input_file}...")

    df = pd.read_csv(work_dir / input_file)
    if df.empty:
        with open(work_dir / output_file, "w") as handle:
            json.dump({"type": "FeatureCollection", "features": []}, handle)
        print(f"  ✓ {output_file} created (empty)")
        return

    coordinate_columns = {f"x{i}" for i in range(1, MAX_BOUNDARY_VERTICES + 1)} | {
        f"y{i}" for i in range(1, MAX_BOUNDARY_VERTICES + 1)
    }
    gene_feature_columns = [
        col for col in df.columns
        if col not in {"Barcode", "Cluster", "Total"} and col not in coordinate_columns
    ]
    has_total = "Total" in df.columns

    geojson = {
        "type": "FeatureCollection",
        "features": [],
    }

    row_count = df.shape[0]
    for index, row in df.iterrows():
        if index % 1000 == 0:
            print(f"  {(index / row_count) * 100:.1f}% processed")

        coordinates = [
            [row[f"x{i + 1}"], row[f"y{i + 1}"]]
            for i in range(MAX_BOUNDARY_VERTICES)
        ]
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])

        cell = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinates],
            },
            "properties": {
                "CellID": row["Barcode"],
                "Z": row["Cluster"],
                "GeneFeatures": [row[col] for col in gene_feature_columns],
                "TotalFeatures": row["Total"] if has_total else None,
            },
        }
        geojson["features"].append(cell)

    with open(work_dir / output_file, "w") as handle:
        json.dump(geojson, handle)

    print(f"  ✓ {output_file} created")


def run_filter(work_dir: Path, filter_file: str | Path) -> str:
    """Filter the combined CSV to a selected list of cells."""
    print(f"\nFiltering cells using {filter_file}...")

    big = pd.read_csv(work_dir / "combined.csv")
    selected_barcodes = read_filter_barcodes(filter_file)

    mask = big["Barcode"].isin(selected_barcodes)
    filtered = big.loc[mask]

    output_name = "filtered_cells.csv"
    filtered.to_csv(work_dir / output_name, index=False)
    print(f"  ✓ Filtered {len(filtered)} cells to {output_name}")

    return output_name


def main():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass

    parser = argparse.ArgumentParser(
        description="Process Xenium spatial transcriptomics data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - process entire dataset
  python xenium_processor.py /path/to/xenium/folder

  # With filtering
  python xenium_processor.py /path/to/xenium/folder --filter cell_list.csv

  # Custom output directory
  python xenium_processor.py /path/to/xenium/folder --output /custom/output
        """,
    )

    parser.add_argument("xenium_folder", help="Path to Xenium output folder")
    parser.add_argument("--filter", help="Optional: CSV file with cell IDs to process")
    parser.add_argument("--output", help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument(
        "--allow-large-run",
        action="store_true",
        help="Override the dense export size guard for very large datasets",
    )

    args = parser.parse_args()
    output_dir = args.output if args.output else DEFAULT_OUTPUT_DIR

    print("Xenium Processor")
    print("================")
    print(f"Input: {args.xenium_folder}")
    print(f"Output: {output_dir}")
    if args.filter:
        print(f"Filter: {args.filter}")
        print("Note: with --filter, combined.* describes the selected subset for this run.")

    selected_barcodes = read_filter_barcodes(args.filter) if args.filter else None

    xenium_files = find_xenium_files(args.xenium_folder)
    work_dir = prepare_working_directory(xenium_files, output_dir, selected_barcodes=selected_barcodes)

    run_zarr_reader(
        work_dir,
        xenium_files,
        selected_barcodes=selected_barcodes,
        allow_large_run=args.allow_large_run,
    )
    run_combiner(work_dir)
    run_geojson_maker(work_dir)

    if args.filter:
        filtered_csv = run_filter(work_dir, args.filter)
        run_geojson_maker(work_dir, filtered_csv, "filtered_cells.geojson")

    print("\n✅ Processing complete!")
    print(f"Output files in: {output_dir}")
    print("  - combined.csv")
    print("  - combined.geojson")
    if args.filter:
        print("  - filtered_cells.csv")
        print("  - filtered_cells.geojson")
        print("  - filtered_* files are retained for backward compatibility with older workflows")


if __name__ == "__main__":
    main()
