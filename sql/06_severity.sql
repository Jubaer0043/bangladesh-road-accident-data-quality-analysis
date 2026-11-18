SELECT severity_label, COUNT(*) AS records, SUM(fatal_record) AS fatal_records,
 SUM(fatalities) AS summed_fatality_values, AVG(fatal_record) AS fatal_record_share
FROM records GROUP BY severity_label ORDER BY records DESC;
