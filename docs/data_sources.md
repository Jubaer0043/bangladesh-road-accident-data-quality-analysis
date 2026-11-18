# Exact source and coverage evidence

Original release: [Mendeley Data v2](https://data.mendeley.com/datasets/p2kgkb5cd2/2), DOI **10.17632/p2kgkb5cd2.2**, published **17 October 2025**. Depositors: **Fernaz Nur and Arafat Sahin Afridi**. License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

| Artifact | Observed identity |
| --- | --- |
| Listed file | Accident_Dataset final.zip |
| File identifier | d6a2455e-9cb3-463e-b736-29473a89bf86 |
| Archive size | 4,907,713 bytes |
| Workbook size | 6,324,598 bytes |
| Publisher archive SHA-256 | ece6ee48507eb50437079dfb43158a3448e50b249535f4ececa4b5b51dd452d4 |
| Original member | Accident_Dataset final/Modified_Accident_Dataset final.xlsx |

Public inventory endpoint:

```text
https://data.mendeley.com/public-api/datasets/p2kgkb5cd2/files?folder_id=root&version=2&$start=0&$limit=1000
```

Requested with `Accept: application/vnd.mendeley-public-dataset.1+json`, it returned one completed file and the checksum above. Original download URL:

```text
https://data.mendeley.com/public-files/datasets/p2kgkb5cd2/files/d6a2455e-9cb3-463e-b736-29473a89bf86/file_downloaded
```

Public GET access succeeded without credentials. The pipeline pins this release, validates archive SHA-256 and CRCs, accepts only the inspected workbook member, and preserves its bytes. The workbook hash and reference acquisition time are in `reports/source_manifest.json`. Disabling checks to accept another release would break reproducibility.

The Python downloader supplies explicit User-Agent and Accept headers: plain default urllib requests received HTTP 403 during fresh-download testing, while the configured request succeeded. An uncached end-to-end download/extraction check is recorded in `reports/acquisition_validation.json`. If access policy changes, use the original-file manual instructions in the README; checksum verification remains mandatory.

## Claimed versus verifiable coverage

The publisher describes 49,566 records across 2007–2024 from ARI, BRTA, DMP, MP Unit, and field forms. Claimed periods are stored in `reports/tables/source_coverage.csv`; they are not independently verified institutional histories.

The actual workbook contains 47,680 rows and 31 columns. No row-level institution, separate institutional extracts, source-specific sheets, field codebook, or transformation script is provided. Coverage overlap and collection changes cannot be resolved from the artifact. The filename identifies the workbook as modified.

After exact deduplication, Year spans 2007–2021 while parsed Date spans 2022–2024 and every parseable date conflicts with Year. Coordinates occupy a limited extent with extensive repetition. Street/highway labels do not establish national coverage, and no district/division codes are invented.

Only the requested original Mendeley artifact contributes to this analysis. A Figshare workbook encountered during earlier discovery is not used as a substitute. No synthetic road dataset, mirror, or analytical test fixture contributes to findings.

## Attribution and transformations

Citation: Nur, Fernaz; Sahin Afridi, Arafat (2025), *Bangladesh Road Traffic Accident Dataset (2007–2024): Multi-Source Integration from ARI, BRTA, DMP, MP Unit.*, Mendeley Data, v2, DOI 10.17632/p2kgkb5cd2.2.

Changes occur only in derived copies: exact-row removal, whitespace/token normalization, explicit parsing, internal row keys, quality flags, participant extraction, aggregates, and conditional statistics. Source-derived outputs retain CC BY 4.0 attribution. No depositor or institutional endorsement is implied.
