from __future__ import annotations
import re
from pathlib import Path
from typing import Callable, Iterable
import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError

## Load File ###

def load_file(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if path.suffix.lower() == ".csv":
        try:
            return pd.read_csv(path)
        except EmptyDataError:
            return pd.DataFrame()
    raise ValueError(f"Unsupported file type: {path}")

## Find Path ###

def discover_input_files(input_dir: str | Path, pattern: str | None = None) -> list[Path]:
    input_dir = Path(input_dir)
    files = [
        path
        for path in sorted(input_dir.iterdir())
        if path.suffix.lower() in {".csv", ".xlsx", ".xls"}
    ]
    if pattern:
        pattern = pattern.lower()
        files = [path for path in files if pattern in path.name.lower()]
    return files

### Load Cleaning Files ###

def load_clean_files(
    input_dir: str | Path,
    source: str,
    clean_func: Callable[[pd.DataFrame], pd.DataFrame],
    column_replacements: dict[str, str],
    pattern: str | None = None,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in discover_input_files(input_dir, pattern):
        df = load_file(path)
        if df.empty:
            continue

        df = clean_column_names(df, column_replacements)
        df = coalesce_duplicate_columns(df)
        df = clean_func(df)
        df["source"] = source
        df["source_file"] = path.name
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True, sort=False)

### Write Output ###

def write_output(df: pd.DataFrame, output: str | Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".csv":
        df.to_csv(output, index=False)
    elif output.suffix.lower() in {".xlsx", ".xls"}:
        df.to_excel(output, index=False)
    else:
        raise ValueError("Output must end with .csv, .xlsx, or .xls")

### Export by Year ###

def export_by_year(df: pd.DataFrame, output_dir: str | Path, prefix: str = "salmon") -> None:
    if "survey_year" not in df.columns:
        raise ValueError("DataFrame must contain a survey_year column")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for year in sorted(df["survey_year"].dropna().unique()):
        subset = df[df["survey_year"] == year]
        subset.to_csv(output_dir / f"{prefix}_{int(year)}.csv", index=False)

### Clean Column Names ###

def clean_column_names(df: pd.DataFrame, replacements: dict[str, str]) -> pd.DataFrame:
    df = df.copy()
    cols = [_basic_column_name(col) for col in df.columns]
    cols = [replacements.get(col, col) for col in cols]
    cols = [col.replace("_location", "") for col in cols]
    cols = [col.strip("_") for col in cols]

    final_replacements = {
        "unnamed_0": "",
        "latitude": "lat",
        "startdate": "survey_date",
        "creationdate": "created_at",
        "createdat": "created_at",
        "ec5createdat": "created_at",
        "accuracy": "gps_accuracy",
        "reddnr": "redd",
        "speciesid": "species",
        "length": "standard_length",
    }
    cols = [final_replacements.get(col, col) for col in cols]

    df.columns = cols
    drop_cols = [col for col in df.columns if col == ""]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    return df

### Map Values ###

def map_values(series: pd.Series, mapping: dict, keep_unmapped: bool) -> pd.Series:
    def map_one(value: object) -> object:
        if pd.isna(value):
            return pd.NA

        key = str(value).lower().strip()
        if key in {"", "nan"}:
            return pd.NA

        if key in mapping:
            return mapping[key]

        first_token = key.split()[0]
        if first_token in mapping:
            return mapping[first_token]

        return key if keep_unmapped else np.nan

    return series.map(map_one)

### Handle Duplicate Columns ###

def coalesce_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    if not df.columns.duplicated().any():
        return df

    out = pd.DataFrame(index=df.index)
    for col in dict.fromkeys(df.columns):
        same_name = df.loc[:, df.columns == col]
        if same_name.shape[1] == 1:
            out[col] = same_name.iloc[:, 0]
        else:
            out[col] = same_name.bfill(axis=1).iloc[:, 0]
    return out

### If missing column error ####

def require_columns(df: pd.DataFrame, columns: Iterable[str], context: str) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"{context} is missing required column(s): {missing_text}")

### Basic Column Name Treatment ####

def _basic_column_name(col: object) -> str:
    col = str(col).strip().lower()
    col = col.replace("[station]", "")
    col = re.sub(r"[^0-9a-zA-Z]+", "_", col)
    col = re.sub(r"_+", "_", col)
    return col.strip("_")
