from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from clean_common import LOCATION_MAP, core_clean
from utils import load_clean_files, map_values, write_output


REPO_ROOT = Path(__file__).resolve().parents[1]

EPICOLLECT_COLUMN_RENAMES = {
    "lat_location": "lat",
    "long_location": "lon",
    "longitude": "lon",
    "accuracy": "gps_accuracy",
    "lifestagetype": "life_stage",
    "carcass_location": "location",
    "hours_since_death": "carcass_age",
    "spawned": "spawning_success",
    "length_inches": "standard_length",
    "width_inches": "width",
    "surveyid": "id",
    "comments": "notes",
    "15_photo": "photo",
}

REDD_PRESENT_MAP = {
    "yes": True,
    "y": True,
    "true": True,
    "no": False,
    "n": False,
    "false": False,
    "r": True,
    "g": True,
}


def clean_epicollect_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = core_clean(df)

    drop_cols = ["title", "ec5_parent_uuid", "uploaded_at"]
    df = df.drop(columns=[col for col in drop_cols if col in df.columns])

    if "carcass_age_hours" in df.columns:
        df["carcass_age_hours"] = pd.to_numeric(df["carcass_age_hours"], errors="coerce")

    if "distance" in df.columns:
        df["distance"] = pd.to_numeric(df["distance"], errors="coerce").astype("Int64")

    if "carcass" in df.columns:
        df["location"] = map_values(df["carcass"], LOCATION_MAP, keep_unmapped=True)
        df = df.drop(columns=["carcass"])

    if "redd" in df.columns:
        df["redd"] = map_values(df["redd"], REDD_PRESENT_MAP, keep_unmapped=False)

    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean Epicollect salmon survey files.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=REPO_ROOT / "data" / "raw" / "salmon",
        help="Folder containing Epicollect raw CSV/XLSX files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "data" / "interim" / "epicollect_clean.csv",
        help="Cleaned Epicollect output file.",
    )
    parser.add_argument(
        "--pattern",
        default="epicollect",
        help="Optional filename substring to filter input files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cleaned = load_clean_files(
        args.input_dir,
        source="epicollect",
        clean_func=clean_epicollect_dataframe,
        column_replacements=EPICOLLECT_COLUMN_RENAMES,
        pattern=args.pattern,
    )
    write_output(cleaned, args.output)
    print(f"Wrote {len(cleaned):,} Epicollect rows to {args.output}")


if __name__ == "__main__":
    main()
