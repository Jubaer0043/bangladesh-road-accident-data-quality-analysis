"""Conservative cleaning: preserve competing fields and expose unresolved conflicts."""

from datetime import date, datetime
import hashlib
import json
import re

import numpy as np
import pandas as pd

from .acquisition import verify_raw, write_json
from .config import COLUMNS, PROCESSED, REPORTS, TABLES, WORKBOOK

MISSING = {
    "",
    "unknown",
    "not known",
    "not available",
    "n/a",
    "na",
    "none",
    "null",
    "-",
}
MONTHS = {
    name: i
    for i, name in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        1,
    )
}


def text(value):
    if pd.isna(value):
        return pd.NA
    result = re.sub(r"\s+", " ", str(value)).strip()
    return pd.NA if result.casefold() in MISSING else result


def parse_date(value):
    """Respect stored Excel dates; parse slash strings day-first, flag ambiguity separately."""
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return pd.Timestamp(value).normalize()
    value = str(value).strip()
    for pattern in ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
        try:
            return pd.Timestamp(datetime.strptime(value, pattern)).normalize()
        except ValueError:
            pass
    return pd.NaT


def ambiguous_date(value):
    if not isinstance(value, str):
        return False
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})", value.strip())
    return bool(
        match
        and 1 <= int(match[1]) <= 12
        and 1 <= int(match[2]) <= 12
        and match[1] != match[2]
    )


def parse_hour(value):
    value = str(value).strip().upper().replace(".", ":")
    for pattern in ["%H:%M:%S", "%I:%M %p", "%H:%M"]:
        try:
            return datetime.strptime(value, pattern).hour
        except ValueError:
            pass
    return np.nan


def coordinates(value):
    # Use hemisphere markers rather than trusting the reversed source header.
    match = re.fullmatch(r"\s*([\d.]+)\s*°?\s*N\s*,\s*([\d.]+)\s*°?\s*E\s*", str(value))
    if not match:
        return (np.nan, np.nan)
    lat, lon = map(float, match.groups())
    return (lat, lon) if 0 <= lat <= 90 and 0 <= lon <= 180 else (np.nan, np.nan)


def prepare():
    verify_raw()
    for path in [PROCESSED, TABLES]:
        path.mkdir(parents=True, exist_ok=True)
    book = pd.ExcelFile(WORKBOOK, engine="openpyxl")
    if book.sheet_names != ["Sheet1"]:
        raise ValueError(f"Unexpected workbook sheets: {book.sheet_names}")
    raw = pd.read_excel(book, sheet_name="Sheet1")
    book.close()
    if list(raw.columns) != COLUMNS:
        raise ValueError("Workbook schema differs from the inspected v2 contract")
    inventory = []
    for column in raw.columns:
        normalized = raw[column].map(text)
        counts = normalized.value_counts(dropna=False)
        inventory.append(
            {
                "original_column": column,
                "dtype": str(raw[column].dtype),
                "raw_nulls": int(raw[column].isna().sum()),
                "missing_after_token_normalization": int(normalized.isna().sum()),
                "distinct_nonmissing": int(normalized.nunique()),
                "largest_value_count": int(counts.iloc[0]),
                "largest_value_share": float(counts.iloc[0] / len(raw)),
            }
        )
    pd.DataFrame(inventory).to_csv(TABLES / "column_inventory.csv", index=False)
    duplicates = raw.duplicated()
    source_rows = np.arange(2, len(raw) + 2)
    data = raw.loc[~duplicates].copy()
    data.columns = data.columns.str.strip()
    cleaned = pd.DataFrame(index=data.index)
    cleaned["source_row"] = source_rows[~duplicates.to_numpy()]
    mapping = {
        "serial_no": "Accident Serial No",
        "source_id": "ID",
        "declared_year": "Year",
        "declared_month_label": "Month",
        "location": "Location",
        "vehicle_description": "Vehicle Info",
        "fatalities": "Death Count",
        "injuries": "Injury Count",
        "vehicle_count": "Vehicle Count",
        "driver_age": "Driver  Age",
        "severity_label": "Accident_Intensity",
        "light_original": "Light Condition",
        "lighting": "Lighting",
        "weather_x": "Weather_x",
        "weather_y": "Weather_y",
        "road_surface": "Road Surface Type",
        "road_nature": "Road nature",
        "road_class": "Road classification",
        "road_condition": "Road Surface Condition",
        "place_characteristic": "Place characteristic",
        "victim_category": "Victim Category",
        "junction": "Junction",
        "traffic_control": "Traffic_Control",
    }
    numeric = [
        "serial_no",
        "source_id",
        "declared_year",
        "fatalities",
        "injuries",
        "vehicle_count",
        "driver_age",
    ]
    invalid_numbers = {}
    for name, original in mapping.items():
        cleaned[name] = data[original].map(text).astype("string")
        if name in numeric:
            values = pd.to_numeric(cleaned[name], errors="coerce")
            bad = cleaned[name].notna() & (values.isna() | ~np.isfinite(values))
            invalid_numbers[name] = int(bad.sum())
            if (
                bad.any()
                or (values.dropna() % 1).ne(0).any()
                or values.dropna().lt(0).any()
            ):
                raise ValueError(f"Invalid nonnegative integer field: {name}")
            cleaned[name] = values.astype("Int64")
    cleaned["date_parsed"] = pd.to_datetime(data.Date.map(parse_date))
    cleaned["date_ambiguous"] = data.Date.map(ambiguous_date)
    cleaned["date_year"] = cleaned.date_parsed.dt.year.astype("Int64")
    cleaned["date_month"] = cleaned.date_parsed.dt.month.astype("Int64")
    cleaned["declared_month"] = cleaned.declared_month_label.map(MONTHS).astype("Int64")
    cleaned["date_year_conflict"] = (
        cleaned.date_year.ne(cleaned.declared_year) & cleaned.date_year.notna()
    ).fillna(False)
    cleaned["date_month_conflict"] = (
        cleaned.date_month.ne(cleaned.declared_month) & cleaned.date_month.notna()
    ).fillna(False)
    cleaned["hour"] = data.Time.map(parse_hour).astype("Int64")
    cleaned["time_band"] = pd.cut(
        cleaned.hour.astype(float),
        [-1, 5, 11, 17, 23],
        labels=["00–05", "06–11", "12–17", "18–23"],
    ).astype("string")
    cleaned[["latitude", "longitude"]] = pd.DataFrame(
        data["Longitude and Latitude"].map(coordinates).tolist(), index=data.index
    )
    cleaned["inside_broad_bd_box"] = cleaned.latitude.between(
        20, 27
    ) & cleaned.longitude.between(88, 93)
    cleaned["fatal_record"] = cleaned.fatalities.gt(0).astype("Int64")
    # This is an operational consistency flag, not proof the labels were intended to encode fatalities.
    cleaned["severity_fatality_disagreement"] = cleaned.severity_label.eq("Death").ne(
        cleaned.fatal_record.eq(1)
    )
    cleaned["weather_disagreement"] = (
        cleaned.weather_x.str.casefold()
        .ne(cleaned.weather_y.str.casefold())
        .fillna(False)
    )
    cleaned["light_disagreement"] = (
        cleaned.light_original.str.casefold()
        .ne(cleaned.lighting.str.casefold())
        .fillna(False)
    )
    cleaned["road_nature"] = cleaned.road_nature.replace({"Two-lane": "Two-Lane"})
    cleaned["victim_category"] = cleaned.victim_category.replace(
        {"Vehicle owner": "Vehicle Owner", "Bicyclist": "Cyclist"}
    )
    # Narrative participates in LOCAL matching, but names/narratives are not exported.
    signature_fields = [
        "Date",
        "Time",
        "Location",
        "Accident Narrative",
        "Vehicle Info",
    ]

    def signature(row):
        payload = ["" if pd.isna(text(v)) else str(text(v)).casefold() for v in row]
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False).encode()
        ).hexdigest()

    cleaned["descriptor_group"] = data[signature_fields].apply(signature, axis=1)
    group_size = cleaned.groupby("descriptor_group").source_row.transform("size")
    cleaned["descriptor_group_size"] = group_size
    grouped = cleaned.groupby("descriptor_group").agg(
        records=("source_row", "size"),
        declared_years=("declared_year", "nunique"),
        fatality_values=("fatalities", "nunique"),
        severity_values=("severity_label", "nunique"),
        weather_values=("weather_y", "nunique"),
    )
    grouped.reset_index().to_csv(TABLES / "descriptor_groups.csv", index=False)
    quality = {
        "schema_valid": True,
        "sheet_names": ["Sheet1"],
        "original_rows": len(raw),
        "original_columns": len(raw.columns),
        "exact_duplicate_rows_removed": int(duplicates.sum()),
        "cleaned_rows": len(cleaned),
        "raw_null_cells": int(raw.isna().sum().sum()),
        "invalid_numeric_counts": invalid_numbers,
        "invalid_dates": int(cleaned.date_parsed.isna().sum()),
        "ambiguous_slash_dates": int(cleaned.date_ambiguous.sum()),
        "parseable_dates": int(cleaned.date_parsed.notna().sum()),
        "date_year_conflicts": int(cleaned.date_year_conflict.sum()),
        "date_month_conflicts": int(cleaned.date_month_conflict.sum()),
        "invalid_times": int(cleaned.hour.isna().sum()),
        "invalid_coordinates": int(cleaned.latitude.isna().sum()),
        "declared_year_min": int(cleaned.declared_year.min()),
        "declared_year_max": int(cleaned.declared_year.max()),
        "parsed_date_min": str(cleaned.date_parsed.min().date()),
        "parsed_date_max": str(cleaned.date_parsed.max().date()),
        "distinct_serial_numbers": int(cleaned.serial_no.nunique()),
        "distinct_source_ids": int(cleaned.source_id.nunique()),
        "repeated_serial_excess_rows": int(cleaned.duplicated("serial_no").sum()),
        "repeated_source_id_excess_rows": int(cleaned.duplicated("source_id").sum()),
        "descriptor_groups": len(grouped),
        "excess_descriptor_rows": len(cleaned) - len(grouped),
        "groups_with_conflicting_fatality_values": int(
            grouped.fatality_values.gt(1).sum()
        ),
        "groups_spanning_multiple_declared_years": int(
            grouped.declared_years.gt(1).sum()
        ),
        "weather_disagreements": int(cleaned.weather_disagreement.sum()),
        "light_disagreements": int(cleaned.light_disagreement.sum()),
        "severity_fatality_disagreements": int(
            cleaned.severity_fatality_disagreement.sum()
        ),
        "dominant_date_rows": int(data.Date.astype(str).value_counts().iloc[0]),
        "dominant_narrative_rows": int(
            data["Accident Narrative"].value_counts().iloc[0]
        ),
        "dominant_time_rows": int(data.Time.value_counts().iloc[0]),
        "dominant_coordinate_rows": int(
            data["Longitude and Latitude"].value_counts().iloc[0]
        ),
        "source_column_present": False,
        "cross_source_overlap_resolvable": False,
        "quality_status": "NOT FIT for national trends, incident-risk estimation, or causal safety conclusions",
        "allowed_use": "Descriptive audit of the published workbook, conditional exploratory comparisons, and sensitivity analysis",
        "strict_temporal_cohort_rows": int(
            (
                cleaned.date_parsed.notna()
                & ~cleaned.date_year_conflict
                & ~cleaned.date_ambiguous
            ).sum()
        ),
    }
    cleaned.to_csv(
        PROCESSED / "cleaned_records.csv", index=False, date_format="%Y-%m-%d"
    )
    write_json(REPORTS / "data_quality.json", quality)
    verify_raw()
    return cleaned, quality
