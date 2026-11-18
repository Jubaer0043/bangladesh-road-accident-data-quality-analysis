import json
from contextlib import closing

import numpy as np
import pandas as pd

from .acquisition import verify_raw, write_json
from .config import FIGURES, REPORTS, ROOT, TABLES, WORKBOOK
from .model import connect, read_clean
from .notebooks import NOTEBOOK_NAMES
from .statistics import night_day_effect


def validate():
    verify_raw()
    d = read_clean()
    q = json.loads((REPORTS / "data_quality.json").read_text())
    s = json.loads((REPORTS / "statistics.json").read_text())
    original = pd.read_excel(WORKBOOK, engine="openpyxl")
    source_rows = (np.flatnonzero(~original.duplicated()) + 2).tolist()
    parsed = d.date_parsed.notna()
    year_conflicts = parsed & d.date_parsed.dt.year.ne(d.declared_year)
    with closing(connect()) as con:
        modeled = pd.read_sql_query("SELECT * FROM records ORDER BY source_row", con)
        links = pd.read_sql_query("SELECT * FROM participants", con)
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        fk = con.execute("PRAGMA foreign_key_check").fetchall()
    declared = pd.read_csv(TABLES / "declared_years.csv")
    dateyears = pd.read_csv(TABLES / "date_years.csv")
    months = pd.read_csv(TABLES / "months.csv")
    time = pd.read_csv(TABLES / "time_of_day.csv")
    severity = pd.read_csv(TABLES / "severity.csv")
    sensitivity = pd.read_csv(TABLES / "duplicate_sensitivity.csv")
    effect = night_day_effect(d)
    checks = {
        "source_hashes_preserved": verify_raw(),
        "original_shape_matches_audit": original.shape
        == (q["original_rows"], q["original_columns"]),
        "only_exact_duplicate_rows_removed": source_rows == d.source_row.tolist(),
        "cleaned_count_reconciles": len(d)
        == q["cleaned_rows"]
        == q["original_rows"] - q["exact_duplicate_rows_removed"],
        "internal_row_key_unique": d.source_row.is_unique
        and d.source_row.notna().all(),
        "sql_integrity_and_foreign_keys": integrity == "ok" and not fk,
        "sql_cleaned_rows_agree": modeled.source_row.tolist() == d.source_row.tolist(),
        "sql_fatality_values_preserved": modeled.fatalities.sum()
        == d.fatalities.sum()
        == s["summed_fatality_values"],
        "sql_injury_values_preserved": modeled.injuries.sum()
        == d.injuries.sum()
        == s["summed_injury_values"],
        "date_conflict_audit_recomputed": int(year_conflicts.sum())
        == q["date_year_conflicts"]
        and int(parsed.sum()) == q["parseable_dates"],
        "declared_year_table_reconciles": declared.records.sum() == len(d)
        and declared.summed_fatality_values.sum() == d.fatalities.sum(),
        "parsed_year_table_reconciles": dateyears.records.sum() == parsed.sum(),
        "month_tables_reconcile": months.loc[
            months.basis.eq("Month column"), "records"
        ].sum()
        == len(d)
        and months.loc[months.basis.eq("Parsed Date"), "records"].sum() == parsed.sum(),
        "time_table_reconciles": time.records.sum() == d.hour.notna().sum(),
        "severity_table_reconciles": severity.records.sum() == len(d)
        and severity.fatal_records.sum() == d.fatal_record.sum(),
        "participant_links_cover_records_without_duplicate_pairs": links.source_row.nunique()
        == len(d)
        and not links.duplicated(["source_row", "participant_type"]).any(),
        "descriptor_sensitivity_counts_match": int(sensitivity.iloc[2].records)
        == d.descriptor_group.nunique()
        and int(sensitivity.iloc[1].records) == d.source_id.nunique(),
        "statistical_effect_recomputed": all(
            np.isclose(s["night_day_effect"][k], v)
            for k, v in effect.items()
            if k != "field"
        ),
        "conditional_interval_finite_and_bounded": -1
        <= s["conditional_bootstrap"]["lower"]
        <= s["conditional_bootstrap"]["upper"]
        <= 1,
        "substantive_limitations_retained": q["strict_temporal_cohort_rows"]
        == int((parsed & ~year_conflicts & ~d.date_ambiguous).sum())
        and s["population_safety_confidence_intervals_withheld"],
    }
    from PIL import Image

    images = sorted(FIGURES.glob("*.png"))
    for path in images:
        with Image.open(path) as picture:
            picture.verify()
    checks["ten_valid_figures"] = len(images) == 10
    import nbformat

    notebooks = sorted((ROOT / "notebooks").glob("*.ipynb"))
    executed = True
    for path in notebooks:
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        executed &= all(
            c.execution_count is not None
            and not any(o.output_type == "error" for o in c.outputs)
            for c in notebook.cells
            if c.cell_type == "code"
        )
    checks["notebook_sequence_executed_without_errors"] = (
        tuple(path.name for path in notebooks) == NOTEBOOK_NAMES and executed
    )
    reports = [
        "data_quality_report.md",
        "analytical_report.md",
        "environment.json",
        "source_manifest.json",
    ]
    checks["reports_present"] = all((REPORTS / name).is_file() for name in reports)
    result = {
        "checks": {k: bool(v) for k, v in checks.items()},
        "passed": bool(all(checks.values())),
        "meaning": "Implementation fidelity only; source suitability is assessed separately in data_quality.json",
        "source_quality_status": q["quality_status"],
    }
    write_json(REPORTS / "final_validation.json", result)
    if not result["passed"]:
        raise ValueError(f"Validation failed: {result}")
    return result
