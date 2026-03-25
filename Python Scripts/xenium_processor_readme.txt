Xenium Processor
================

xenium_processor.py converts a 10x Xenium output directory into EscDat-compatible
CSV and GeoJSON overlays.

Recommended usage
-----------------

Full run:
  python "Python Scripts/xenium_processor.py" "/path/to/xenium/output"

Selected cells only:
  python "Python Scripts/xenium_processor.py" "/path/to/xenium/output" --filter "/path/to/selected_cells.csv"

Custom output directory:
  python "Python Scripts/xenium_processor.py" "/path/to/xenium/output" --output "./xenium_output_custom"

Very large full export:
  python "Python Scripts/xenium_processor.py" "/path/to/xenium/output" --allow-large-run

Supported inputs
----------------

The script recursively searches for:
  - cell_feature_matrix.zarr.zip
  - cell_boundaries.csv / cell_boundaries.csv.gz / cell_boundaries.parquet
  - clusters.csv
  - features.tsv.gz

It also supports newer Xenium layouts by falling back to:
  - cell_features/.zattrs for feature metadata
  - polygon_sets/ in the root zarr tree for boundary recovery

Main outputs
------------

Default output directory:
  ./xenium_output/

Primary files:
  - combined.csv
  - combined.geojson

Support files:
  - gene_features.csv
  - cell_ids.csv
  - feature_list.csv
  - feature_metadata.csv
  - cell_boundaries.csv
  - clusters.csv

If --filter is used, the script also writes:
  - filtered_cells.csv
  - filtered_cells.geojson

Validation
----------

You can run a lightweight validation step with:

  python tools/validate_combined_output.py "./xenium_output" --clusters "/path/to/analysis/clustering/gene_expression_graphclust/clusters.csv"

Notes for publication
---------------------

For manuscript preparation, record:
  - repository commit hash
  - exact preprocessing command
  - Xenium output/software version
  - whether --filter or --allow-large-run was used
  - feature_metadata.csv and final overlay files

For a fuller guide, see:
  - ../README.md
  - ../REPRODUCIBILITY.md
