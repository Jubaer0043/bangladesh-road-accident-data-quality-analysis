"""Readable, deterministic notebook source. Regeneration resets executed outputs."""

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]


def write(name, cells):
    notebook = nbf.v4.new_notebook()
    notebook.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata.language_info = {"name": "python"}
    for i, (kind, source) in enumerate(cells):
        cell = (nbf.v4.new_markdown_cell if kind == "md" else nbf.v4.new_code_cell)(
            source.strip()
        )
        cell.id = f"cell-{i:02d}"
        notebook.cells.append(cell)
    nbf.validate(notebook)
    nbf.write(notebook, ROOT / "notebooks" / name)


write(
    "00_dataset_and_source_assessment.ipynb",
    [
        (
            "md",
            """# 00 · Dataset and source assessment

Can this release support a national road-safety analysis? Begin with what was actually deposited and which checks require the original institutional records. Run the [reproduction steps](../README.md#source-and-reproduction) to execute the notebook.

[Notebook guide](../README.md#notebook-guide) · [Next](01_source_quality_and_cleaning.ipynb)
""",
        ),
        (
            "code",
            """import json
from pathlib import Path

import pandas as pd
from bd_safety.acquisition import verify_raw
from IPython.display import display

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
assert (ROOT / "src/bd_safety").is_dir(), (
    "Open from the project root or notebooks directory."
)
REPORTS = ROOT / "reports"
TABLES = REPORTS / "tables"
""",
        ),
        (
            "md",
            """## What does the release contain?

Compare the depositor’s description with the workbook inventory. Verify source bytes against the acquisition manifest. The workbook is the analysis input, and its rows are published records.
""",
        ),
        (
            "code",
            """manifest = json.loads((REPORTS / "source_manifest.json").read_text())
quality = json.loads((REPORTS / "data_quality.json").read_text())
verify_raw()
display(
    pd.Series(
        {
            "release": manifest["doi"],
            "workbook member": manifest["archive_member"],
            "publisher-row count": manifest["publisher_claimed_records"],
            "observed rows": quality["original_rows"],
            "observed columns": quality["original_columns"],
        }
    )
)
""",
        ),
        (
            "md",
            """The archive contains a single modified workbook with 47,680 rows and 31 columns. The deposited row count differs from the publisher’s description of 49,566.

## Can the named sources be reconciled?

Review the provenance ledger. Periods and organizations in the ledger come from the publisher’s description. Investigate whether workbook fields can identify which organization produced each row.
""",
        ),
        (
            "code",
            """coverage = pd.read_csv(TABLES / "source_coverage.csv")
display(
    coverage[["claimed_source", "claimed_years", "row_level_attribution_available"]]
)
assert not coverage["row_level_attribution_available"].any()
""",
        ),
        (
            "md",
            """Institutional attribution is unavailable at row level. The publisher’s coverage periods cannot resolve overlap, source-specific reporting or completeness. The next notebook checks whether dates and record identifiers can establish a usable analytical cohort independently.
""",
        ),
        (
            "md",
            """[Notebook guide](../README.md#notebook-guide) · [Next](01_source_quality_and_cleaning.ipynb)
""",
        ),
    ],
)

write(
    "01_source_quality_and_cleaning.ipynb",
    [
        (
            "md",
            """# 01 · Missingness, duplicate patterns, and preparation

Test whether the workbook can support a consistent chronology and a unique incident grain. Work on in-memory views of the workbook and compare key transformations against the approved export. Only aggregate outputs are shown.

[Previous](00_dataset_and_source_assessment.ipynb) · [Notebook guide](../README.md#notebook-guide) · [Next](02_eda_statistics_and_visualization.ipynb)
""",
        ),
        (
            "code",
            """import json
from pathlib import Path

import numpy as np
import pandas as pd
from bd_safety.cleaning import ambiguous_date, parse_date
from IPython.display import Image, display

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
assert (ROOT / "src/bd_safety").is_dir(), (
    "Open from the project root or notebooks directory."
)
REPORTS = ROOT / "reports"
TABLES = REPORTS / "tables"


WORKBOOK = ROOT / "data/raw/Modified_Accident_Dataset final.xlsx"
quality = json.loads((REPORTS / "data_quality.json").read_text())
""",
        ),
        (
            "md",
            """## How much is missing, and what is duplicated?

Read the workbook once. Count actual missing cells and exact duplicates across all columns before any normalization. Preserve Excel row numbers as provenance keys. Report concentrated values using the inventory without displaying their raw text.
""",
        ),
        (
            "code",
            """raw = pd.read_excel(WORKBOOK, engine="openpyxl")
duplicate = raw.duplicated()
retained = raw.loc[~duplicate, ["Date ", "Year", "ID", "Accident Serial No"]]
source_rows = np.flatnonzero(~duplicate.to_numpy()) + 2
assert int(duplicate.sum()) == quality["exact_duplicate_rows_removed"]
assert int(raw.isna().sum().sum()) == quality["raw_null_cells"]
inventory = pd.read_csv(TABLES / "column_inventory.csv")
display(
    pd.Series(
        {
            "raw rows": len(raw),
            "raw null cells": int(raw.isna().sum().sum()),
            "exact duplicates": int(duplicate.sum()),
            "retained rows": len(retained),
        }
    )
)
display(
    inventory.nlargest(6, "largest_value_share")[
        [
            "original_column",
            "raw_nulls",
            "missing_after_token_normalization",
            "distinct_nonmissing",
            "largest_value_share",
        ]
    ]
)
""",
        ),
        (
            "md",
            """Four exact duplicates are removed from analytical preparation. Zero raw null cells can coexist with unusable dates and highly repeated field values.

## Do parsed dates agree with declared years?

Use the established date parser for Excel-native dates and day-first slash strings. Keep the declared year beside the parsed year and flag disagreements. Invalid or ambiguous dates are excluded from a strict chronology cohort.
""",
        ),
        (
            "code",
            """parsed = pd.to_datetime(retained["Date "].map(parse_date))
ambiguous = retained["Date "].map(ambiguous_date)
conflict = (parsed.notna() & parsed.dt.year.ne(retained["Year"])).fillna(False)
consistent = parsed.notna() & ~conflict & ~ambiguous
chronology = {
    "parseable_dates": int(parsed.notna().sum()),
    "invalid_dates": int(parsed.isna().sum()),
    "date_year_conflicts": int(conflict.sum()),
    "strict_temporal_cohort_rows": int(consistent.sum()),
}
assert all(value == quality[key] for key, value in chronology.items())
display(pd.Series(chronology))
display(Image(filename=str(REPORTS / "figures/01_year_coverage.png"), width=900))
""",
        ),
        (
            "md",
            """All 47,533 parseable dates disagree with the declared year and 143 dates fail parsing. The declared years span 2007–2021 while parsed dates fall in 2022–2024. The strict cohort is empty.

## Can an identifier rescue incident identity?

Check how many distinct IDs and serial numbers remain. Compare group summaries based on normalized Date, Time, Location, Narrative and Vehicle Info. These descriptors are used only as matching candidates. Reconcile the approved analytical export’s row positions and date flags with the direct calculation.
""",
        ),
        (
            "code",
            """prepared = pd.read_csv(
    ROOT / "data/processed/cleaned_records.csv",
    usecols=["source_row", "date_year_conflict", "latitude"],
)
np.testing.assert_array_equal(prepared["source_row"], source_rows)
np.testing.assert_array_equal(prepared["date_year_conflict"], conflict)
groups = pd.read_csv(TABLES / "descriptor_groups.csv")
identity = pd.Series(
    {
        "distinct source IDs": retained["ID"].nunique(),
        "distinct serial numbers": retained["Accident Serial No"].nunique(),
        "candidate groups": len(groups),
        "groups with conflicting fatality values": groups["fatality_values"]
        .gt(1)
        .sum(),
        "records without parsed latitude": prepared["latitude"].isna().sum(),
    }
)
assert (
    identity["groups with conflicting fatality values"]
    == quality["groups_with_conflicting_fatality_values"]
)
display(identity)
display(Image(filename=str(REPORTS / "figures/09_quality_flags.png"), width=900))
""",
        ),
        (
            "md",
            """There are 17,497 distinct source IDs among 47,676 retained rows. In 1,929 of 2,321 candidate descriptor groups, fatality values disagree. Quality flags can overlap on a row, so adding them would overcount affected records. Carry the verified row grain into descriptive exploration.
""",
        ),
        (
            "md",
            """[Previous](00_dataset_and_source_assessment.ipynb) · [Notebook guide](../README.md#notebook-guide) · [Next](02_eda_statistics_and_visualization.ipynb)
""",
        ),
    ],
)

write(
    "02_eda_statistics_and_visualization.ipynb",
    [
        (
            "md",
            """# 02 · Exploratory patterns in published records

Explore what the workbook encodes after exact duplicate removal. Each chart describes the published rows. Compare field definitions and coverage before interpreting their apparent patterns.

[Previous](01_source_quality_and_cleaning.ipynb) · [Notebook guide](../README.md#notebook-guide) · [Next](03_statistics_and_identity_sensitivity.ipynb)
""",
        ),
        (
            "code",
            """import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd
from IPython.display import Image, display

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
assert (ROOT / "src/bd_safety").is_dir(), (
    "Open from the project root or notebooks directory."
)
REPORTS = ROOT / "reports"
TABLES = REPORTS / "tables"


DB_URI = (ROOT / "data/processed/accident_records.sqlite3").as_uri() + "?mode=ro"
""",
        ),
        (
            "md",
            """## What do the month and hour fields measure?

Run the verified month query, which keeps each month basis separate. Inspect those distributions alongside hours extracted from the original time field.
""",
        ),
        (
            "code",
            """month_sql = (ROOT / "sql/04_months.sql").read_text()
print(month_sql)
with closing(sqlite3.connect(DB_URI, uri=True)) as connection:
    months = pd.read_sql_query(month_sql, connection)
display(months.groupby("basis")["records"].sum())
display(Image(filename=str(REPORTS / "figures/02_month_fields.png"), width=900))
""",
        ),
        (
            "md",
            """The two month fields place records in different months and have different denominators. Chronology conflicts prevent seasonal inference.

## How concentrated is the recorded hour?
""",
        ),
        (
            "code",
            """display(Image(filename=str(REPORTS / "figures/03_recorded_hour.png"), width=900))
""",
        ),
        (
            "md",
            """One recorded time dominates the workbook. Repeated descriptors and unknown traffic exposure limit interpretation of that peak.

## Do severity labels agree with numeric fatality counts?
""",
        ),
        (
            "code",
            """display(
    Image(
        filename=str(REPORTS / "figures/04_severity_fatality_consistency.png"),
        width=900,
    )
)
""",
        ),
        (
            "md",
            """Death labels appear even where the numeric fatality value is zero. Conversely, positive values occur under other labels. Keep the original severity label and a separately defined positive-count indicator.

## What does a participant count represent?

Join the participant bridge by source_row. One row can mention multiple categories. COUNT(DISTINCT ...) keeps the numerator at source-row grain within each category.
""",
        ),
        (
            "code",
            """participant_sql = (ROOT / "sql/07_participants.sql").read_text()
print(participant_sql)
with closing(sqlite3.connect(DB_URI, uri=True)) as connection:
    participants = pd.read_sql_query(participant_sql, connection)
display(participants.head(5))
display(Image(filename=str(REPORTS / "figures/05_participant_mentions.png"), width=900))
""",
        ),
        (
            "md",
            """Motorcycle and truck mentions dominate. Their categories overlap, and neither the row counts nor the within-category shares measure road-user risk.

## Do parallel weather and light fields tell the same story?
""",
        ),
        (
            "code",
            """display(
    Image(
        filename=str(REPORTS / "figures/06_parallel_field_disagreements.png"), width=900
    )
)
""",
        ),
        (
            "md",
            """Weather and light fields frequently disagree. Collapsing them to a single trusted measure would require definitions or source records.

## How concentrated are road categories and coordinates?
""",
        ),
        (
            "code",
            """display(Image(filename=str(REPORTS / "figures/07_road_fields.png"), width=900))
""",
        ),
        (
            "md",
            """National Road dominates the road-class labels. The field describes the workbook’s composition, with broad coverage and reporting practices still unknown.

## Does one coordinate drive the spatial picture?
""",
        ),
        (
            "code",
            """display(Image(filename=str(REPORTS / "figures/08_coordinate_coverage.png"), width=900))
""",
        ),
        (
            "md",
            """One coordinate pair appears on 45,506 rows. The second view exposes the other observed pairs on a shared color scale. Neither view establishes validated hotspots. Next, test how uncertain identity changes even a narrow comparison of recorded fields.
""",
        ),
        (
            "md",
            """[Previous](01_source_quality_and_cleaning.ipynb) · [Notebook guide](../README.md#notebook-guide) · [Next](03_statistics_and_identity_sensitivity.ipynb)
""",
        ),
    ],
)

write(
    "03_statistics_and_identity_sensitivity.ipynb",
    [
        (
            "md",
            """# 03 · Descriptive statistics and identity sensitivity

Measure associations between recorded fields and evaluate how changing the row selection changes a lighting comparison. Values refer to workbook records with positive numeric fatality counts.

[Previous](02_eda_statistics_and_visualization.ipynb) · [Notebook guide](../README.md#notebook-guide) · [Next](04_data_suitability.ipynb)
""",
        ),
        (
            "code",
            """import json
from pathlib import Path

import numpy as np
import pandas as pd
from bd_safety.statistics import conditional_cluster_interval, night_day_effect
from IPython.display import Image, display
from scipy.stats import chi2_contingency, spearmanr

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
assert (ROOT / "src/bd_safety").is_dir(), (
    "Open from the project root or notebooks directory."
)
REPORTS = ROOT / "reports"
TABLES = REPORTS / "tables"


fields = [
    "fatal_record",
    "fatalities",
    "injuries",
    "lighting",
    "source_id",
    "descriptor_group",
]
records = pd.read_csv(ROOT / "data/processed/cleaned_records.csv", usecols=fields)
stats = json.loads((REPORTS / "statistics.json").read_text())
""",
        ),
        (
            "md",
            """## How strongly do the recorded fields vary together?

Build a contingency table to calculate Cramér’s V for lighting and the positive fatality-count flag. Use Spearman’s rank correlation for the two recorded casualty counts. Inspect the statistics without making independent-event inference.
""",
        ),
        (
            "code",
            """counts = pd.crosstab(records["lighting"], records["fatal_record"])
chi_squared, _, _, expected = chi2_contingency(counts, correction=False)
cramers_v = np.sqrt(chi_squared / (counts.to_numpy().sum() * (min(counts.shape) - 1)))
rho = spearmanr(records["fatalities"], records["injuries"]).statistic
lighting = next(
    row for row in stats["descriptive_effects"] if row["field"] == "lighting"
)
assert np.isclose(cramers_v, lighting["cramers_v"])
assert np.isclose(rho, stats["fatality_injury_spearman_rho"])
display(counts)
display(
    pd.Series(
        {
            "lighting Cramér’s V": cramers_v,
            "casualty-count Spearman rho": rho,
            "minimum expected lighting cell": expected.min(),
        }
    )
)
""",
        ),
        (
            "md",
            """The associations are small for these recorded fields. Uncertain incident identity and conflicting measurements prevent treating workbook rows as independent events.

## How does the recorded Night–Day comparison vary under resampling?

Calculate the fraction of positive-count rows within each label. Resample descriptor groups as computational clusters with the original fixed seed and 2,000 replicates.
""",
        ),
        (
            "code",
            """lighting_rows = records.loc[records["lighting"].isin(["Day", "Night"])]
summary = lighting_rows.groupby("lighting")["fatal_record"].agg(
    records="size", positive_share="mean"
)
gap = summary.at["Night", "positive_share"] - summary.at["Day", "positive_share"]
assert np.isclose(gap, stats["night_day_effect"]["difference_night_minus_day"])
interval = conditional_cluster_interval(records)
np.testing.assert_allclose(
    [interval["lower"], interval["upper"]],
    [stats["conditional_bootstrap"]["lower"], stats["conditional_bootstrap"]["upper"]],
)
display(summary)
display(
    pd.Series(
        {
            "gap_pp": gap * 100,
            "lower_pp": interval["lower"] * 100,
            "upper_pp": interval["upper"] * 100,
        }
    ).round(2)
)
""",
        ),
        (
            "md",
            """The Night-minus-Day difference is −0.70 percentage points and the conditional reference interval runs from −1.78 to +0.29. It describes resampling under the candidate grouping. Verified incidents, exposure and a defensible sampling frame would be needed for population inference.

## Does the direction survive a different row selection?

Apply the audited first- and last-record selection rules in source order. Compare all four gaps to the original sensitivity export.
""",
        ),
        (
            "code",
            """alternatives = [
    records,
    records.drop_duplicates("source_id"),
    records.drop_duplicates("descriptor_group"),
    records.drop_duplicates("descriptor_group", keep="last"),
]
differences = [
    night_day_effect(frame)["difference_night_minus_day"] for frame in alternatives
]
saved = pd.read_csv(TABLES / "duplicate_sensitivity.csv")
np.testing.assert_allclose(differences, saved["difference_night_minus_day"])
display(
    saved[["scenario", "records"]].assign(
        night_minus_day_pp=np.round(np.array(differences) * 100, 2)
    )
)
display(
    Image(filename=str(REPORTS / "figures/10_duplicate_sensitivity.png"), width=900)
)
""",
        ),
        (
            "md",
            """Selecting the first versus last row per candidate descriptor group reverses the gap from −1.80 to +1.35 points. This instability matters more for the suitability decision than the precision of any one conditional interval.
""",
        ),
        (
            "md",
            """[Previous](02_eda_statistics_and_visualization.ipynb) · [Notebook guide](../README.md#notebook-guide) · [Next](04_data_suitability.ipynb)
""",
        ),
    ],
)

write(
    "04_data_suitability.ipynb",
    [
        (
            "md",
            """# 04 · Data suitability and conclusions

Decide which questions can be answered from this release and which require a better source. The earlier notebooks established the record grain, reconciled the original audit and tested sensitivity.

[Previous](03_statistics_and_identity_sensitivity.ipynb) · [Notebook guide](../README.md#notebook-guide)
""",
        ),
        (
            "code",
            """import json
from pathlib import Path

import pandas as pd
from IPython.display import display

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
assert (ROOT / "src/bd_safety").is_dir(), (
    "Open from the project root or notebooks directory."
)
REPORTS = ROOT / "reports"
TABLES = REPORTS / "tables"
""",
        ),
        (
            "md",
            """## What evidence determines suitability?

Collect the audited checks that govern chronology, identity and institutional attribution. Pair each issue with the evidence needed to resolve it.
""",
        ),
        (
            "code",
            """quality = json.loads((REPORTS / "data_quality.json").read_text())
checks = pd.DataFrame(
    [
        ("Chronology", quality["date_year_conflicts"], "Reconciled event dates"),
        (
            "Strict temporal cohort",
            quality["strict_temporal_cohort_rows"],
            "Validated date-year pairs",
        ),
        (
            "Conflicting fatality groups",
            quality["groups_with_conflicting_fatality_values"],
            "Source-level casualty reconciliation",
        ),
        (
            "Institutional attribution present",
            quality["source_column_present"],
            "Agency identifier and documented merge",
        ),
    ],
    columns=["check", "observed", "evidence needed"],
)
display(checks)
""",
        ),
        (
            "md",
            """## Decision

Use the release for reproducible record-quality auditing and conditional exploratory comparisons. The empty temporal cohort rules out a reliable national time series. Ambiguous event identity and missing traffic exposure rule out accident-risk rankings or targeting based on the observed counts.

Obtain original institutional registers and a field codebook, document the merge and overlap rules, adjudicate matching candidates, and validate traffic-exposure denominators for each proposed comparison. See the [source-quality report](../reports/data_quality_report.md) and [analytical report](../reports/analytical_report.md) for the original evidence.
""",
        ),
        (
            "md",
            """[Previous](03_statistics_and_identity_sensitivity.ipynb) · [Notebook guide](../README.md#notebook-guide)
""",
        ),
    ],
)
