# VS Code Debugging

## Quick start

1. Open the repository root in VS Code.
2. Run the `Prepare debug environment` task once.
3. Press `F5` and choose one of these launch profiles:
   - `xenium_processor: sample dataset`
   - `xenium_processor: sample dataset with filter`

## What the setup does

- Creates a local `.venv` using Python 3.13
- Installs the project dependencies from `requirements.txt`
- Generates a small synthetic Xenium-style dataset under `debug_data/`
- Launches `Python Scripts/xenium_processor.py` against that dataset

## Real data

To debug with an actual Xenium export, duplicate one of the launch profiles in `.vscode/launch.json` and replace:

- `${workspaceFolder}/debug_data/sample_xenium`
- `${workspaceFolder}/debug_data/selected_cells.csv`
- `${workspaceFolder}/debug_data/xenium_output`

with your own dataset and output paths.

## Large real datasets

For large Xenium runs, the script may stop with a protective memory error before creating the dense matrix. In that case:

- prefer debugging with a filter CSV that contains a small cell subset
- duplicate a launch profile and add `--allow-large-run` only if you intentionally want to stress-test a full export

For manuscript or reproducibility work, keep a copy of the exact launch arguments you used.

