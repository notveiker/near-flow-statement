-- Q3. Fills and priced volume by inferred solver (distinct-counterparty rule), top 3000 by fills.
SELECT solver_cps AS solver, COUNT(*) AS fills, COUNTIF(usd IS NOT NULL) AS priced, SUM(usd) AS usd,
       MAX(IF(a = solver_cps, cps_a, cps_b)) AS cps, MIN(day) AS first_day, MAX(day) AS last_day, COUNT(DISTINCT day) AS days
FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver`
WHERE solver_cps IS NOT NULL AND day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015
GROUP BY 1 ORDER BY fills DESC LIMIT 3000
