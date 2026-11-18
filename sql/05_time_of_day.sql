SELECT hour, COUNT(*) AS records, SUM(fatal_record) AS fatal_records,
 AVG(fatal_record) AS fatal_record_share
FROM records WHERE hour IS NOT NULL GROUP BY hour ORDER BY hour;
