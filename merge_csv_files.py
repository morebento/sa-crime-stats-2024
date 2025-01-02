#!/usr/bin/env python3

"""
Script Name: merge_crime_data.py
Description: Merges multiple CSV files containing crime data into a single CSV file based on a predefined schema.
             Ensures that there are no duplicate records by aggregating 'Offence count' for logical duplicates.
Author: @morebento
Date: July 2024

Usage:
    python merge_crime_data.py input1.csv input2.csv ... -o output.csv

Example:
    python merge_crime_data.py july.csv august.csv september.csv -o merged_crime_data.csv
"""

import pandas as pd
import argparse
import os
import sys
from typing import List

# Define the required schema
REQUIRED_COLUMNS = [
    "Reported Date",
    "Suburb - Incident",
    "Postcode - Incident",
    "Offence Level 1 Description",
    "Offence Level 2 Description",
    "Offence Level 3 Description",
    "Offence count"
]

def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments containing input files and output file.
    """
    parser = argparse.ArgumentParser(
        description="Merge multiple crime data CSV files into a single CSV based on a predefined schema."
    )
    parser.add_argument(
        "input_files",
        metavar="INPUT_CSV",
        type=str,
        nargs="+",
        help="One or more input CSV files to be merged."
    )
    parser.add_argument(
        "-o", "--output",
        metavar="OUTPUT_CSV",
        type=str,
        required=True,
        help="Output CSV file name for the merged data."
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

def validate_columns(df: pd.DataFrame, file_name: str) -> None:
    """
    Validates that the DataFrame contains all required columns.

    Args:
        df (pd.DataFrame): DataFrame to validate.
        file_name (str): Name of the source file (for error messages).

    Raises:
        ValueError: If any required columns are missing.
    """
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"Error: The following required columns are missing in '{file_name}': {missing_cols}", file=sys.stderr)
        sys.exit(1)

def merge_csv_files(input_files: List[str], output_file: str) -> None:
    """
    Merges multiple CSV files into a single CSV file based on the predefined schema.
    Ensures no duplicate records by aggregating 'Offence count' for logical duplicates.

    Args:
        input_files (List[str]): List of input CSV file paths.
        output_file (str): Output CSV file path.
    """
    merged_data = []
    total_rows = 0

    for file in input_files:
        print(f"Processing file: {file}...")
        try:
            # Read the CSV file
            df = pd.read_csv(file, dtype=str)  # Read all columns as strings to prevent dtype issues
            validate_columns(df, file)

            # Select only the required columns
            df = df[REQUIRED_COLUMNS]

            # Convert 'Offence count' to integer
            df['Offence count'] = pd.to_numeric(df['Offence count'], errors='coerce').fillna(0).astype(int)

            # Append to the list
            merged_data.append(df)
            total_rows += len(df)
            print(f" - {len(df)} rows added from '{file}'.")

        except pd.errors.EmptyDataError:
            print(f"Warning: '{file}' is empty and will be skipped.", file=sys.stderr)
        except pd.errors.ParserError as e:
            print(f"Error: Failed to parse '{file}'. {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: An unexpected error occurred while processing '{file}'. {e}", file=sys.stderr)
            sys.exit(1)

    if not merged_data:
        print("Error: No data to merge. Please check the input files.", file=sys.stderr)
        sys.exit(1)

    # Concatenate all DataFrames
    print(f"Merging {len(merged_data)} files with a total of {total_rows} rows...")
    merged_df = pd.concat(merged_data, ignore_index=True)

    # Remove exact duplicate rows
    exact_duplicates = merged_df.duplicated().sum()
    if exact_duplicates > 0:
        print(f"Found {exact_duplicates} exact duplicate rows. Removing them...")
        merged_df.drop_duplicates(inplace=True)

    # Identify and aggregate logical duplicates
    grouping_columns = [
        "Reported Date",
        "Suburb - Incident",
        "Postcode - Incident",
        "Offence Level 1 Description",
        "Offence Level 2 Description",
        "Offence Level 3 Description"
    ]

    # Check for logical duplicates
    duplicate_counts = merged_df.duplicated(subset=grouping_columns, keep=False).sum()
    if duplicate_counts > 0:
        print(f"Found {duplicate_counts} logical duplicate rows. Aggregating 'Offence count'...")

        # Group by the defined columns and sum 'Offence count'
        merged_df = merged_df.groupby(grouping_columns, as_index=False)["Offence count"].sum()

    # Optional: Sort the data by 'Reported Date' and other relevant columns
    merged_df.sort_values(by=["Reported Date", "Suburb - Incident"], inplace=True)

    # Save to the output CSV
    try:
        merged_df.to_csv(output_file, index=False)
        print(f"Successfully merged data saved to '{output_file}'. Total unique rows: {len(merged_df)}.")
    except Exception as e:
        print(f"Error: Failed to write to '{output_file}'. {e}", file=sys.stderr)
        sys.exit(1)

def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Validate input files
    validate_files(args.input_files)

    # Merge CSV files with duplicate handling
    merge_csv_files(args.input_files, args.output)

if __name__ == "__main__":
    main()
