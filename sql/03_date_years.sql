SELECT date_year, COUNT(*) AS records, SUM(date_year_conflict) AS declared_year_conflicts
FROM records WHERE date_year IS NOT NULL GROUP BY date_year ORDER BY date_year;
