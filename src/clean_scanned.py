from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from clean_common import core_clean
from utils import load_clean_files, map_values, write_output


REPO_ROOT = Path(__file__).resolve().parents[1]

SCANNED_COLUMN_RENAMES = {
    "station": "",
    "survey_date": "survey_date",
    "life_stage": "life_stage",
    "carcass_age": "carcass_age",
    "spawning_success": "spawning_success",
    "adipose_fin": "adipose_fin",
    "adipose_fin?": "adipose_fin",
    "sighting": "type",
    "salmon_species": "species",
    "life_stage_type": "life_stage",
    "adult_spawner_carcass_age_type": "carcass_age",
    "visual_estimate": "",
    "redds_number": "redd",
    "redd_type": "redd_status",
    "comment": "notes",
    "comments": "notes",
    "temp": "temperature",
    "fish_number": "fish_count",
    "survey_id": "id",
}

REDD_SUBSTRATE_MAP = {
    "r": "riffle",
    "riffle": "riffle",
    "g": "gravel",
    "gravel": "gravel",
}


def clean_scanned_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = core_clean(df)

    if "redd" in df.columns:
        df["redd_substrate"] = map_values(df["redd"], REDD_SUBSTRATE_MAP, keep_unmapped=False)
        df = df.drop(columns=["redd"])

    if "distance" in df.columns:
        beach_mask = df["distance"].astype(str).str.contains("beach", case=False, na=False)
        if beach_mask.any():
            if "notes" not in df.columns:
                df["notes"] = ""
            df.loc[beach_mask, "notes"] = (
                df.loc[beach_mask, "notes"].fillna("").astype(str)
                + " original distance: "
                + df.loc[beach_mask, "distance"].astype(str)
            )
            df.loc[beach_mask, "distance"] = 0
        df["distance"] = pd.to_numeric(df["distance"], errors="coerce").astype("Int64")

    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean scanned salmon survey files.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=REPO_ROOT / "data" / "raw" / "salmon",
        help="Folder containing scanned raw CSV/XLSX files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "data" / "interim" / "scanned_clean.csv",
        help="Cleaned scanned output file.",
    )
    parser.add_argument(
        "--pattern",
        default="scanned",
        help="Optional filename substring to filter input files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cleaned = load_clean_files(
        args.input_dir,
        source="scanned",
        clean_func=clean_scanned_dataframe,
        column_replacements=SCANNED_COLUMN_RENAMES,
        pattern=args.pattern,
    )
    write_output(cleaned, args.output)
    print(f"Wrote {len(cleaned):,} scanned rows to {args.output}")


if __name__ == "__main__":
    main()
