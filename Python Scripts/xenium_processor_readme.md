# Xenium Processor

`xenium_processor.py` converts a 10x Xenium output directory into EscDat-compatible CSV and GeoJSON overlays.

It merges:

- cell barcodes
- cluster assignments
- biological gene counts
- total transcript counts
- polygon boundary coordinates

## Recommended Usage

Run from the repository root:

```bash
python "Python Scripts/xenium_processor.py" "/path/to/xenium/output"
```

### Process only a selected cell set

```bash
python "Python Scripts/xenium_processor.py" \
  "/path/to/xenium/output" \
  --filter "/path/to/selected_cells.csv"
```

### Override the output directory

```bash
python "Python Scripts/xenium_processor.py" \
  "/path/to/xenium/output" \
  --output "./xenium_output_custom"
```

### Force a very large full export

```bash
python "Python Scripts/xenium_processor.py" \
  "/path/to/xenium/output" \
  --allow-large-run
```

Use `--allow-large-run` only when you intentionally want a full dense export and have enough RAM.

## Input Discovery

The script recursively searches the Xenium output folder and supports:

- `cell_feature_matrix.zarr.zip`
- `cell_boundaries.csv`, `cell_boundaries.csv.gz`, or `cell_boundaries.parquet`
- `clusters.csv`
- `features.tsv.gz`

It also supports newer Xenium layouts by falling back to:

- `cell_features/.zattrs` for feature metadata
- root `polygon_sets/` zarr data for boundary recovery

## Output Files

The script writes the following files into `./xenium_output/` by default:

- `combined.csv`
- `combined.geojson`
- `gene_features.csv`
- `cell_ids.csv`
- `feature_list.csv`
- `feature_metadata.csv`
- `cell_boundaries.csv`
- `clusters.csv`

If `--filter` is supplied, it also writes:

- `filtered_cells.csv`
- `filtered_cells.geojson`

## Filter Files

The filter CSV may contain one of the following:

- a `Barcode` column
- a `cell_id` column
- any first column containing Xenium barcodes

Example:

```csv
Barcode
aaaiflmn-1
aaanapee-1
aaapcdjl-1
```

## Validation

After a run, validate the output directory with:

```bash
python tools/validate_combined_output.py \
  "./xenium_output" \
  --clusters "/path/to/analysis/clustering/gene_expression_graphclust/clusters.csv"
```

## Notes for Manuscripts and Shared Pipelines

- record the repository commit used for preprocessing
- save the exact command line used
- archive `feature_metadata.csv` alongside final outputs
- document whether `--filter` or `--allow-large-run` was used
- report the Xenium output format or software version when possible

For a broader project-level overview, see the repository [README](../README.md).
