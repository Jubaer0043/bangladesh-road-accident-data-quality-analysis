from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW, EXTERNAL, PROCESSED = (
    ROOT / f"data/{p}" for p in ["raw", "external", "processed"]
)
REPORTS = ROOT / "reports"
TABLES, FIGURES = REPORTS / "tables", REPORTS / "figures"
DB = PROCESSED / "accident_records.sqlite3"
SOURCE = "https://data.mendeley.com/datasets/p2kgkb5cd2/2"
DOI = "10.17632/p2kgkb5cd2.2"
FILE_ID = "d6a2455e-9cb3-463e-b736-29473a89bf86"
DOWNLOAD = f"https://data.mendeley.com/public-files/datasets/p2kgkb5cd2/files/{FILE_ID}/file_downloaded"
INVENTORY = "https://data.mendeley.com/public-api/datasets/p2kgkb5cd2/files?folder_id=root&version=2&$start=0&$limit=1000"
PUBLISHED_SHA256 = "ece6ee48507eb50437079dfb43158a3448e50b249535f4ececa4b5b51dd452d4"
MEMBER = "Accident_Dataset final/Modified_Accident_Dataset final.xlsx"
WORKBOOK = RAW / "Modified_Accident_Dataset final.xlsx"
# Established AFTER inspecting the actual version-2 workbook, not from its description.
COLUMNS = [
    "Accident Serial No",
    "Date ",
    "Time",
    "Location",
    "Longitude and Latitude",
    "Driver  Age ",
    "Accident Narrative",
    "Vehicle Info",
    "Vehicle Count ",
    "Death Count",
    "Death Info",
    "Injury Count",
    "Injury Info",
    "Light Condition",
    "Weather_x",
    "Road Surface Type",
    "Road nature",
    "Road classification",
    "Place characteristic",
    "Type of Road connection point ",
    "Road Surface Condition",
    "Victim Category",
    "Trafic Condition ",
    "ID",
    "Year",
    "Month",
    "Accident_Intensity",
    "Junction",
    "Traffic_Control",
    "Weather_y",
    "Lighting",
]
