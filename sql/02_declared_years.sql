-- Source Year is unresolved against Date. Counts are workbook records, not national annual totals.
SELECT declared_year, COUNT(*) AS records, COUNT(DISTINCT descriptor_group) AS descriptor_groups,
 SUM(fatalities) AS summed_fatality_values, SUM(injuries) AS summed_injury_values,
 AVG(fatal_record) AS fatal_record_share, SUM(date_year_conflict) AS date_year_conflicts
FROM records GROUP BY declared_year ORDER BY declared_year;
