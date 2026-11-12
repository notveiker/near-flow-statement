-- Q3 sensitivity. Same shares under the alternative rule (solver = participant with more fills), top 3000.
SELECT solver_fills AS solver, COUNT(*) AS fills, COUNTIF(usd IS NOT NULL) AS priced, SUM(usd) AS usd
FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver`
WHERE solver_fills IS NOT NULL AND day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015
GROUP BY 1 ORDER BY fills DESC LIMIT 3000
