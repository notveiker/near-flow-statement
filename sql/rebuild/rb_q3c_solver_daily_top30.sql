-- Q3. Daily fills and volume of the 30 solvers with the most fills (distinct-counterparty rule).
WITH top AS (
  SELECT solver_cps AS s FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver` WHERE solver_cps IS NOT NULL
  GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 30
)
SELECT day, solver_cps AS solver, COUNT(*) AS fills, COUNTIF(usd IS NOT NULL) AS priced, SUM(usd) AS usd
FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver`
WHERE solver_cps IN (SELECT s FROM top) AND day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015
GROUP BY 1, 2 ORDER BY 1, 2
