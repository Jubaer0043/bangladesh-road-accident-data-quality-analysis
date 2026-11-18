PRAGMA foreign_keys=ON;
-- One preserved workbook row after exact deduplication, NOT one verified accident.
CREATE TABLE records (
 source_row INTEGER PRIMARY KEY,
 serial_no INTEGER, source_id INTEGER, declared_year INTEGER, declared_month INTEGER,
 date_parsed TEXT, date_year INTEGER, date_month INTEGER,
 date_year_conflict INTEGER, date_month_conflict INTEGER,
 hour INTEGER CHECK(hour BETWEEN 0 AND 23), time_band TEXT,
 location TEXT, fatalities INTEGER CHECK(fatalities>=0), injuries INTEGER CHECK(injuries>=0),
 vehicle_count INTEGER, fatal_record INTEGER CHECK(fatal_record IN (0,1)), severity_label TEXT,
 light_original TEXT, lighting TEXT, weather_x TEXT, weather_y TEXT,
 road_class TEXT, road_condition TEXT, road_surface TEXT, victim_category TEXT,
 latitude REAL, longitude REAL, descriptor_group TEXT NOT NULL
);
CREATE INDEX idx_descriptor ON records(descriptor_group);
CREATE TABLE participants (
 source_row INTEGER NOT NULL REFERENCES records(source_row),
 participant_type TEXT NOT NULL, PRIMARY KEY(source_row, participant_type)
);
