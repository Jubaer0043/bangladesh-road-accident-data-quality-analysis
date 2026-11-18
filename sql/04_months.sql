-- Report both month fields independently; neither is silently corrected using the other.
SELECT 'Month column' AS basis, declared_month AS month, COUNT(*) AS records
FROM records WHERE declared_month IS NOT NULL GROUP BY declared_month
UNION ALL
SELECT 'Parsed Date' AS basis, date_month AS month, COUNT(*) AS records
FROM records WHERE date_month IS NOT NULL GROUP BY date_month;
