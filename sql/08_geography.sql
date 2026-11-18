-- Labels as published; street/highway labels are not districts or national exposure denominators.
SELECT location, COUNT(*) AS records, COUNT(DISTINCT descriptor_group) AS descriptor_groups
FROM records GROUP BY location ORDER BY records DESC,location;
