import importlib.metadata
import json
import platform
import sqlite3

import pandas as pd

from .acquisition import verify_raw, write_json
from .config import REPORTS, TABLES


def table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        + ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    )


def render():
    verify_raw()
    q = json.loads((REPORTS / "data_quality.json").read_text())
    s = json.loads((REPORTS / "statistics.json").read_text())
    g = json.loads((REPORTS / "geographic_coverage.json").read_text())
    manifest = json.loads((REPORTS / "source_manifest.json").read_text())
    n = q["cleaned_rows"]
    flags = table(
        ["Audit", "Observed result", "Interpretation"],
        [
            [
                "Original workbook",
                f"{q['original_rows']:,} rows × {q['original_columns']} columns",
                "One sheet; modified research workbook",
            ],
            [
                "Exact duplicates",
                q["exact_duplicate_rows_removed"],
                f"Removed only from cleaned copy; {n:,} rows remain",
            ],
            [
                "Raw null cells",
                q["raw_null_cells"],
                "Non-null does not establish measurement completeness or accuracy",
            ],
            [
                "Unparseable Date",
                f"{q['invalid_dates']:,}",
                "Retained as missing parsed date; original workbook preserved",
            ],
            [
                "Date versus Year conflicts",
                f"{q['date_year_conflicts']:,} / {q['parseable_dates']:,} parseable dates",
                "No defensible unified annual trend",
            ],
            [
                "Date versus Month conflicts",
                f"{q['date_month_conflicts']:,} / {q['parseable_dates']:,}",
                "No defensible seasonality claim",
            ],
            [
                "Invalid coordinate strings",
                q["invalid_coordinates"],
                "No coordinate imputation or swapping without hemisphere evidence",
            ],
            [
                "Weather field lexical disagreement",
                f"{q['weather_disagreements']:,} / {n:,}",
                "Both source fields retained; neither declared correct",
            ],
            [
                "Lighting field disagreement",
                f"{q['light_disagreements']:,} / {n:,}",
                "Time, Light Condition, and Lighting are distinct measurements",
            ],
            [
                "Severity/fatality flag disagreement",
                f"{q['severity_fatality_disagreements']:,} / {n:,}",
                "Death label versus Death Count > 0; definition is an audit assumption",
            ],
        ],
    )
    quality = f"""# Data-quality and source-suitability report

## Outcome

**{q["quality_status"]}**. The software can successfully reproduce a descriptive audit of this published artifact. That success does not validate the underlying incidents or fields.

{flags}

## Provenance and coverage

Source: Mendeley Data v2, DOI `{manifest["doi"]}`, published {manifest["published_date"]}, CC BY 4.0. Original archive SHA-256 matches the checksum supplied by Mendeley's public file inventory. One XLSX file is provided, named `Modified_Accident_Dataset final.xlsx`; no raw institutional extracts, codebook, source mapping, or transformation log is included. No evidence establishes which of the overlapping source records was reconciled.

The landing-page description claims {manifest["publisher_claimed_records"]:,} records across 2007–2024 and several institutional/field sources. The downloaded workbook contains {q["original_rows"]:,} rows, a difference of {manifest["publisher_claimed_records"] - q["original_rows"]:,}. These are publisher claims, not independently verified source histories.

The separate Year field spans {q["declared_year_min"]}–{q["declared_year_max"]}; parsed Date spans {q["parsed_date_min"]}–{q["parsed_date_max"]}. The strict cohort requiring a parseable date agreeing with declared year contains **{q["strict_temporal_cohort_rows"]:,} records**. No nationwide year-on-year or seasonal change is estimated. `source_coverage.csv` distinguishes claimed coverage from what can actually be verified.

## Duplicate and overlap audit

The source has {q["distinct_serial_numbers"]:,} distinct serial numbers and {q["distinct_source_ids"]:,} distinct IDs after exact deduplication. Serial and ID are not globally unique keys: excess repeated rows are {q["repeated_serial_excess_rows"]:,} and {q["repeated_source_id_excess_rows"]:,}, respectively. A stable internal `source_row` references the original Excel row; it is not an accident identifier.

Normalized Date, Time, Location, Accident Narrative, and Vehicle Info define **candidate descriptor groups**, not verified accidents. There are {q["descriptor_groups"]:,} groups and {q["excess_descriptor_rows"]:,} excess rows. Of those groups, {q["groups_with_conflicting_fatality_values"]:,} contain different fatality values and {q["groups_spanning_multiple_declared_years"]:,} span multiple declared years. Repeated templates, genuine repeated events, and flawed merges cannot be distinguished without source evidence. Collapsing on ID or descriptors is therefore a sensitivity scenario, not accepted incident deduplication.

The modal date and modal narrative each occur in {q["dominant_date_rows"]:,} cleaned rows ({q["dominant_date_rows"] / n:.2%}). The modal time occurs in {q["dominant_time_rows"]:,} rows and the modal coordinate in {q["dominant_coordinate_rows"]:,}. These concentrations warrant investigation; they do not by themselves prove fabrication, imputation, or any specific processing error.

## Missingness and field handling

The detailed [column inventory](tables/column_inventory.csv) preserves all original column names and inferred types, raw-null counts, normalized missing-token counts, cardinality, and modal shares. Explicit missing tokens are normalized in copies. `Others` remains a reported category. Invalid dates and coordinates are set missing in derived fields with counts reported. No dates, coordinates, scores, casualties, or source memberships are invented. A low null count does not resolve repeated default-like values or cross-field contradictions.

Free-text personal details and narratives are excluded from cleaned analytical exports and notebook outputs. Narrative content is used only locally to construct matching-group hashes. Source bytes remain untouched.

## Release gate

The pipeline rejects checksum changes, unexpected schemas, invalid count values, corrupted archives, model reconciliation failures, or notebook errors. Known source-quality problems are retained as explicit analytical flags; they do not cause silent repairs. `data_quality.json` states the substantive suitability failure, while `final_validation.json` records whether the implementation faithfully reproduces that audit. Population safety inference must remain withheld until provenance and measurement issues are resolved.
"""
    (REPORTS / "data_quality_report.md").write_text(quality, encoding="utf-8")
    effects = table(
        ["Published field vs fatal-record flag", "Cramér's V", "Minimum expected cell"],
        [
            [e["field"], f"{e['cramers_v']:.4f}", f"{e['min_expected_cell']:.2f}"]
            for e in s["descriptive_effects"]
            if e["estimable"]
        ],
    )
    sensitivity = pd.read_csv(TABLES / "duplicate_sensitivity.csv")
    sensitivity_table = table(
        [
            "Scenario",
            "Rows",
            "Share with Death Count > 0",
            "Sum of Death Count values",
            "Night−Day difference (pp)",
        ],
        [
            [
                r.scenario,
                f"{r.records:,}",
                f"{r.fatal_record_share:.2%}",
                f"{r.summed_fatality_values:,}",
                f"{100 * r.difference_night_minus_day:.2f}",
            ]
            for r in sensitivity.itertuples()
        ],
    )
    effect, ci, bounds = (
        s["night_day_effect"],
        s["conditional_bootstrap"],
        s["descriptor_sensitivity_bounds"],
    )
    report = f"""# Bangladesh Road Accident Data Quality Audit & Exploratory Analysis

## Executive assessment

**This source is not suitable for reliable national trends, accident-risk estimation, or causal safety conclusions.** The defensible portfolio outcome is a reproducible source-quality audit plus clearly bounded exploratory analysis of published records. The original Mendeley version 2 ZIP was downloaded successfully and matches the publisher's checksum; no manual download was required.

There are {q["original_rows"]:,} original rows and {n:,} after removal of {q["exact_duplicate_rows_removed"]} exact duplicate rows. All {q["parseable_dates"]:,} parseable dates conflict with the separate Year field. There is no row-level source attribution to resolve overlapping institutional coverage. Repeated identifiers and descriptor templates make the number of independent accidents unknown. Read the [quality report](data_quality_report.md) before interpreting any chart.

## Questions and analytical boundaries

The intended questions concern temporal patterns, recorded severity, vehicle/participant involvement, road/weather conditions, and geographic concentration. This workbook permits inspection of how those fields are distributed and whether they agree. It does **not** support claims that one road, vehicle, weather condition, hour, or place has a higher probability of accident. There are no traffic volume, distance traveled, population-at-risk, vehicle fleet, or uninjured exposure denominators.

The unit below is an exact-deduplicated workbook record. `fatal_record_share` means the proportion of selected records with numeric Death Count > 0, not a person's probability of dying, road-user fatality risk, or severity of a verified unique accident. Summed casualty values can double-count repeated events and have unresolved consistency issues.

## Source and quality findings

Source authors: Fernaz Nur and Arafat Sahin Afridi. Release: Mendeley Data v2, DOI `{manifest["doi"]}`, CC BY 4.0. The artifact is one modified XLSX workbook with {q["original_columns"]} columns. The archive and workbook hashes are recorded in [source_manifest.json](source_manifest.json).

{flags}

No institution-specific dataset or mapping was included. The source description mentions overlapping ARI, BRTA, DMP, MP Unit, and form-based contributions. The available fields cannot establish that these sources were deduplicated, independently verify their collection procedures, or identify source-specific reporting changes. Absence of ordinary null cells is not proof of complete data.

## Temporal patterns: incompatible source fields

![Competing year fields](figures/01_year_coverage.png)

The declared Year range is {q["declared_year_min"]}–{q["declared_year_max"]}; Date parses to {q["parsed_date_min"]}–{q["parsed_date_max"]}. **No growth rate, annual safety improvement, seasonal effect, or comparable national year series is reported.** The chart compares field distributions to diagnose the source. The strict date/year-consistent cohort is empty.

![Competing month fields](figures/02_month_fields.png)

![Recorded hour](figures/03_recorded_hour.png)

The modal time appears in {q["dominant_time_rows"]:,} records ({q["dominant_time_rows"] / n:.2%}). This is a source concentration requiring validation, not evidence that accident risk peaks at that time. Broad time bands are exported, but hour-level counts cannot adjust for road use or potential template reuse.

## Recorded severity and casualty fields

![Severity versus fatalities](figures/04_severity_fatality_consistency.png)

Numeric fatality values sum to {s["summed_fatality_values"]:,} and injury values to {s["summed_injury_values"]:,} across cleaned rows. **These sums are not a verified death or injury toll.** {s["fatal_record_share"]:.2%} of cleaned records have Death Count > 0. The flag comparing label `Death` with positive numeric Death Count disagrees in {q["severity_fatality_disagreements"]:,} records; the source supplies no codebook to reconcile the two definitions. Severity labels are retained separately and not silently converted to a numeric scale.

## Participant, road, and environmental distributions

![Participants](figures/05_participant_mentions.png)

Participant types are extracted using transparent token patterns from Vehicle Info, including pedestrians as road users. Records can mention several participants; counts overlap. A dominant repeated vehicle description cannot establish real-world vehicle risk. Road-user exposure, fleet sizes, and verified incident attribution are unavailable.

![Parallel weather and light fields](figures/06_parallel_field_disagreements.png)

Weather and light columns are displayed separately because they disagree extensively. Lexical disagreement is a screening flag; category definitions may also differ. No claim is made about which field is correct or that environmental factors have no safety effect.

![Road fields](figures/07_road_fields.png)

Road-field distributions are highly concentrated; counts use logarithmic axes where labeled to retain minority categories. They describe source composition and cannot identify hazardous road types.

## Geographic coverage

![Coordinate coverage](figures/08_coordinate_coverage.png)

There are {g["valid_coordinate_records"]:,} records with parseable coordinates and {g["distinct_coordinate_pairs"]:,} distinct coordinate pairs. Observed latitude is {g["latitude_min"]:.5f}–{g["latitude_max"]:.5f}°N and longitude {g["longitude_min"]:.5f}–{g["longitude_max"]:.5f}°E. The dominant pair is reused in {g["dominant_coordinate_records"]:,} records. This limited numeric extent and street/highway labels do not establish nationwide coverage. No validated district/division codes or boundary join are provided, so no district ranking is invented. The right panel removes the dominant coordinate pair solely to inspect the remaining distribution; it is not a validated cleaned hotspot map.

## Statistical relationships and uncertainty

{effects}

Cramér's V summarizes the strength of association **within the published fields**. Pearson chi-square discrepancies, degrees of freedom, and expected cell counts are retained for audit; inferential p-values are withheld because independent verified incident units and measurement validity have not been established. Sparse road-category expected cells also make usual asymptotic test assumptions questionable. Fatality and injury values have descriptive Spearman rank correlation {s["fatality_injury_spearman_rho"]:.4f}; this says nothing reliable about the true relationship between crash severity and injuries.

Using `Lighting`, the Night-minus-Day difference in fatal-record share is {100 * effect["difference_night_minus_day"]:.2f} percentage points ({effect["night_records"]:,} Night records, {effect["day_records"]:,} Day records). A conditional descriptor-cluster percentile bootstrap gives a 95% **model reference interval** of {100 * ci["lower"]:.2f} to {100 * ci["upper"]:.2f} pp ({ci["repetitions"]:,} resamples; seed {ci["seed"]}; {ci["descriptor_clusters"]:,} groups represented in Day/Night rows). Descriptor groups are only computational clusters. Their independence and incident identity are unverified. **This interval is not a validated accident-level or population-risk confidence interval** and does not quantify source error, duplicated events, or causal effects. It is included to make the conditional resampling mechanics and their limitations inspectable. Safety decisions must not use it.

## Identity and duplicate sensitivity

{sensitivity_table}

![Duplicate sensitivity](figures/10_duplicate_sensitivity.png)

There are {q["descriptor_groups"]:,} normalized descriptor groups, but they are not a count of verified accidents. Of these, {q["groups_with_conflicting_fatality_values"]:,} contain conflicting numeric fatality values. If, only as a what-if assumption, each group were one incident, its possible fatal-record share lies between {bounds["fatal_share_lower"]:.2%} and {bounds["fatal_share_upper"]:.2%} using within-group minima and maxima. These are conditional identification bounds, **not confidence limits**. First/last-row and ID-based alternatives illustrate dependence on unresolved identity choices; none is accepted as the correct deduplication.

![Quality flags](figures/09_quality_flags.png)

## Recommended next steps

1. Request the original institutional extracts, collection definitions, field codebook, source identifiers, merge keys, imputation rules, and transformation script from the depositors. Resolve the completely inconsistent chronologies before any temporal comparison.
2. Establish an incident identifier and reconcile overlapping source coverage. Manually review candidate duplicates and conflicting casualty/condition values against original records; preserve a decision log.
3. Validate coordinates and administrative codes against an authoritative boundary source. Obtain appropriate traffic/exposure denominators before estimating road, vehicle, weather, or geographic risk.
4. Re-run this audit on a corrected, separately versioned release. Only then consider incident-level severity comparisons or operational safety recommendations.

No particular road-user group, location, or condition is recommended as a safety target from this artifact. No causal claims, machine-learning predictions, national fatality estimates, or fabricated incident corrections are provided.

## Reproduction

See [README](../README.md), [methodology](../docs/methodology.md), [source notes](../docs/data_sources.md), executable [SQL](../sql/), and two [notebooks](../notebooks/). Local `data/processed/cleaned_records.csv` and `accident_records.sqlite3` are reproducible derivatives, excluded from Git with original data. Aggregate tables, audit JSON, report, and figures are versionable evidence. [final_validation.json](final_validation.json) validates implementation fidelity; [data_quality.json](data_quality.json) preserves the distinct substantive quality failure.
"""
    (REPORTS / "analytical_report.md").write_text(report, encoding="utf-8")
    packages = [
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "scipy",
        "openpyxl",
        "nbformat",
        "nbclient",
        "ipykernel",
        "jupyterlab",
    ]
    write_json(
        REPORTS / "environment.json",
        {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "sqlite": sqlite3.sqlite_version,
            "packages": {p: importlib.metadata.version(p) for p in packages},
        },
    )
    coverage = []
    for source, years in manifest["publisher_claimed_sources"].items():
        coverage.append(
            {
                "claimed_source": source,
                "claimed_years": years,
                "claim_basis": "Publisher landing-page description",
                "row_level_attribution_available": False,
                "overlap_resolved": False,
            }
        )
    pd.DataFrame(coverage).to_csv(TABLES / "source_coverage.csv", index=False)
    return {
        "reports": ["data_quality_report.md", "analytical_report.md"],
        "substantive_source_status": q["quality_status"],
    }
