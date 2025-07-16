**# Xenium Processor**



A command-line tool for converting Xenium spatial transcriptomics data to a .GeoJSON file used in EscDat (MALDI-MSI and spatial transcriptomics overlay software). Generated file used in step 4 of EscDat. 

This tool combines multiple processing steps into a single, easy-to-use script that automatically handles file discovery, data combination, and GeoJSON generation.

The resulting .GeoJSON file contains the spatial single-cell information that contains: Cell\_ID, Cluster, Gene counts per gene and Spatial coordinates. 





**DETAILED STEPS ON HOW TO RUN xenium\_processor.py:**



**START**

1\. Download xenium\_processor.py (https://https://github.com/M4i-Imaging-Mass-Spectrometry/MALDI-MSI---Spatial-Transcriptomics-Overlay).

2\. Copy and paste xenium\_processor.py to your xenium output folder. This is the folder that is often called (output-XET####) and contains the experiment.xenium file from your measurement.

3\. Open a terminal in the xenium output folder (right-click in an empty space, click "Open in terminal").

4\. Make sure you have the required packages installed (see requirements).



**# The following is required to extract your full Xenium run**



5.. If you want to run xenium\_processor.py, you need to write the following command line in the terminal: python xenium\_processor.py "path/to/xenium/output"  

KEEP IN MIND! That the "path/to/xenium/output" is not literally this text. Change it to the folder path where your 'experiment.xenium' is stored. You can do this by copying your path on the top of your windows explorer or right clicking on the folder and selecting 'Copy as Path'. Change backward slashes (\\) to forward slashes (/). 

IMPORTANT! your path needs to be in between quotation marks "". 

6\. Now press the "Enter"-key.

7\. The script automates a few steps and results in the following.

&nbsp;	- Creates a new folder called: xenium\_output

&nbsp;	- Collects files from your output folder and places them in there

&nbsp;	- Creates a .GeoJSON file named: combined.geojson which contains: Cell\_ID, Cluster, Gene counts per gene and Spatial coordinates from each individual cell.

&nbsp;	- This .GeoJSON file is used in the software called ESCDAT which allows for the overlay of timsTOF-MSI and Xenium Spatial Transcriptomics data.

**STOP**



**# The following is required if you want to work with a selection of the cells, instead of all cells that are measured in your Xenium analysis.**



8\. In Xenium Explorer, select your cells, albeit using an ROI or cluster or a single cell.

9\. In Xenium explorer, click 'Cells' in the selection window. Press the three vertical dots (...) in the same line as 'Cell Stats'.

10\. Click 'Download Cell Stats as .csv'

11\. Rename your .csv to e.g, selected\_cells.csv and copy it to your xenium output folder.

12\. Delete the first two rows in the .csv file.

13\. Open a new terminal in your xenium output folder.

14\. In your terminal window, you now need to run the following command line: python xenium\_processor.py "path/to/xenium/output" --filter "path/to/xenium/output/selected\_cells.csv"

IMPORTANT! Keep the quotation marks in mind and also the name of your .csv file!

15\. The script automates a few steps and results in the following.

&nbsp;	- Creates a new folder called: xenium\_output

&nbsp;	- Collects files from your output folder and places them in there

&nbsp;	- Creates a .GeoJSON file named: filtered.geojson which contains: Cell\_ID, Cluster, Gene counts per gene and Spatial coordinates from each individual cell that you selected.

&nbsp;	- This .GeoJSON file is used in the software called ESCDAT which allows for the overlay of timsTOF-MSI and Xenium Spatial Transcriptomics data.

**STOP**





\## Requirements to run xenium\_processor.py



\- Python 3.7+



\- Required packages:



numpy

pandas

zarr



To install:

&nbsp; ```bash

&nbsp; py -m pip install numpy pandas zarr

&nbsp; ```



\## Installation of xenium\_processor.py



Download the `xenium\_processor.py` script to your local machine. No installation needed!



```bash

\# Download the script from:

wget https://https://github.com/M4i-Imaging-Mass-Spectrometry/MALDI-MSI---Spatial-Transcriptomics-Overlay



\# Or just copy the file to your working directory (xenium/output/folder) if you already have it downloaded.

```



\## Basic Usage

Open terminal in your Xenium output folder and run:



\### Process entire Xenium dataset

```bash

python xenium\_processor.py "/path/to/xenium/output/folder"

```



\### With cell filtering

```bash

python xenium\_processor.py "/path/to/xenium/folder" --filter "selected\_cells.csv"

```



"selected\_cells.csv" is the file you generate when you select a ROI in Xenium Explorer.



\### Custom output directory

```bash

python xenium\_processor.py "/path/to/xenium/folder" --output "./my\_analysis"

```



\## Input Files



The script automatically searches for these required files anywhere in your Xenium output folder:



| File | Description | Common Locations |

|------|-------------|------------------|

| `cell\_feature\_matrix.zarr.zip` | Compressed gene expression matrix | Root folder |

| `cell\_boundaries.csv` or `.csv.gz` | Cell polygon coordinates | `/analysis/` folder |

| `clusters.csv` | Cell cluster assignments | `/analysis/clustering/gene\_expression\_graphclust/` |

| `features.tsv.gz` | Gene feature list | `/cell\_feature\_matrix/` |



\*\*Note\*\*: The script searches recursively, so files can be anywhere in the directory tree.



\## Output Files



All outputs are saved to `./xenium\_output/` (or your specified output directory):



| File | Description |

|------|-------------|

| `combined.csv` | Master dataset with all cell data |

| `combined.geojson` | Spatial visualization file for full dataset |

| `filtered\_cells.csv` | Subset of cells (if --filter used) |

| `filtered\_cells.geojson` | Spatial visualization for filtered cells |



\### Combined.csv Structure

\- \*\*Barcode\*\*: Unique cell identifier

\- \*\*Cluster\*\*: Cluster assignment

\- \*\*Gene columns\*\*: Expression count for each gene

\- \*\*Total\*\*: Sum of all transcripts

\- \*\*x1-x25, y1-y25\*\*: Cell boundary coordinates (up to 25 vertices)



\## Cell Filtering



To analyze specific cell populations:



1\. Create a CSV file with cell IDs in one of these formats:

&nbsp;  - Column named `cell\_id`

&nbsp;  - Column named `Barcode`

&nbsp;  - First column (if no headers match)



2\. Run with the `--filter` flag:

&nbsp;  ```bash

&nbsp;  python xenium\_processor.py "/xenium/data" --filter "selected\_cells.csv"

&nbsp;  ```



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



\## Script Workflow Details



\### Step 1: File Discovery

\- Recursively searches the input folder

\- Identifies all required files automatically

\- Handles both compressed (.gz) and uncompressed files



\### Step 2: Zarr Processing

\- Reads sparse expression matrix

\- Converts to dense format

\- Outputs: `gene\_features.csv`



\### Step 3: Data Combination

\- Merges expression data with spatial coordinates

\- Adds cluster assignments

\- Removes unassigned cells

\- Pads coordinate arrays to uniform size (25 vertices)

\- Outputs: `combined.csv`



\### Step 4: GeoJSON Creation

\- Converts tabular data to GeoJSON format

\- Creates polygon features for each cell

\- Includes all expression data as properties

\- Outputs: `combined.geojson`



\## Troubleshooting



\### "Missing required files" error

\- Ensure all 4 required files are present in the Xenium output folder

\- Check that file names match exactly (case-sensitive on Linux/Mac)

\- Verify `.gz` files aren't corrupted



\### Multiple files found warning

\- The script will automatically choose the most likely file

\- For `clusters.csv`, it prefers files in `gene\_expression\_graphclust` folders





\## Example Workflow



```bash

\# 1. Basic processing

python xenium\_processor.py "/path/to/xenium/folder"



\# 2. Check the outputs

ls xenium\_output/

\# combined.csv  combined.geojson  gene\_features.csv



\# 3. Filter for specific cells

python xenium\_processor.py "/path/to/xenium/folder" --filter "selected\_cells.csv"



\# 4. Load in GeoJSON viewer

\# Open combined.geojson in QGIS, geojson.io, text editor, or custom viewer

```



\## Limitations



\- Maximum 25 vertices per cell polygon (additional vertices are truncated)

\- Requires all 4 input files to be present

\- Memory usage scales with dataset size



\## Citation



If you use this tool in your research, please cite the paper:

One Section, Two Worlds: Single-Cell Integration of MALDI-MSI and Spatial Transcriptomics on the Same Tissue Section



DOI: ###



\## Support



For issues or questions:

1\. Check that all input files are present

2\. Verify Python package versions

3\. Review error messages for specific missing files

4\. Ensure sufficient disk space for outputs



---



DETAILED STEPS ON HOW TO RUN xenium\_processor.py:



1\. Download xenium\_processor.py (https://https://github.com/M4i-Imaging-Mass-Spectrometry/MALDI-MSI---Spatial-Transcriptomics-Overlay).

2\. Copy and paste xenium\_processor.py to your xenium output folder. This is the folder that is often called (output-XET####) and contains the experiment.xenium file from your measurement.

3\. Open a terminal in the xenium output folder (right-click in an empty space, click "Open in terminal".

4\. If you want to run xenium\_processor.py you need to write the following command line in the terminal: python xenium\_processor.py "path/to/xenium/output"  

KEEP IN MIND! That the "path/to/xenium/output" is not literally this text. Change it to the path where your xenium.experiment is stored. You can do this by copying your path on the top of your windows explorer. 

IMPORTANT! your path needs to be in between quotation marks "". 

5\. Now press the "Enter"-key.

6\. The script automates a few steps and results in the following.

&nbsp;	- Creates a new folder called: xenium\_output

&nbsp;	- Collects files from your output folder and places them in there

&nbsp;	- Creates a .GeoJSON file named: combined.geojson which contains: Cell\_ID, Cluster, Gene counts per gene and Spatial coordinates from each individual cell.

7\. This file is used in the software called ESCDAT which allows for the overlay of timsTOF-MSI and Xenium Spatial Transcriptomics data.



!	The following is required if you want to work with a selection of the cells, instead of all cells that are measured in your Xenium analysis.



8\. In Xenium Explorer, select your cells, albeit using an ROI or cluster or a single cell.

9\. In Xenium explorer, click "Cells" in the selection window. Press the three vertical dots (...) in the same line as "Cell Stats".

10\. Click "Download Cell Stats as .csv

11\. Rename your .csv to e.g, selected\_cells.csv and copy it to your xenium output folder.

12\. Open a new terminal in your xenium output folder.

13\. In your terminal window, you now need to run the following command line: python xenium\_processor.py "path/to/xenium/output" --filter "path/to/xenium/output/selected\_cells.csv"

IMPORTANT! Keep the quotation marks in mind and also the name of your .csv file!

14\. The script automates a few steps and results in the following.

&nbsp;	- Creates a new folder called: xenium\_output

&nbsp;	- Collects files from your output folder and places them in there

&nbsp;	- Creates a .GeoJSON file named: filtered.geojson which contains: Cell\_ID, Cluster, Gene counts per gene and Spatial coordinates from each individual cell that you selected.

15\. This file is used in the software called ESCDAT which allows for the overlay of timsTOF-MSI and Xenium Spatial Transcriptomics data.











