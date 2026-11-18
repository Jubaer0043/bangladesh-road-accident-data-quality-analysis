# Methodology and limitations

## Analytical unit and suitability

The primary unit is a published workbook row after exact-row deduplication, not a verified accident. Internal `source_row` references the original Excel row, starting at 2. Serial number and ID are retained as unverified identifiers. Without row-level institutional attribution, overlapping source coverage and reporting changes cannot be reconciled.

The exact requested artifact passes file-integrity checks but fails substantive chronology, identity, and measurement checks. Outputs describe that artifact; code validation is not a source-quality endorsement.

## Cleaning rules

| Issue | Policy |
| --- | --- |
| Raw inputs | Preserve ZIP and workbook bytes; verify SHA-256 before/after stages |
| Schema | Inspect first; require the observed one-sheet, 31-column contract on reproduction |
| Exact original-row duplicates | Keep first; report count and preserve original source-row references |
| Repeated ID/serial | Flag; do not assume unique incidents |
| Candidate descriptor duplicates | Group normalized Date, Time, Location, Narrative, Vehicle Info; retain records in primary analysis |
| Missing tokens | Normalize blank/unknown/not known/not available/n/a/na/none/null/hyphen in derived text; preserve `Others` |
| Date | Respect stored Excel dates; explicitly parse slash strings day-first or ISO dates; invalid derived dates remain missing |
| Ambiguous slash dates | Flag; do not claim original day/month intent; none observed in the pinned artifact |
| Year/Month disagreement | Preserve both bases and flags; do not repair one with the other |
| Time | Explicit 24-hour or AM/PM formats; normalize dotted minute separators; invalid remains missing |
| Coordinates | Use N/E markers despite reversed source header; invalid remains missing; no guessed geocoding |
| Counts/identifiers | Require finite nonnegative integers; invalid values stop execution |
| Spelling | Trim whitespace; normalize documented Two-lane, Vehicle owner, and Bicyclist variants only |
| Parallel weather/light fields | Retain separately; do not select a supposedly correct field without evidence |
| Personal-detail text | Exclude narratives and Death/Injury Info from analytical exports and output; narrative used locally for matching hashes |
| Extreme values and modal templates | Retain and audit; no arbitrary trimming or assumed error mechanism |

No time, date, coordinate, casualty, source membership, or incident identity is imputed.

## Metrics and coverage

`records` counts workbook rows. `fatal_record=1` means numeric Death Count > 0; `fatal_record_share` is its mean among selected records. These are not person-level fatality probability or exposure-adjusted accident risk. Summed casualty fields may double-count events and cannot establish a national toll.

Declared-year/month and parsed-date-year/month summaries use separate bases. The strict temporal cohort requires a parseable Date agreeing with Year and no slash ambiguity. It is empty in this release. No national growth, comparable annual trend, or seasonal effect is estimated.

Time bands are 00–05, 06–11, 12–17, and 18–23 from Time, independent of the two light fields. Participant mentions use transparent regex patterns from Vehicle Info; several types can occur per record. Pedestrians are included as participants, not vehicles. Counts overlap and cannot be added or interpreted as vehicle exposure.

Coordinates are plotted as published using shared marker/color scales. A sensitivity panel excludes the modal coordinate pair to inspect the remainder. The broad screening box 20–27°N, 88–93°E is not an authoritative country boundary. No district/division or road-network mapping is invented, and the scatter is not a validated hotspot map.

## Duplicate and source-overlap analysis

Primary cleaning drops only exact original rows. Descriptor hashes define matching candidates, not ground-truth accidents. Repeated templates, separate events, and processing errors cannot be distinguished without additional source records. Different declared years and fatality values may occur within a group.

Alternative scenarios keep the first row per source ID, first row per descriptor group, or last row per descriptor group. They are what-if populations, not accepted deduplication. Metrics include selected row count, fatal-record share, casualty-value sums, and Night−Day differences. Some rules reverse the direction of the recorded association.

Within-group minimum/maximum fatal-record indicators give conditional identification bounds **if** each descriptor group represented one incident. They do not establish that assumption, count unique accidents, or provide confidence limits.

## Statistical analysis

Cramér's V describes categorical recorded fields versus the fatal-record indicator. SciPy provides Pearson chi-square discrepancy, degrees of freedom, and expected cells. P-values are withheld because verified independent incident units and measurement validity are unestablished. Sparse road groups also have expected cells below five, making ordinary asymptotic assumptions questionable. Small descriptive V values do not show that a real-world safety factor has no effect.

Spearman rho describes recorded fatality/injury values. Its p-value is withheld for the same reasons; no causal or validated crash-severity relationship is inferred.

The Night−Day difference uses `Lighting`; `Light Condition` is analyzed separately. A percentile bootstrap samples candidate descriptor groups with replacement, retaining every row within each sampled group, for 2,000 repetitions using NumPy RNG seed 42. The 95% interval is conditional on treating these computational groups as exchangeable. Their independence, identity, and accurate measurements are unverified. It is therefore a **model reference interval**, not a validated confidence interval for real incidents or population risk. It quantifies only conditional resampling variability and cannot quantify source error, hidden duplication, selection, or confounding. It is not used for safety recommendations.

All comparisons are exploratory. No population-risk confidence intervals, multiple-comparison significance rankings, causal identification, or machine learning are provided. Exact quality rates in this finite audited file need no sampling interval; precision cannot repair systematic contradictions.

## What is needed for substantive safety analysis

Risk requires a valid numerator and compatible exposure denominator, such as vehicle-kilometers or person exposure in a defined period and location. Neither is established here. No enforcement priority, transport expenditure, or dangerous road-user/place/weather ranking is inferred.

Request raw institutional extracts, source identifiers, field definitions, transformation/imputation logs, and duplicate adjudication records. Validate coordinates and administrative boundaries, establish coverage changes, and obtain exposure data. A corrected release must retain separate versioned provenance and pass the audit before incident-level inference.
