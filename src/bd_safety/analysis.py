import pandas as pd
from scipy import stats

from .acquisition import verify_raw, write_json
from .config import REPORTS, TABLES
from .model import export_sql, read_clean
from .statistics import (
    contingency_effect,
    conditional_cluster_interval,
    descriptor_bounds,
    night_day_effect,
)


def analyze():
    verify_raw()
    frame = read_clean()
    export_sql()
    dimensions = [
        "road_class",
        "road_condition",
        "road_surface",
        "weather_x",
        "weather_y",
        "lighting",
        "light_original",
        "time_band",
        "victim_category",
    ]
    for column in dimensions:
        summary = frame.groupby(column, dropna=False).agg(
            records=("source_row", "size"),
            fatal_records=("fatal_record", "sum"),
            summed_fatality_values=("fatalities", "sum"),
            mean_fatality_value=("fatalities", "mean"),
        )
        summary["fatal_record_share"] = summary.fatal_records / summary.records
        summary.to_csv(TABLES / f"{column}.csv")
    for field in ["fatalities", "injuries", "vehicle_count"]:
        frame.groupby(field).size().rename("records").to_csv(
            TABLES / f"{field}_distribution.csv"
        )
    for left, right in [
        ("severity_label", "fatalities"),
        ("weather_x", "weather_y"),
        ("light_original", "lighting"),
        ("declared_year", "date_year"),
    ]:
        pd.crosstab(frame[left], frame[right]).to_csv(
            TABLES / f"cross_{left}_{right}.csv"
        )
    coordinates = (
        frame.dropna(subset=["latitude", "longitude"])
        .groupby(["latitude", "longitude"])
        .size()
        .rename("records")
        .reset_index()
    )
    coordinates.to_csv(TABLES / "coordinates.csv", index=False)
    mode = coordinates.sort_values("records", ascending=False).iloc[0]
    geography = {
        "valid_coordinate_records": int(coordinates.records.sum()),
        "distinct_coordinate_pairs": len(coordinates),
        "latitude_min": float(coordinates.latitude.min()),
        "latitude_max": float(coordinates.latitude.max()),
        "longitude_min": float(coordinates.longitude.min()),
        "longitude_max": float(coordinates.longitude.max()),
        "dominant_coordinate_records": int(mode.records),
        "dominant_latitude": float(mode.latitude),
        "dominant_longitude": float(mode.longitude),
        "district_or_division_column_present": False,
        "interpretation": "Coordinates and free-text locations do not establish national coverage; no validated administrative or route boundaries",
    }
    write_json(REPORTS / "geographic_coverage.json", geography)
    rows = []
    scenarios = {
        "Exact-row deduplication only": frame,
        "One earliest row per source ID (unverified identity)": frame.drop_duplicates(
            "source_id"
        ),
        "One earliest row per descriptor group (unverified identity)": frame.drop_duplicates(
            "descriptor_group"
        ),
        "One latest row per descriptor group (unverified identity)": frame.drop_duplicates(
            "descriptor_group", keep="last"
        ),
    }
    for label, sample in scenarios.items():
        rows.append(
            {
                "scenario": label,
                "records": len(sample),
                "fatal_record_share": float(sample.fatal_record.mean()),
                "summed_fatality_values": int(sample.fatalities.sum()),
                **night_day_effect(sample),
            }
        )
    pd.DataFrame(rows).to_csv(TABLES / "duplicate_sensitivity.csv", index=False)
    rho = stats.spearmanr(frame.fatalities, frame.injuries).statistic
    result = {
        "analysis_unit": "Published workbook record; independently verified accidents unavailable",
        "descriptive_effects": [
            contingency_effect(frame, field)
            for field in [
                "lighting",
                "light_original",
                "weather_y",
                "weather_x",
                "severity_label",
                "road_class",
            ]
        ],
        "night_day_effect": night_day_effect(frame),
        "night_day_alternative_light_field": night_day_effect(frame, "light_original"),
        "conditional_bootstrap": conditional_cluster_interval(frame),
        "descriptor_sensitivity_bounds": descriptor_bounds(frame),
        "fatality_injury_spearman_rho": float(rho),
        "p_values_withheld": True,
        "population_safety_confidence_intervals_withheld": True,
        "reason": "Source attribution, chronology, incident identity, and field validity remain unresolved",
        "summed_fatality_values": int(frame.fatalities.sum()),
        "summed_injury_values": int(frame.injuries.sum()),
        "fatal_record_share": float(frame.fatal_record.mean()),
    }
    write_json(REPORTS / "statistics.json", result)
    verify_raw()
    return result
