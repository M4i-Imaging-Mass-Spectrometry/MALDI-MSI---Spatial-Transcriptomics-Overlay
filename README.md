# MALDI-MSI and Spatial Transcriptomics Overlay

Tools and reference material for generating EscDat-compatible overlays between MALDI-MSI and 10x Xenium spatial transcriptomics data.

This repository currently centers on [`xenium_processor.py`](./Python%20Scripts/xenium_processor.py), a reproducible preprocessing script that converts Xenium outputs into:

- `combined.csv`
- `combined.geojson`
- optional filtered-cell outputs for selected ROIs or cell populations

## Overview

The processor was written to make a Xenium run easier to reuse in downstream overlay software and manuscript-ready analysis workflows. It:

- discovers required Xenium files automatically
- supports both legacy and newer Xenium output layouts
- merges cell-level expression, cluster labels, and polygon boundaries
- exports tabular and GeoJSON outputs for visualization and downstream integration
- includes lightweight validation tooling for reproducibility checks

## Repository Layout

- [`Python Scripts/xenium_processor.py`](./Python%20Scripts/xenium_processor.py): main processing script
- [`Python Scripts/xenium_processor_readme.md`](./Python%20Scripts/xenium_processor_readme.md): script-specific usage guide
- [`tools/create_debug_dataset.py`](./tools/create_debug_dataset.py): synthetic debug dataset generator
- [`tools/validate_combined_output.py`](./tools/validate_combined_output.py): lightweight output validator
- [`VSCODE_DEBUG.md`](./VSCODE_DEBUG.md): VS Code debugging workflow
- [`REPRODUCIBILITY.md`](./REPRODUCIBILITY.md): recommended reporting and validation checklist

## Xenium Compatibility

The processor supports two Xenium layouts that appear in practice:

1. Legacy-style outputs with `features.tsv.gz` and `cell_feature_matrix.zarr.zip`
2. Newer outputs where feature metadata comes from `cell_features/.zattrs`

It also includes a boundary fallback for cases where:

- `cell_boundaries.csv.gz` exists but is a macOS/iCloud placeholder
- only the root zarr `polygon_sets/` representation is locally available

Cluster labels are resolved from `clusters.csv`, preferring `gene_expression_graphclust` when multiple clustering outputs are present.

## Installation

### Minimal environment

```bash
python -m pip install -r requirements.txt
```

### Optional dependency

If you need to read `.parquet` boundary files directly, also install:

```bash
python -m pip install pyarrow
```

## Quick Start

### Process a full Xenium run

```bash
python "Python Scripts/xenium_processor.py" "/path/to/xenium/output"
```

### Process a selected subset of cells

```bash
python "Python Scripts/xenium_processor.py" \
  "/path/to/xenium/output" \
  --filter "/path/to/selected_cells.csv"
```

### Custom output directory

```bash
python "Python Scripts/xenium_processor.py" \
  "/path/to/xenium/output" \
  --output "./xenium_output_custom"
```

## Large Datasets

The script converts sparse Xenium matrices into a dense intermediate table. For very large runs, that can require several gigabytes of RAM.

To avoid accidental workstation lockups, the script stops early with a clear `MemoryError` when the estimated dense matrix is too large. In that case:

- use `--filter` to process a selected subset of cells
- or rerun with `--allow-large-run` if you intentionally want the full dense export and have enough memory

## Output Files

By default, results are written into `./xenium_output/`.

### Primary outputs

- `combined.csv`: merged cell table with barcode, cluster, gene counts, total counts, and polygon coordinates
- `combined.geojson`: EscDat-compatible GeoJSON export

### Support files

- `cell_ids.csv`: barcode order used in the dense matrix
- `gene_features.csv`: dense feature matrix exported from the Xenium sparse matrix
- `feature_list.csv`: ordered feature names
- `feature_metadata.csv`: feature names plus source row indices
- `cell_boundaries.csv`: working boundary table used for the merge
- `clusters.csv`: copied clustering assignments

### Filtered outputs

If `--filter` is used, the script also writes:

- `filtered_cells.csv`
- `filtered_cells.geojson`

Note:
With `--filter`, the current implementation processes only the selected subset to control memory usage on large runs. As a result, `combined.*` in that run also describes the selected subset. The `filtered_*` files are retained for backward compatibility with earlier workflows.

## combined.csv Schema

- `Barcode`: Xenium cell barcode
- `Cluster`: cluster label from `clusters.csv`
- gene columns: one column per retained biological feature
- `Total`: total transcript count for the cell
- `x1-y25`: up to 25 boundary vertices per cell

The processor keeps biological gene features and the aggregate total feature while excluding non-biological control/codeword channels from the exported matrix.

## Validation

After generating outputs, you can run a lightweight consistency check:

```bash
python tools/validate_combined_output.py \
  "./xenium_output" \
  --clusters "/path/to/analysis/clustering/gene_expression_graphclust/clusters.csv"
```

The validator checks sampled rows for:

- `Total == sum(gene columns)`
- cluster labels match the source `clusters.csv`
- coordinate columns match the generated `cell_boundaries.csv`

## VS Code Workflow

If you want a ready-to-debug local project setup, see:

- [`VSCODE_DEBUG.md`](./VSCODE_DEBUG.md)

## Reproducibility Notes

For manuscript preparation, we recommend archiving:

- the exact command used
- the Xenium software/output version
- the filter file used, if any
- the generated `feature_metadata.csv`
- the generated `combined.csv` or `combined.geojson`
- a validation log from `tools/validate_combined_output.py`

See [`REPRODUCIBILITY.md`](./REPRODUCIBILITY.md) for a fuller checklist.

## Limitations

- dense matrix generation scales with `features x cells`
- cell polygons are capped at 25 vertices in the exported table
- filtered runs currently write both `combined.*` and `filtered_*` for compatibility
- direct `.parquet` fallback requires an optional parquet engine such as `pyarrow`

## Citation

If this repository or processor script is used in a publication, please replace this section with the final manuscript citation, DOI, and version or commit hash used for preprocessing.
