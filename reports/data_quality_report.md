# Data-quality and source-suitability report

## Outcome

**NOT FIT for national trends, incident-risk estimation, or causal safety conclusions**. The software can successfully reproduce a descriptive audit of this published artifact. That success does not validate the underlying incidents or fields.

| Audit | Observed result | Interpretation |
| --- | --- | --- |
| Original workbook | 47,680 rows × 31 columns | One sheet; modified research workbook |
| Exact duplicates | 4 | Removed only from cleaned copy; 47,676 rows remain |
| Raw null cells | 0 | Non-null does not establish measurement completeness or accuracy |
| Unparseable Date | 143 | Retained as missing parsed date; original workbook preserved |
| Date versus Year conflicts | 47,533 / 47,533 parseable dates | No defensible unified annual trend |
| Date versus Month conflicts | 43,812 / 47,533 | No defensible seasonality claim |
| Invalid coordinate strings | 19 | No coordinate imputation or swapping without hemisphere evidence |
| Weather field lexical disagreement | 36,995 / 47,676 | Both source fields retained; neither declared correct |
| Lighting field disagreement | 32,639 / 47,676 | Time, Light Condition, and Lighting are distinct measurements |
| Severity/fatality flag disagreement | 27,929 / 47,676 | Death label versus Death Count > 0; definition is an audit assumption |

## Provenance and coverage

Source: Mendeley Data v2, DOI `10.17632/p2kgkb5cd2.2`, published 2025-10-17, CC BY 4.0. Original archive SHA-256 matches the checksum supplied by Mendeley's public file inventory. One XLSX file is provided, named `Modified_Accident_Dataset final.xlsx`; no raw institutional extracts, codebook, source mapping, or transformation log is included. No evidence establishes which of the overlapping source records was reconciled.

The landing-page description claims 49,566 records across 2007–2024 and several institutional/field sources. The downloaded workbook contains 47,680 rows, a difference of 1,886. These are publisher claims, not independently verified source histories.

The separate Year field spans 2007–2021; parsed Date spans 2022-01-02–2024-12-03. The strict cohort requiring a parseable date agreeing with declared year contains **0 records**. No nationwide year-on-year or seasonal change is estimated. `source_coverage.csv` distinguishes claimed coverage from what can actually be verified.

## Duplicate and overlap audit

The source has 47,305 distinct serial numbers and 17,497 distinct IDs after exact deduplication. Serial and ID are not globally unique keys: excess repeated rows are 371 and 30,179, respectively. A stable internal `source_row` references the original Excel row; it is not an accident identifier.

Normalized Date, Time, Location, Accident Narrative, and Vehicle Info define **candidate descriptor groups**, not verified accidents. There are 2,321 groups and 45,355 excess rows. Of those groups, 1,929 contain different fatality values and 1,837 span multiple declared years. Repeated templates, genuine repeated events, and flawed merges cannot be distinguished without source evidence. Collapsing on ID or descriptors is therefore a sensitivity scenario, not accepted incident deduplication.

The modal date and modal narrative each occur in 45,501 cleaned rows (95.44%). The modal time occurs in 45,550 rows and the modal coordinate in 45,506. These concentrations warrant investigation; they do not by themselves prove fabrication, imputation, or any specific processing error.

## Missingness and field handling

The detailed [column inventory](tables/column_inventory.csv) preserves all original column names and inferred types, raw-null counts, normalized missing-token counts, cardinality, and modal shares. Explicit missing tokens are normalized in copies. `Others` remains a reported category. Invalid dates and coordinates are set missing in derived fields with counts reported. No dates, coordinates, scores, casualties, or source memberships are invented. A low null count does not resolve repeated default-like values or cross-field contradictions.

Free-text personal details and narratives are excluded from cleaned analytical exports and notebook outputs. Narrative content is used only locally to construct matching-group hashes. Source bytes remain untouched.

## Release gate

The pipeline rejects checksum changes, unexpected schemas, invalid count values, corrupted archives, model reconciliation failures, or notebook errors. Known source-quality problems are retained as explicit analytical flags; they do not cause silent repairs. `data_quality.json` states the substantive suitability failure, while `final_validation.json` records whether the implementation faithfully reproduces that audit. Population safety inference must remain withheld until provenance and measurement issues are resolved.
