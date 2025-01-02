#!/usr/bin/env python3

"""
Script Name: filter_crime_data.py
Description: Filters the original crime data CSV to include only specified suburbs and outputs the result to a new CSV file.
Author: @morebento
Date: July 2024

Usage:
    python filter_crime_data.py -i input1.csv input2.csv ... -o output.csv -s SUBURB1 SUBURB2 ...

Example:
    python filter_crime_data.py -i data-sa-crime-q1q3-2023-24.csv -o filtered-data-sa-crime.csv -s PARKSIDE UNLEY FULLARTON EASTWOOD
"""

import pandas as pd
import argparse
import os
import sys
from typing import List


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments containing input files, output file, and suburbs.
    """
    parser = argparse.ArgumentParser(
        description="Filter crime data CSV files for specified suburbs and merge them into a single output CSV."
    )
    parser.add_argument(
        '-i', '--input',
        metavar='INPUT_CSV',
        type=str,
        nargs='+',
        required=True,
        help='One or more input CSV files to be filtered and merged.'
    )
    parser.add_argument(
        '-o', '--output',
        metavar='OUTPUT_CSV',
        type=str,
        required=True,
        help='Output CSV file name for the filtered and merged data.'
    )
    parser.add_argument(
        '-s', '--suburbs',
        metavar='SUBURB',
        type=str,
        nargs='+',
        required=True,
        help='List of suburbs to filter the data by. Example: PARKSIDE UNLEY FULLARTON EASTWOOD'
    )
    return parser.parse_args()


def validate_files(input_files: List[str]) -> None:
    """
    Validates the existence of input files.

    Args:
        input_files (List[str]): List of input CSV file paths.

    Raises:
        FileNotFoundError: If any of the input files do not exist.
    """
    missing_files = [file for file in input_files if not os.path.isfile(file)]
    if missing_files:
        for file in missing_files:
            print(f"Error: Input file '{file}' does not exist.", file=sys.stderr)
        sys.exit(1)


def filter_crime_data(input_files: List[str], suburbs: List[str]) -> pd.DataFrame:
    """
    Filters the crime data for specified suburbs from multiple CSV files.

    Args:
        input_files (List[str]): List of input CSV file paths.
        suburbs (List[str]): List of suburbs to filter by.

    Returns:
        pd.DataFrame: Filtered and concatenated DataFrame.
    """
    filtered_chunks = []
    total_filtered_rows = 0

    for file in input_files:
        print(f"Processing file: {file}...")
        try:
            # Read the CSV file in chunks to handle large files efficiently
            chunksize = 10 ** 6  # Adjust based on your system's memory
            for chunk in pd.read_csv(file, chunksize=chunksize):
                # Ensure all required columns are present
                required_columns = [
                    "Reported Date",
                    "Suburb - Incident",
                    "Postcode - Incident",
                    "Offence Level 1 Description",
                    "Offence Level 2 Description",
                    "Offence Level 3 Description",
                    "Offence count"
                ]
                missing_cols = [col for col in required_columns if col not in chunk.columns]
                if missing_cols:
                    print(f"Error: The following required columns are missing in '{file}': {missing_cols}", file=sys.stderr)
                    sys.exit(1)

                # Filter rows where 'Suburb - Incident' is in the suburbs list
                filtered_chunk = chunk[chunk['Suburb - Incident'].isin(suburbs)].copy()
                rows_before = len(filtered_chunk)
                if rows_before > 0:
                    # Convert 'Offence count' to integer, handling non-numeric values
                    filtered_chunk['Offence count'] = pd.to_numeric(filtered_chunk['Offence count'], errors='coerce').fillna(0).astype(int)
                    filtered_chunks.append(filtered_chunk)
                    total_filtered_rows += rows_before
                    print(f" - {rows_before} rows filtered from this chunk.")
        except pd.errors.EmptyDataError:
            print(f"Warning: '{file}' is empty and will be skipped.", file=sys.stderr)
        except pd.errors.ParserError as e:
            print(f"Error: Failed to parse '{file}'. {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: An unexpected error occurred while processing '{file}'. {e}", file=sys.stderr)
            sys.exit(1)

    if not filtered_chunks:
        print("Warning: No data matched the specified suburbs in the provided input files.", file=sys.stderr)

    # Concatenate all filtered chunks
    if filtered_chunks:
        merged_data = pd.concat(filtered_chunks, ignore_index=True)
        print(f"Total filtered rows across all files: {total_filtered_rows}")
        return merged_data
    else:
        # Return an empty DataFrame with the required columns if no data is found
        return pd.DataFrame(columns=[
            "Reported Date",
            "Suburb - Incident",
            "Postcode - Incident",
            "Offence Level 1 Description",
            "Offence Level 2 Description",
            "Offence Level 3 Description",
            "Offence count"
        ])


def save_to_csv(df: pd.DataFrame, output_file: str) -> None:
    """
    Saves the DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): DataFrame to save.
        output_file (str): Output CSV file path.
    """
    try:
        # Sort the data by 'Reported Date' and 'Suburb - Incident' for better organization
        df.sort_values(by=["Reported Date", "Suburb - Incident"], inplace=True)
        # Save to CSV
        df.to_csv(output_file, index=False)
        print(f"Successfully saved filtered data to '{output_file}'. Total rows: {len(df)}.")
    except Exception as e:
        print(f"Error: Failed to write to '{output_file}'. {e}", file=sys.stderr)
        sys.exit(1)


def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Validate input files
    validate_files(args.input)

    # Filter crime data
    filtered_data = filter_crime_data(args.input, args.suburbs)

    # Save filtered data to output CSV
    save_to_csv(filtered_data, args.output)


if __name__ == "__main__":
    main()
