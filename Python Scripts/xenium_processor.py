#!/usr/bin/env python3
"""
Xenium Processor - Simple CLI wrapper for Xenium spatial transcriptomics analysis
Usage: python xenium_processor.py <xenium_folder> [--filter <cell_list.csv>] [--output <output_dir>]
"""

import os
import sys
import argparse
import gzip
import shutil
import json
from pathlib import Path

# Import required libraries
import numpy as np
import pandas as pd
import zarr


def find_xenium_files(base_path):
    """Find all required files by searching recursively in the directory tree"""
    base = Path(base_path)
    
    print("Searching for required files...")
    
    # Define what we're looking for
    file_patterns = {
        'zarr': 'cell_feature_matrix.zarr.zip',
        'boundaries': 'cell_boundaries.csv.gz',
        'clusters': 'clusters.csv',
        'features': 'features.tsv.gz'
    }
    
    # Also check for uncompressed boundaries file
    alt_patterns = {
        'boundaries': 'cell_boundaries.csv'
    }
    
    found_files = {}
    
    # Search for each file
    for name, pattern in file_patterns.items():
        print(f"  Looking for {pattern}...")
        
        # Search recursively
        matches = list(base.rglob(pattern))
        
        # If not found and there's an alternative, try that
        if not matches and name in alt_patterns:
            alt_pattern = alt_patterns[name]
            print(f"    Not found, trying {alt_pattern}...")
            matches = list(base.rglob(alt_pattern))
        
        if matches:
            # If multiple matches, try to pick the best one
            if len(matches) > 1:
                # For clusters.csv, prefer the one in gene_expression_graphclust
                if name == 'clusters' and pattern == 'clusters.csv':
                    gene_expr_matches = [m for m in matches if 'gene_expression_graphclust' in str(m)]
                    if gene_expr_matches:
                        matches = gene_expr_matches
                
                # Otherwise, just take the first one and warn
                print(f"    Warning: Found {len(matches)} matches for {pattern}, using: {matches[0]}")
            
            found_files[name] = matches[0]
            print(f"    ✓ Found: {matches[0].relative_to(base)}")
        else:
            print(f"    ✗ Not found!")
    
    # Check if all required files were found
    missing = []
    for name, pattern in file_patterns.items():
        if name not in found_files:
            missing.append(f"{name} ({pattern})")
    
    if missing:
        print("\nERROR: Could not find required files:")
        for m in missing:
            print(f"  - {m}")
        print(f"\nSearched in: {base}")
        print("Please ensure all required files are present somewhere in the directory tree.")
        sys.exit(1)
    
    return found_files


def prepare_working_directory(xenium_files, output_dir):
    """Copy/extract files to working directory"""
    work_dir = Path(output_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nPreparing files...")
    
    # Copy zarr file
    shutil.copy2(xenium_files['zarr'], work_dir / 'cell_feature_matrix.zarr.zip')
    
    # Handle boundaries file (might be .gz or .csv)
    boundaries_path = xenium_files['boundaries']
    if boundaries_path.suffix == '.gz':
        # Extract if compressed
        with gzip.open(boundaries_path, 'rb') as f_in:
            with open(work_dir / 'cell_boundaries.csv', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    else:
        # Just copy if already uncompressed
        shutil.copy2(boundaries_path, work_dir / 'cell_boundaries.csv')
    
    # Copy clusters
    shutil.copy2(xenium_files['clusters'], work_dir / 'clusters.csv')
    
    # Extract and process features
    with gzip.open(xenium_files['features'], 'rt') as f:
        lines = f.readlines()
    
    # Extract gene names (second column) and add "Total"
    gene_names = [line.split('\t')[1].strip() for line in lines]
    gene_names.append('Total')
    
    with open(work_dir / 'feature_list.csv', 'w') as f:
        for name in gene_names:
            f.write(f"{name}\n")
    
    return work_dir


def run_zarr_reader(work_dir):
    """Run zarr_reader_thing.py logic"""
    print("\nStep 1/3: Reading zarr file...")
    
    file = work_dir / "cell_feature_matrix.zarr.zip"
    result = zarr.open(file, 'r')
    
    data = np.array(result.cell_features.data)
    indices = np.array(result.cell_features.indices)
    indptr = np.array(result.cell_features.indptr)
    
    # Build the empty cell_count by feature_count matrix
    zeros = np.zeros((len(indptr) - 1, np.array(result.cell_features.cell_id.shape[0])))
    
    # Fill in the zeros array
    for i, (start, end) in enumerate(zip(indptr, indptr[1:])):
        if i % 10000 == 0:
            print(f"  Processing cell {i}/{len(indptr)-1}")
        index_slice = indices[start:end]
        data_slice = data[start:end]
        np.add.at(zeros[i], index_slice, data_slice)
    
    np.savetxt(work_dir / "gene_features.csv", zeros.T, fmt='%i', delimiter=',')
    print("  ✓ gene_features.csv created")


def run_combiner(work_dir):
    """Run combiner2.py logic"""
    print("\nStep 2/3: Combining data...")
    
    # Load data
    boundaries = pd.read_csv(work_dir / "cell_boundaries.csv")
    features = pd.read_csv(work_dir / "gene_features.csv", header=None)
    clusters = pd.read_csv(work_dir / "clusters.csv")
    
    # Apply feature names
    with open(work_dir / "feature_list.csv", 'r') as f:
        features.columns = [l.strip() for l in f.readlines()]
    
    # Drop unassigned cells
    unassigned = set(boundaries['cell_id']) - set(clusters['Barcode'])
    
    # Insert Barcode column
    features.insert(0, 'Barcode', boundaries['cell_id'].unique())
    
    # Drop unassigned rows
    features = features[~features['Barcode'].isin(unassigned)].reset_index(drop=True)
    boundaries = boundaries[~boundaries['cell_id'].isin(unassigned)].reset_index(drop=True)
    
    # Add cluster labels
    features.insert(1, 'Cluster', clusters['Cluster'])
    
    # Prepare zero-pads for coordinates
    n_cells = features.shape[0]
    max_verts = 25
    
    x_zeros = np.zeros((n_cells, max_verts))
    y_zeros = np.zeros((n_cells, max_verts))
    
    # Map cell_id to row index
    cell_to_idx = {
        cell_id: idx
        for idx, cell_id in enumerate(features['Barcode'])
    }
    
    # Fill boundary coordinates
    print("  Processing cell boundaries...")
    for cell_id, group in boundaries.groupby('cell_id'):
        idx = cell_to_idx[cell_id]
        coords = group[['vertex_x','vertex_y']].values
        n = coords.shape[0]
        
        if n >= max_verts:
            x_zeros[idx, :] = coords[:max_verts, 0]
            y_zeros[idx, :] = coords[:max_verts, 1]
        else:
            x_zeros[idx, :n] = coords[:, 0]
            y_zeros[idx, :n] = coords[:, 1]
            x_zeros[idx, n:] = coords[-1, 0]
            y_zeros[idx, n:] = coords[-1, 1]
    
    # Attach coordinates to features
    for i in range(max_verts):
        features[f'x{i+1}'] = x_zeros[:, i]
        features[f'y{i+1}'] = y_zeros[:, i]
    
    features.to_csv(work_dir / "combined.csv", index=False)
    print("  ✓ combined.csv created")


def run_geojson_maker(work_dir, input_file="combined.csv", output_file="combined.geojson"):
    """Run geo_json_maker.py logic"""
    print(f"\nStep 3/3: Creating GeoJSON from {input_file}...")
    
    df = pd.read_csv(work_dir / input_file)
    
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    row_count = df.shape[0]
    for index, row in df.iterrows():
        if index % 1000 == 0:
            print(f'  {(index / row_count) * 100:.1f}% processed')
        
        array_row = np.array(row)
        xs = array_row[array_row.size - 50::2]
        ys = array_row[array_row.size - 49::2]
        assert(len(xs) == len(ys) == 25)
        
        cell = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[x, y] for x, y in zip(xs, ys)]],
            },
            "properties": {
                "CellID": row["Barcode"],
                "Z": row["Cluster"],
                "GeneFeatures": list(array_row[3:array_row.size - 51]),
                "TotalFeatures": array_row[array_row.size - 51],
            }
        }
        geojson['features'].append(cell)
    
    with open(work_dir / output_file, 'w') as f:
        json.dump(geojson, f)
    
    print(f"  ✓ {output_file} created")


def run_filter(work_dir, filter_file):
    """Run filter_common.py logic"""
    print(f"\nFiltering cells using {filter_file}...")
    
    # Load full dataset
    big = pd.read_csv(work_dir / "combined.csv")
    
    # Load filter list
    small = pd.read_csv(filter_file, comment='#')
    
    # Detect ID column
    if 'cell_id' in small.columns:
        id_col = 'cell_id'
    elif 'Barcode' in small.columns:
        id_col = 'Barcode'
    else:
        id_col = small.columns[0]
    
    # Filter
    mask = big['Barcode'].isin(small[id_col])
    filtered = big.loc[mask]
    
    # Save
    output_name = "filtered_cells.csv"
    filtered.to_csv(work_dir / output_name, index=False)
    print(f"  ✓ Filtered {len(filtered)} cells to {output_name}")
    
    return output_name


def main():
    parser = argparse.ArgumentParser(
        description='Process Xenium spatial transcriptomics data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - process entire dataset
  python xenium_processor.py /path/to/xenium/folder
  
  # With filtering
  python xenium_processor.py /path/to/xenium/folder --filter cell_list.csv
  
  # Custom output directory
  python xenium_processor.py /path/to/xenium/folder --output /custom/output
        """
    )
    
    parser.add_argument('xenium_folder', help='Path to Xenium output folder')
    parser.add_argument('--filter', help='Optional: CSV file with cell IDs to filter')
    parser.add_argument('--output', help='Output directory (default: ./xenium_output)')
    
    args = parser.parse_args()
    
    # Set output directory
    output_dir = args.output if args.output else './xenium_output'
    
    print(f"Xenium Processor")
    print(f"================")
    print(f"Input: {args.xenium_folder}")
    print(f"Output: {output_dir}")
    if args.filter:
        print(f"Filter: {args.filter}")
    
    # Find required files
    xenium_files = find_xenium_files(args.xenium_folder)
    
    # Prepare working directory
    work_dir = prepare_working_directory(xenium_files, output_dir)
    
    # Run main pipeline
    run_zarr_reader(work_dir)
    run_combiner(work_dir)
    run_geojson_maker(work_dir)
    
    # Run filtering if requested
    if args.filter:
        filtered_csv = run_filter(work_dir, args.filter)
        # Create geojson for filtered data
        run_geojson_maker(work_dir, filtered_csv, "filtered_cells.geojson")
    
    print(f"\n✅ Processing complete!")
    print(f"Output files in: {output_dir}")
    print("  - combined.csv (full dataset)")
    print("  - combined.geojson (full dataset)")
    if args.filter:
        print("  - filtered_cells.csv")
        print("  - filtered_cells.geojson")


if __name__ == "__main__":
    main()