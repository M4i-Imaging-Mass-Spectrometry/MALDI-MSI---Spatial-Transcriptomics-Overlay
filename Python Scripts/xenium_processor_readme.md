# Xenium Processor

A command-line tool for converting Xenium spatial transcriptomics data to a .GeoJSON file used in EscDat (MALDI-MSI and spatial transcriptomics overlay software). Generated file used in step 4 of EscDat. 

This tool combines multiple processing steps into a single, easy-to-use script that automatically handles file discovery, data combination, and GeoJSON generation. The resulting .GeoJSON file contains the spatial single-cell information that includes: Cell_ID, Cluster, Gene counts per gene and Spatial coordinates.

## Quick Start Guide

### Step 1: Download the Script
1. Download `xenium_processor.py` from: https://github.com/M4i-Imaging-Mass-Spectrometry/MALDI-MSI---Spatial-Transcriptomics-Overlay
2. Copy and paste `xenium_processor.py` to your xenium output folder. This is the folder that is often called `output-XET####` and contains the `experiment.xenium` file from your measurement.

### Step 2: Open Terminal
3. Open a terminal in the xenium output folder (right-click in an empty space, click "Open in terminal")

### Step 3: Run the Script

**For processing ALL cells:**
```bash
python xenium_processor.py "path/to/xenium/output"
```

**IMPORTANT NOTES:**
- Replace `"path/to/xenium/output"` with your actual folder path
- You can get your path by copying it from the top of your Windows Explorer window or right-clicking the folder and selecting "Copy as Path"
- Change backward slashes (\) to forward slashes (/)
- Your path MUST be in quotation marks ""

**Example:**
```bash
python xenium_processor.py "C:/Users/YourName/Documents/output-XET1234"
```

### Step 4: Results
The script will automatically:
- Create a new folder called `xenium_output`
- Collect files from your output folder and place them there
- Create a `.GeoJSON` file named `combined.geojson` which contains: Cell_ID, Cluster, Gene counts per gene and Spatial coordinates from each individual cell
- This `.GeoJSON` file is used in the software called ESCDAT which allows for the overlay of timsTOF-MSI and Xenium Spatial Transcriptomics data

## Working with Selected Cells Only

If you want to work with a selection of cells instead of all cells measured in your Xenium analysis:

### Step 1: Select Cells in Xenium Explorer
1. In Xenium Explorer, select your cells using an ROI, cluster, or individual cells
2. In Xenium Explorer, click "Cells" in the selection window
3. Press the three vertical dots (...) in the same line as "Cell Stats"
4. Click "Download Cell Stats as .csv"

### Step 2: Prepare the CSV File
5. Rename your .csv file to something like `selected_cells.csv`
6. Copy it to your xenium output folder
7. Delete the first two rows in the .csv file

### Step 3: Run with Filter
8. Open a new terminal in your xenium output folder
9. Run the following command:
```bash
python xenium_processor.py "path/to/xenium/output" --filter "path/to/xenium/output/selected_cells.csv"
```

**IMPORTANT:** Keep the quotation marks and use the correct name of your .csv file!

### Step 4: Results
The script will create:
- A new folder called `xenium_output`
- Collect files from your output folder and place them there
- Create a `.GeoJSON` file named `filtered.geojson` which contains: Cell_ID, Cluster, Gene counts per gene and Spatial coordinates from each selected cell
- This `.GeoJSON` file is used in ESCDAT for overlay analysis

## Requirements

### System Requirements
- Python 3.7 or higher

### Required Python Packages
- numpy
- pandas
- zarr

### Installation of Required Packages
```bash
py -m pip install numpy pandas zarr
```

## Installation

No installation needed! Just download the `xenium_processor.py` script and place it in your working directory.

```bash
# Download from:
wget https://github.com/M4i-Imaging-Mass-Spectrometry/MALDI-MSI---Spatial-Transcriptomics-Overlay

# Or copy the file to your xenium output folder if you already have it downloaded
```

## Advanced Usage

### Basic Processing
```bash
python xenium_processor.py "/path/to/xenium/output/folder"
```

### With Cell Filtering
```bash
python xenium_processor.py "/path/to/xenium/folder" --filter "selected_cells.csv"
```

### Custom Output Directory
```bash
python xenium_processor.py "/path/to/xenium/folder" --output "./my_analysis"
```

## Input Files

The script automatically searches for these required files anywhere in your Xenium output folder:

| File | Description | Common Locations |
|------|-------------|------------------|
| `cell_feature_matrix.zarr.zip` | Compressed gene expression matrix | Root folder |
| `cell_boundaries.csv` or `.csv.gz` | Cell polygon coordinates | `/analysis/` folder |
| `clusters.csv` | Cell cluster assignments | `/analysis/clustering/gene_expression_graphclust/` |
| `features.tsv.gz` | Gene feature list | `/cell_feature_matrix/` |

**Note:** The script searches recursively, so files can be anywhere in the directory tree.

## Output Files

All outputs are saved to `./xenium_output/` (or your specified output directory):

| File | Description |
|------|-------------|
| `combined.csv` | Master dataset with all cell data |
| `combined.geojson` | Spatial visualization file for full dataset |
| `filtered_cells.csv` | Subset of cells (if --filter used) |
| `filtered_cells.geojson` | Spatial visualization for filtered cells |

### Combined.csv Structure
- **Barcode:** Unique cell identifier
- **Cluster:** Cluster assignment
- **Gene columns:** Expression count for each gene
- **Total:** Sum of all transcripts
- **x1-x25, y1-y25:** Cell boundary coordinates (up to 25 vertices)

## Cell Filtering

To analyze specific cell populations:

1. Create a CSV file with cell IDs in one of these formats:
   - Column named `cell_id`
   - Column named `Barcode`
   - First column (if no headers match)

2. Run with the `--filter` flag:
   ```bash
   python xenium_processor.py "/xenium/data" --filter "selected_cells.csv"
   ```

Example filter file:
```csv
Barcode
aaaiflmn-1
aaanapee-1
aaapcdjl-1
aabmdjhc-1
aacgbgnk-1
aacgoeoa-1
aacnhgpe-1
```

## How the Script Works

### Step 1: File Discovery
- Recursively searches the input folder
- Identifies all required files automatically
- Handles both compressed (.gz) and uncompressed files

### Step 2: Zarr Processing
- Reads sparse expression matrix
- Converts to dense format
- Outputs: `gene_features.csv`

### Step 3: Data Combination
- Merges expression data with spatial coordinates
- Adds cluster assignments
- Removes unassigned cells
- Pads coordinate arrays to uniform size (25 vertices)
- Outputs: `combined.csv`

### Step 4: GeoJSON Creation
- Converts tabular data to GeoJSON format
- Creates polygon features for each cell
- Includes all expression data as properties
- Outputs: `combined.geojson`

## Troubleshooting

### "Missing required files" error
- Ensure all 4 required files are present in the Xenium output folder
- Check that file names match exactly (case-sensitive on Linux/Mac)
- Verify `.gz` files are not corrupted

### Multiple files found warning
- The script will automatically choose the most likely file
- For `clusters.csv`, it prefers files in `gene_expression_graphclust` folders

### Path issues
- Make sure your path is in quotation marks
- Use forward slashes (/) instead of backward slashes (\)
- Verify the path actually exists and contains the required files

## Example Workflow

```bash
# 1. Basic processing
python xenium_processor.py "/path/to/xenium/folder"

# 2. Check the outputs
ls xenium_output/
# combined.csv  combined.geojson  gene_features.csv

# 3. Filter for specific cells
python xenium_processor.py "/path/to/xenium/folder" --filter "selected_cells.csv"

# 4. Load in GeoJSON viewer
# Open combined.geojson in QGIS, geojson.io, text editor, or custom viewer
```

## Limitations

- Maximum 25 vertices per cell polygon (additional vertices are truncated)
- Requires all 4 input files to be present
- Memory usage scales with dataset size

## Citation

If you use this tool in your research, please cite the paper:
One Section, Two Worlds: Single-Cell Integration of MALDI-MSI and Spatial Transcriptomics on the Same Tissue Section

DOI: (to be updated)

## Support

For issues or questions:
1. Check that all input files are present
2. Verify Python package versions
3. Review error messages for specific missing files
4. Ensure sufficient disk space for outputs

## Additional Notes

- The script is designed to be user-friendly for non-technical users
- All file searches are done automatically - you don't need to specify individual file locations
- The output GeoJSON files can be opened in various GIS software or text editors
- For large datasets, processing may take several minutes