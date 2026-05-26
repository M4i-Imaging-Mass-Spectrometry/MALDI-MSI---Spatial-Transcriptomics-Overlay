# VS Code Debugging

## Quick start

From the repository root:

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows
# or: source .venv/bin/activate  # macOS / Linux
python -m pip install -r requirements.txt
python tools/create_debug_dataset.py
python "Python Scripts/xenium_processor.py" debug_data/sample_xenium --output debug_data/xenium_output
```

To debug inside VS Code, open the repository, select the `.venv` interpreter, and either run the commands above in the integrated terminal or create your own `.vscode/launch.json` profile pointing at `Python Scripts/xenium_processor.py` with arguments such as `debug_data/sample_xenium --output debug_data/xenium_output`.

## Real data

To debug with an actual Xenium export, point the script at your own dataset and output directory, optionally adding `--filter <selected_cells.csv>`.

## Large real datasets

For large Xenium runs, the script may stop with a protective memory error before creating the dense matrix. In that case:

- prefer debugging with a filter CSV that contains a small cell subset
- duplicate a launch profile and add `--allow-large-run` only if you intentionally want to stress-test a full export

For manuscript or reproducibility work, keep a copy of the exact launch arguments you used.

