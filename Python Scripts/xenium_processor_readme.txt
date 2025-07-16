# Xenium Processor

A command-line tool for converting Xenium spatial transcriptomics data to a .GeoJSON file used in EscDat (MALDI-MSI and spatial transcriptomics overlay software). Generated file used in step 4 of EscDat. 
This tool combines multiple processing steps into a single, easy-to-use script that automatically handles file discovery, data combination, and GeoJSON generation.
The resulting .GeoJSON file contains the spatial single-cell information that contains: Cell_ID, Cluster, Gene counts per gene and Spatial coordinates. 


DETAILED STEPS ON HOW TO RUN xenium_processor.py:

START
1. Download xenium_processor.py (https://https://github.com/M4i-Imaging-Mass-Spectrometry/MALDI-MSI---Spatial-Transcriptomics-Overlay).
2. Copy and paste xenium_processor.py to your xenium output folder. This is the folder that is often called (output-XET####) and contains the experiment.xenium file from your measurement.
3. Open a terminal in the xenium output folder (right-click in an empty space, click "Open in terminal").

# The following is required to extract your full Xenium run

4. If you want to run xenium_processor.py, you need to write the following command line in the terminal: python xenium_processor.py "path/to/xenium/output"  
KEEP IN MIND! That the "path/to/xenium/output" is not literally this text. Change it to the folder path where your 'experiment.xenium' is stored. You can do this by copying your path on the top of your windows explorer or right clicking on the folder and selecting 'Copy as Path'. Change backward slashes (\) to forward slashes (/). 
IMPORTANT! your path needs to be in between quotation marks "". 
5. Now press the "Enter"-key.
6. The script automates a few steps and results in the following.
	- Creates a new folder called: xenium_output
	- Collects files from your output folder and places them in there
	- Creates a .GeoJSON file named: combined.geojson which contains: Cell_ID, Cluster, Gene counts per gene and Spatial coordinates from each individual cell.
	- This .GeoJSON file is used in the software called ESCDAT which allows for the overlay of timsTOF-MSI and Xenium Spatial Transcriptomics data.
STOP

# The following is required if you want to work with a selection of the cells, instead of all cells that are measured in your Xenium analysis.

7. In Xenium Explorer, select your cells, albeit using an ROI or cluster or a single cell.
8. In Xenium explorer, click 'Cells' in the selection window. Press the three vertical dots (...) in the same line as 'Cell Stats'.
9. Click 'Download Cell Stats as .csv'
10. Rename your .csv to e.g, selected_cells.csv and copy it to your xenium output folder.
11. Open a new terminal in your xenium output folder.
12. In your terminal window, you now need to run the following command line: python xenium_processor.py "path/to/xenium/output" --filter "path/to/xenium/output/selected_cells.csv"
IMPORTANT! Keep the quotation marks in mind and also the name of your .csv file!
13. The script automates a few steps and results in the following.
	- Creates a new folder called: xenium_output
	- Collects files from your output folder and places them in there
	- Creates a .GeoJSON file named: filtered.geojson which contains: Cell_ID, Cluster, Gene counts per gene and Spatial coordinates from each individual cell that you selected.
	- This .GeoJSON file is used in the software called ESCDAT which allows for the overlay of timsTOF-MSI and Xenium Spatial Transcriptomics data.
STOP

## Requirements to run xenium_processor.py

- Python 3.7+

- Required packages:

numpy
pandas
zarr

To install:
  ```bash
  py -m pip install numpy pandas zarr
  ```

## Installation of xenium_processor.py

Download the `xenium_processor.py` script to your local machine. No installation needed!

```bash
# Download the script from:
wget https://https://github.com/M4i-Imaging-Mass-Spectrometry/MALDI-MSI---Spatial-Transcriptomics-Overlay

# Or just copy the file to your working directory (xenium/output/folder) if you already have it downloaded.
```

## Basic Usage
Open terminal in your Xenium output folder and run:

### Process entire Xenium dataset
```bash
python xenium_processor.py "/path/to/xenium/output/folder"
```

### With cell filtering
```bash
python xenium_processor.py "/path/to/xenium/folder" --filter "selected_cells.csv"
```

"selected_cells.csv" is the file you generate when you select a ROI in Xenium Explorer.

### Custom output directory
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

**Note**: The script searches recursively, so files can be anywhere in the directory tree.

## Output Files

All outputs are saved to `./xenium_output/` (or your specified output directory):

| File | Description |
|------|-------------|
| `combined.csv` | Master dataset with all cell data |
| `combined.geojson` | Spatial visualization file for full dataset |
| `filtered_cells.csv` | Subset of cells (if --filter used) |
| `filtered_cells.geojson` | Spatial visualization for filtered cells |

### Combined.csv Structure
- **Barcode**: Unique cell identifier
- **Cluster**: Cluster assignment
- **Gene columns**: Expression count for each gene
- **Total**: Sum of all transcripts
- **x1-x25, y1-y25**: Cell boundary coordinates (up to 25 vertices)

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

## Script Workflow Details

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
- Verify `.gz` files aren't corrupted

### Multiple files found warning
- The script will automatically choose the most likely file
- For `clusters.csv`, it prefers files in `gene_expression_graphclust` folders


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

DOI: ###

## Support

For issues or questions:
1. Check that all input files are present
2. Verify Python package versions
3. Review error messages for specific missing files
4. Ensure sufficient disk space for outputs

---

DETAILED STEPS ON HOW TO RUN xenium_processor.py:

1. Download xenium_processor.py (https://https://github.com/M4i-Imaging-Mass-Spectrometry/MALDI-MSI---Spatial-Transcriptomics-Overlay).
2. Copy and paste xenium_processor.py to your xenium output folder. This is the folder that is often called (output-XET####) and contains the experiment.xenium file from your measurement.
3. Open a terminal in the xenium output folder (right-click in an empty space, click "Open in terminal".
4. If you want to run xenium_processor.py you need to write the following command line in the terminal: python xenium_processor.py "path/to/xenium/output"  
KEEP IN MIND! That the "path/to/xenium/output" is not literally this text. Change it to the path where your xenium.experiment is stored. You can do this by copying your path on the top of your windows explorer. 
IMPORTANT! your path needs to be in between quotation marks "". 
5. Now press the "Enter"-key.
6. The script automates a few steps and results in the following.
	- Creates a new folder called: xenium_output
	- Collects files from your output folder and places them in there
	- Creates a .GeoJSON file named: combined.geojson which contains: Cell_ID, Cluster, Gene counts per gene and Spatial coordinates from each individual cell.
7. This file is used in the software called ESCDAT which allows for the overlay of timsTOF-MSI and Xenium Spatial Transcriptomics data.

!	The following is required if you want to work with a selection of the cells, instead of all cells that are measured in your Xenium analysis.

8. In Xenium Explorer, select your cells, albeit using an ROI or cluster or a single cell.
9. In Xenium explorer, click "Cells" in the selection window. Press the three vertical dots (...) in the same line as "Cell Stats".
10. Click "Download Cell Stats as .csv
11. Rename your .csv to e.g, selected_cells.csv and copy it to your xenium output folder.
12. Open a new terminal in your xenium output folder.
13. In your terminal window, you now need to run the following command line: python xenium_processor.py "path/to/xenium/output" --filter "path/to/xenium/output/selected_cells.csv"
IMPORTANT! Keep the quotation marks in mind and also the name of your .csv file!
14. The script automates a few steps and results in the following.
	- Creates a new folder called: xenium_output
	- Collects files from your output folder and places them in there
	- Creates a .GeoJSON file named: filtered.geojson which contains: Cell_ID, Cluster, Gene counts per gene and Spatial coordinates from each individual cell that you selected.
15. This file is used in the software called ESCDAT which allows for the overlay of timsTOF-MSI and Xenium Spatial Transcriptomics data.




