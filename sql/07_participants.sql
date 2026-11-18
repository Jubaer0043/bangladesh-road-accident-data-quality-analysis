-- Participant rows overlap. Do not add counts or summed fatality values across participants.
SELECT p.participant_type, COUNT(DISTINCT r.source_row) AS records,
 SUM(r.fatal_record) AS fatal_records, AVG(r.fatal_record) AS fatal_record_share
FROM participants p JOIN records r USING(source_row)
GROUP BY p.participant_type ORDER BY records DESC;
