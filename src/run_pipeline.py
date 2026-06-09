
### INSTRUCTIONS: RUN THIS SCRIPT FOR PIPELINE

from __future__ import annotations
from pathlib import Path
from clean_epicollect import clean_epicollect_dataframe, EPICOLLECT_COLUMN_RENAMES
from clean_scanned import clean_scanned_dataframe, SCANNED_COLUMN_RENAMES
from merge_salmon import merge_salmon_data
from utils import export_by_year, load_clean_files, write_output
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    raw_salmon_dir = REPO_ROOT / "data" / "raw" / "salmon"
    interim_dir = REPO_ROOT / "data" / "interim"
    processed_dir = REPO_ROOT / "data" / "processed"

    scanned_output = interim_dir / "scanned_clean.csv"
    epicollect_output = interim_dir / "epicollect_clean.csv"
    merged_output = processed_dir / "salmon_merged.csv"
    by_year_dir = processed_dir / "by_year"

    print("1. Cleaning scanned files")
    scanned = load_clean_files(
        raw_salmon_dir,
        source="scanned",
        clean_func=clean_scanned_dataframe,
        column_replacements=SCANNED_COLUMN_RENAMES,
        pattern="scanned",
    )
    write_output(scanned, scanned_output)
    print(f"   Wrote {len(scanned):,} rows to {scanned_output}")

    print("2. Cleaning Epicollect files")
    epicollect = load_clean_files(
        raw_salmon_dir,
        source="epicollect",
        clean_func=clean_epicollect_dataframe,
        column_replacements=EPICOLLECT_COLUMN_RENAMES,
        pattern="epicollect",
    )
    write_output(epicollect, epicollect_output)
    print(f"   Wrote {len(epicollect):,} rows to {epicollect_output}")

    print("3. Merging salmon files")
    merged = merge_salmon_data(scanned, epicollect)
    write_output(merged, merged_output)
    export_by_year(merged, by_year_dir)
    print(f"   Wrote {len(merged):,} rows to {merged_output}")
    print(f"   Wrote by-year files to {by_year_dir}")


if __name__ == "__main__":
    main()
