#!/usr/bin/env python3
"""Generate a minimal Xenium-like dataset for local debugging."""

from __future__ import annotations

import csv
import gzip
import shutil
from pathlib import Path

import numpy as np
import zarr
from zarr.storage import ZipStore


ROOT = Path(__file__).resolve().parents[1]
DEBUG_DIR = ROOT / "debug_data"
SAMPLE_DIR = DEBUG_DIR / "sample_xenium"
SELECTED_CELLS = DEBUG_DIR / "selected_cells.csv"

CELL_IDS = ["cell-001", "cell-002", "cell-003"]
GENES = [
    ("ENSG000001", "GeneA"),
    ("ENSG000002", "GeneB"),
]
CLUSTERS = [
    ("cell-001", "Cluster-1"),
    ("cell-002", "Cluster-2"),
    ("cell-003", "Cluster-1"),
]

# Rows represent features, columns represent cells.
# The last row is the synthetic "Total" feature expected by xenium_processor.py.
COUNTS = np.array(
    [
        [2, 0, 1],
        [1, 3, 0],
        [3, 3, 1],
    ],
    dtype=np.int32,
)

BOUNDARIES = {
    "cell-001": [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)],
    "cell-002": [(10.0, 0.0), (14.0, 0.0), (14.0, 4.0), (10.0, 4.0)],
    "cell-003": [(0.0, 10.0), (4.0, 10.0), (4.0, 14.0), (0.0, 14.0)],
}


def build_csr_rows(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    data: list[int] = []
    indices: list[int] = []
    indptr = [0]

    for row in matrix:
        nonzero = np.nonzero(row)[0]
        data.extend(row[nonzero].tolist())
        indices.extend(nonzero.tolist())
        indptr.append(len(data))

    return (
        np.asarray(data, dtype=np.int32),
        np.asarray(indices, dtype=np.int32),
        np.asarray(indptr, dtype=np.int32),
    )


def write_boundaries(path: Path) -> None:
    rows: list[dict[str, float | str]] = []
    for cell_id, coords in BOUNDARIES.items():
        for vertex_x, vertex_y in coords:
            rows.append(
                {
                    "cell_id": cell_id,
                    "vertex_x": vertex_x,
                    "vertex_y": vertex_y,
                }
            )

    with gzip.open(path, "wt", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["cell_id", "vertex_x", "vertex_y"])
        writer.writeheader()
        writer.writerows(rows)


def write_clusters(path: Path) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Barcode", "Cluster"])
        writer.writerows(CLUSTERS)


def write_features(path: Path) -> None:
    with gzip.open(path, "wt", newline="") as handle:
        for feature_id, gene_name in GENES:
            handle.write(f"{feature_id}\t{gene_name}\n")


def write_selected_cells(path: Path) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Barcode"])
        writer.writerow(["cell-001"])
        writer.writerow(["cell-003"])


def write_zarr(path: Path) -> None:
    data, indices, indptr = build_csr_rows(COUNTS)

    with ZipStore(path, mode="w") as store:
        root = zarr.group(store=store)
        cell_features = root.create_group("cell_features")
        cell_features.create_dataset("data", data=data, shape=data.shape, dtype=data.dtype)
        cell_features.create_dataset(
            "indices",
            data=indices,
            shape=indices.shape,
            dtype=indices.dtype,
        )
        cell_features.create_dataset(
            "indptr",
            data=indptr,
            shape=indptr.shape,
            dtype=indptr.dtype,
        )
        cell_features.create_dataset(
            "cell_id",
            data=np.asarray(CELL_IDS, dtype="S16"),
            shape=(len(CELL_IDS),),
            dtype="S16",
        )


def main() -> None:
    if SAMPLE_DIR.exists():
        shutil.rmtree(SAMPLE_DIR)

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    (SAMPLE_DIR / "analysis" / "clustering" / "gene_expression_graphclust").mkdir(
        parents=True,
        exist_ok=True,
    )
    (SAMPLE_DIR / "cell_feature_matrix").mkdir(parents=True, exist_ok=True)

    (SAMPLE_DIR / "experiment.xenium").write_text("synthetic debug dataset\n")
    write_boundaries(SAMPLE_DIR / "analysis" / "cell_boundaries.csv.gz")
    write_clusters(
        SAMPLE_DIR / "analysis" / "clustering" / "gene_expression_graphclust" / "clusters.csv"
    )
    write_features(SAMPLE_DIR / "cell_feature_matrix" / "features.tsv.gz")
    write_zarr(SAMPLE_DIR / "cell_feature_matrix.zarr.zip")

    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    write_selected_cells(SELECTED_CELLS)

    print(f"Debug dataset written to: {SAMPLE_DIR}")
    print(f"Filter CSV written to: {SELECTED_CELLS}")


if __name__ == "__main__":
    main()
