from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from utils import export_by_year, load_file, write_output

REPO_ROOT = Path(__file__).resolve().parents[1]


def merge_salmon_data(scanned: pd.DataFrame, epicollect: pd.DataFrame) -> pd.DataFrame:
    merged = pd.concat([scanned, epicollect], ignore_index=True, sort=False)

    sort_cols = [col for col in ["survey_date", "source", "source_file"] if col in merged.columns]
    if sort_cols:
        merged = merged.sort_values(sort_cols, kind="stable").reset_index(drop=True)

    return merged


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge cleaned scanned and Epicollect salmon data.")
    parser.add_argument(
        "--scanned",
        type=Path,
        default=REPO_ROOT / "data" / "interim" / "scanned_clean.csv",
        help="Cleaned scanned data file.",
    )
    parser.add_argument(
        "--epicollect",
        type=Path,
        default=REPO_ROOT / "data" / "interim" / "epicollect_clean.csv",
        help="Cleaned Epicollect data file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "data" / "processed" / "salmon_merged.csv",
        help="Merged processed output file.",
    )
    parser.add_argument(
        "--by-year-dir",
        type=Path,
        default=None,
        help="Optional folder for one CSV output per survey year.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scanned = load_file(args.scanned)
    epicollect = load_file(args.epicollect)
    merged = merge_salmon_data(scanned, epicollect)

    write_output(merged, args.output)
    if args.by_year_dir:
        export_by_year(merged, args.by_year_dir)

    print(f"Wrote {len(merged):,} merged rows to {args.output}")


if __name__ == "__main__":
    main()
