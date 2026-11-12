-- F3. Solver fills in anchored complex receipts (each solver leg is one fill), and the simple-swap fills, for the 61 solvers.
WITH ss AS (SELECT DISTINCT solver_cps AS acct FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver` WHERE solver_cps IS NOT NULL),
cx AS (
  SELECT JSON_VALUE(d, '$.account_id') AS solver, COUNT(*) AS fills_complex
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events` e JOIN `inlaid-backbone-501715-q6.nfs_rebuild.swaps_complex` c ON c.rid = e.rid AND c.anchored
  WHERE e.event = 'token_diff' AND JSON_VALUE(d, '$.account_id') IN (SELECT acct FROM ss) AND e.day BETWEEN '2026-08-07' AND '2026-11-04' AND e.h <= 223088015
  GROUP BY 1
),
sm AS (SELECT solver_cps AS solver, COUNT(*) AS fills_simple FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver` WHERE solver_cps IS NOT NULL GROUP BY 1)
SELECT sm.solver, sm.fills_simple, IFNULL(cx.fills_complex, 0) AS fills_complex FROM sm LEFT JOIN cx USING (solver) ORDER BY sm.fills_simple + IFNULL(cx.fills_complex, 0) DESC
