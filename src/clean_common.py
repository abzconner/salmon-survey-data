from __future__ import annotations
import numpy as np
import pandas as pd
from utils import map_values

### Mappings that are shared between epicollect and scanned sheets ###

SPECIES_MAP = {
    "ch": "chum",
    "ch *": "chum",
    "co": "coho",
    "ct": "cutthroat",
    "resident cutthroat": "cutthroat",
    "u": np.nan,
    "un": np.nan,
    "unk": np.nan,
    "unknown": np.nan,
    "?": np.nan,
}

TYPE_MAP = {
    "r": "redd",
    "pr": "redd",
    "partial_redd": "redd",
    "partial redd": "redd",
    "d": "dead",
    "l": "live",
    "a": "adult",
    "f": np.nan,
    "-": np.nan,
}

STATUS_MAP = {
    "d": "dead",
    "dl": "dead",
    "l": "live",
    "r": "remnant",
    "a": "adult",
}

LIFE_STAGE_MAP = {
    "a": "adult",
    "y": "young",
    "young of year": "young", ## check this?
    "u": np.nan,
    "unknown": np.nan,
    "?": np.nan,
}

SEX_MAP = {
    "m": "male",
    "f": "female",
    "u": np.nan,
    "unknown": np.nan,
}

ADIPOSE_MAP = {
    "y": "yes",
    "n": "no",
    "u": np.nan,
    "unk": np.nan,
    "unknown": np.nan,
}

SPAWNING_MAP = {
    "s": "spawned",
    "uns": "unspawned",
    "p": "partially spawned",
    "partial": "partially spawned",
    "u": np.nan,
    "unk": np.nan,
    "unknown": np.nan,
}

PREDATION_MAP = {
    "y": "yes",
    "n": "no",
    "p": "partial",
    "s": "scavenged",
    "y/s":"scavenged",
    "u": np.nan,
    "unknown": np.nan,
}

CARCASS_AGE_MAP = {
    "u": np.nan,
    "unk": np.nan,
    "unknown": np.nan,
    "-": np.nan,
    "y": np.nan,
    "72+": 72,
    "48-72": 60,
    "1-12 hours": 6,
    "12-24 hours": 18,
    "greater than 24 hours": 24,
    "less than 1 hour": 0,
    "4848": 48,
}

LOCATION_MAP = {
    "on creek bank": "on bank",
    "outside of creek": "outside creek",
}

####### Cleaning Pipeline ##########

def core_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

# Standardizing date/year
    if "survey_date" not in df.columns and "created_at" in df.columns:
        df["survey_date"] = df["created_at"]
    if "survey_date" in df.columns:
        df["survey_date"] = parse_datetime(df["survey_date"])
        if pd.api.types.is_datetime64tz_dtype(df["survey_date"]):
            df["survey_date"] = df["survey_date"].dt.tz_localize(None)
        df["survey_year"] = df["survey_date"].dt.year.astype("Int64")

# Treating Created/Uploaded Dates
    for col in ["created_at", "uploaded_at"]:
        if col in df.columns:
            df[col] = parse_datetime(df[col])

# Transforming columns into numeric
    for col in ["lat", "lon", "standard_length", "width", "temperature", "fish_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

# Mapping Species
    if "species" in df.columns:
        df["species"] = map_values(df["species"], SPECIES_MAP, keep_unmapped=True)

# Mapping Status and Type
    if "status" in df.columns:
        status_norm = map_values(df["status"], STATUS_MAP, keep_unmapped=True)
        if "type" in df.columns:
            type_norm = map_values(df["type"], TYPE_MAP, keep_unmapped=True)
            df["type"] = type_norm.combine_first(status_norm)
        else:
            df["type"] = status_norm
        df = df.drop(columns=["status"])
    elif "type" in df.columns:
        df["type"] = map_values(df["type"], TYPE_MAP, keep_unmapped=True)
    else:
        df["type"] = np.nan

## Mapping Other Columns
    mapped_columns = {
        "life_stage": LIFE_STAGE_MAP,
        "sex": SEX_MAP,
        "adipose_fin": ADIPOSE_MAP,
        "spawning_success": SPAWNING_MAP,
        "predation": PREDATION_MAP,
    }
    for col, mapping in mapped_columns.items():
        if col in df.columns:
            df[col] = map_values(df[col], mapping, keep_unmapped=True)

## Normalize Carcass Age
    if "carcass_age" in df.columns:
        df["carcass_age_hours"] = df["carcass_age"].apply(normalize_carcass_age)
        df = df.drop(columns=["carcass_age"])

## Mapping of Location
    if "location" in df.columns:
        df["location"] = map_values(df["location"], LOCATION_MAP, keep_unmapped=True)

## Mapping of Size
    if "size" in df.columns:
        size = df["size"].replace({"u": np.nan, "unknown": np.nan})
        extracted = size.astype(str).str.extract(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)")
        df["standard_length"] = pd.to_numeric(extracted[0], errors="coerce")
        df["width"] = pd.to_numeric(extracted[1], errors="coerce")
        df = df.drop(columns=["size"])

    return df

## Normalizing Carcass Age
def normalize_carcass_age(value: object) -> float:
    if pd.isna(value):
        return np.nan

    key = str(value).lower().strip()
    if key in CARCASS_AGE_MAP:
        return CARCASS_AGE_MAP[key]

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return np.nan

    return 48 if parsed == 4848 else parsed

## Dealing with annoying date times
def parse_datetime(series: pd.Series) -> pd.Series:
    try:
        return pd.to_datetime(series, errors="coerce", format="mixed", utc=True).dt.tz_localize(None)
    except TypeError:
        return pd.to_datetime(series, errors="coerce")
