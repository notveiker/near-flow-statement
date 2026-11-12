-- Q3. Inbound movements for the 20 solvers with the most fills, inside the window only (earlier funding is not read):
-- mt_transfer in (counterparty = old_owner) and mt_mint (counterparty = transaction signer). Counts by counterparty,
-- the 50 most frequent per solver (first version hit the 1,000,000-row output cap).
WITH top AS (
  SELECT solver_cps AS s FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver` WHERE solver_cps IS NOT NULL
  GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 20
),
tr AS (
  SELECT JSON_VALUE(d, '$.new_owner_id') AS solver, JSON_VALUE(d, '$.old_owner_id') AS cp, 'mt_transfer' AS kind, day
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events` WHERE event = 'mt_transfer' AND h <= 223088015
    AND JSON_VALUE(d, '$.new_owner_id') IN (SELECT s FROM top)
),
mi AS (
  SELECT JSON_VALUE(d, '$.owner_id') AS solver, signer AS cp, 'mt_mint' AS kind, day
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.mint_origin` WHERE h <= 223088015 AND JSON_VALUE(d, '$.owner_id') IN (SELECT s FROM top)
)
SELECT * EXCEPT (rk) FROM (
  SELECT solver, cp, kind, COUNT(*) AS n, MIN(day) AS first_day, MAX(day) AS last_day,
         SUM(COUNT(*)) OVER (PARTITION BY solver) AS solver_total_inbound,
         ROW_NUMBER() OVER (PARTITION BY solver ORDER BY COUNT(*) DESC, cp, kind) AS rk
  FROM (SELECT * FROM tr UNION ALL SELECT * FROM mi)
  GROUP BY 1, 2, 3
) WHERE rk <= 50 ORDER BY solver, n DESC
