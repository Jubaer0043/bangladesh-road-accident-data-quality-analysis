# Actual workbook and derived fields

The workbook contains one `Sheet1` with the following 31 original columns. Full original names, including spaces and misspellings, appear in `reports/tables/column_inventory.csv` and the schema contract. The interpretations below document observed usage; no publisher codebook was included.

| Original column (trimmed for display) | Analytical treatment |
| --- | --- |
| Accident Serial No | Unverified serial; not globally unique |
| Date | Mixed Excel dates, slash strings, invalid tokens; parsed independently |
| Time | Parsed hour and six-hour bands |
| Location | Free-text street/highway/place; no district inferred |
| Longitude and Latitude | N/E strings parsed by hemisphere despite reversed header |
| Driver  Age | Recorded numeric age; concentration audited |
| Accident Narrative | Local descriptor matching only; excluded from exports |
| Vehicle Info | Recorded description and participant-token extraction |
| Vehicle Count | Recorded count; no exposure interpretation |
| Death Count | Recorded fatality value; positive value defines fatal-record flag |
| Death Info | Personal-detail text excluded from analytical exports |
| Injury Count | Recorded injury value |
| Injury Info | Personal-detail text excluded from analytical exports |
| Light Condition | First light field, retained as `light_original` |
| Weather_x | First weather field, separately retained |
| Road Surface Type | Recorded surface type |
| Road nature | Recorded road nature; limited spelling normalization |
| Road classification | Recorded road class; not proof of national coverage |
| Place characteristic | Recorded place characteristic |
| Type of Road connection point | Inventoried; distinct from Junction; no silent harmonization |
| Road Surface Condition | Recorded surface condition |
| Victim Category | Recorded road-user label; limited spelling normalization |
| Trafic Condition | Inventoried; distinct from Traffic_Control |
| ID | Repeated unverified ID; institutional source unavailable |
| Year | Declared year, retained independently from Date |
| Month | Declared English month; mapped independently to month number |
| Accident_Intensity | Categorical label; no assumed numeric severity scale |
| Junction | Second junction field, separately retained |
| Traffic_Control | Second traffic-control field |
| Weather_y | Second weather field; no claim of greater accuracy |
| Lighting | Second light field; conditional Day/Night comparison |

## Derived fields

| Field | Meaning |
| --- | --- |
| `source_row` | Original Excel row starting at 2; unique internal provenance key |
| `date_parsed` | Explicitly parsed Date; invalid values remain missing |
| `date_year`, `date_month` | Parsed Date components; not corrections to source Year/Month |
| `declared_year`, `declared_month` | Separate source Year and numeric Month mapping |
| `date_ambiguous` | Slash string permits different day/month readings |
| `date_year_conflict`, `date_month_conflict` | Parsed and declared components disagree |
| `hour`, `time_band` | Parsed Time hour and six-hour interval |
| `latitude`, `longitude` | Parsed N/E values; no imputation |
| `inside_broad_bd_box` | Coarse box screen, not country-boundary verification |
| `fatal_record` | Death Count > 0; no verified identity or exposure interpretation |
| `severity_fatality_disagreement` | Death label disagrees with positive numeric count; codebook-dependent audit assumption |
| `weather_disagreement`, `light_disagreement` | Case-insensitive lexical mismatch; no claim of which field is correct |
| `descriptor_group` | SHA-256 of normalized Date/Time/Location/Narrative/Vehicle Info; candidate identity only |
| `descriptor_group_size` | Primary records sharing candidate descriptors |

The SQL model retains the subset needed for queries. `records.source_row` is the primary key; `participants` has composite key (`source_row`, `participant_type`) and a foreign key to records. Several participant types can link to one record.

## Output grains

Year/month tables distinguish declared and parsed bases. Hour, severity, road, weather, and light tables group recorded fields. `geography.csv` groups normalized place labels and `coordinates.csv` groups parsed coordinate pairs; neither defines administrative areas. `descriptor_groups.csv` contains candidate-group hashes and conflict counts. `duplicate_sensitivity.csv` has alternative, non-additive analytical populations. Full local cleaned data and SQLite are excluded from Git; aggregate evidence is versionable.
