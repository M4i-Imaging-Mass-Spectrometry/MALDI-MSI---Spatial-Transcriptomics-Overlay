# Reproducibility Checklist

This file collects the minimum information we recommend saving alongside any published or shared Xenium overlay generated with this repository.

## Record These Items

- repository URL and commit hash
- operating system and Python version
- package environment or `requirements.txt`
- exact command used to run `xenium_processor.py`
- whether `--filter` was used
- whether `--allow-large-run` was used
- Xenium output/software version, if known
- the original clustering source used
- the final output directory contents

## Archive These Files

- `combined.csv`
- `combined.geojson`
- `feature_metadata.csv`
- `feature_list.csv`
- filter CSV, if one was used
- a validation log from `tools/validate_combined_output.py`

## Suggested Validation Step

After each production run, execute:

```bash
python tools/validate_combined_output.py \
  "./xenium_output" \
  --clusters "/path/to/analysis/clustering/gene_expression_graphclust/clusters.csv"
```

This validator checks sampled rows for:

- internal transcript-count consistency
- cluster-label agreement
- coordinate agreement between `combined.csv` and `cell_boundaries.csv`

## Reporting Notes

When describing preprocessing in a manuscript or supplement, it is useful to state:

- that Xenium sparse feature data were converted to a dense per-cell table
- that non-biological control/codeword features were excluded from exported gene columns
- that cluster labels were drawn from `gene_expression_graphclust/clusters.csv` when multiple clustering outputs existed
- that polygon coordinates were exported with a maximum of 25 vertices per cell in the tabular output

## Caveats to Report Clearly

- very large datasets may require filtering or high-memory machines
- filtered runs currently make `combined.*` describe the selected subset used in that run
- `filtered_*` files are retained for compatibility with older workflows
