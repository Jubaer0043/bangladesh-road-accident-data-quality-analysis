from contextlib import closing
import re
import sqlite3

import pandas as pd

from .acquisition import verify_raw, write_json
from .config import DB, PROCESSED, REPORTS, ROOT, TABLES

MODEL_COLUMNS = "source_row serial_no source_id declared_year declared_month date_parsed date_year date_month date_year_conflict date_month_conflict hour time_band location fatalities injuries vehicle_count fatal_record severity_label light_original lighting weather_x weather_y road_class road_condition road_surface victim_category latitude longitude descriptor_group".split()
PATTERNS = {
    "Truck": r"\btruck\b",
    "Motorcycle": r"\bmotorcycle\b|\bmotorbike\b|\bmotocrycle\b",
    "Bus": r"\bbus\b",
    "Car": r"\bcar\b",
    "Rickshaw (unspecified)": r"\brickshaw\b",
    "Van (including covered van)": r"\bvan\b",
    "Pickup": r"\bpickup\b",
    "Scooter": r"\bscooter\b|\bscooty\b",
    "Bicycle": r"\bbicycle\b|\bcyclist\b",
    "Pedestrian": r"\bpedestrian\b|\bpedestian\b",
}


def participants(description):
    if pd.isna(description):
        return ["Unclassified"]
    matched = [
        name
        for name, pattern in PATTERNS.items()
        if re.search(pattern, str(description), re.I)
    ]
    return matched or ["Unclassified"]


def connect():
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys=ON")
    return con


def read_clean():
    path = PROCESSED / "cleaned_records.csv"
    if not path.exists():
        raise FileNotFoundError("Run clean first")
    return pd.read_csv(path, parse_dates=["date_parsed"])


def build_model(frame=None):
    verify_raw()
    frame = read_clean() if frame is None else frame
    staging = PROCESSED / "records.build.sqlite3"
    staging.unlink(missing_ok=True)
    try:
        with closing(sqlite3.connect(staging)) as con:
            con.executescript((ROOT / "sql/01_schema.sql").read_text())
            frame[MODEL_COLUMNS].to_sql("records", con, if_exists="append", index=False)
            bridge = pd.DataFrame(
                [
                    (int(r.source_row), kind)
                    for r in frame.itertuples()
                    for kind in participants(r.vehicle_description)
                ],
                columns=["source_row", "participant_type"],
            )
            bridge.to_sql("participants", con, if_exists="append", index=False)
            if (
                con.execute("PRAGMA integrity_check").fetchone()[0] != "ok"
                or con.execute("PRAGMA foreign_key_check").fetchall()
            ):
                raise ValueError("SQLite integrity or foreign-key validation failed")
            if con.execute("SELECT COUNT(*) FROM records").fetchone()[0] != len(frame):
                raise ValueError("Model record-count mismatch")
            con.commit()
        staging.replace(DB)
    finally:
        staging.unlink(missing_ok=True)
    result = {
        "records": len(frame),
        "participant_links": len(bridge),
        "row_key": "source_row",
        "grain": "Exact-deduplicated published workbook records",
        "passed": True,
    }
    write_json(REPORTS / "model_validation.json", result)
    return result


def export_sql():
    with closing(connect()) as con:
        for path in sorted((ROOT / "sql").glob("*.sql")):
            if path.name.startswith("01_"):
                continue
            pd.read_sql_query(path.read_text(), con).to_csv(
                TABLES / f"{path.stem[3:]}.csv", index=False
            )
