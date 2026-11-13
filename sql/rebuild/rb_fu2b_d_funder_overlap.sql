-- F2b post hoc (written after seeing the step-3 totals). (1) Direct funders of bridge-mng.near that also received native NEAR from an intents.near
-- native_withdraw in the window: amount funded, amount withdrawn to them. (2) The footprint of the top funder 1244d552... inside intents.near:
-- events that name it, by event type and field.
WITH wd AS (
  SELECT JSON_VALUE(d, '$.receiver_id') AS acct, SUM(SAFE_CAST(JSON_VALUE(d, '$.amount') AS BIGNUMERIC)) / 1e24 AS withdrawn_near, COUNT(*) AS n_wd
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
  WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015 AND event = 'native_withdraw'
  GROUP BY 1
),
f AS (SELECT signer, SUM(near) AS funded_near, COUNT(*) AS n_tx FROM `inlaid-backbone-501715-q6.nfs_rebuild.bridge_direct` WHERE status NOT LIKE '%FAIL%' GROUP BY 1)
SELECT 'overlap' AS part, f.signer AS a, CAST(f.funded_near AS STRING) AS x, CAST(wd.withdrawn_near AS STRING) AS y, CAST(f.n_tx AS STRING) AS n
FROM f JOIN wd ON wd.acct = f.signer
UNION ALL
SELECT 'top_funder_footprint', event, JSON_VALUE(d, '$.account_id'), JSON_VALUE(d, '$.owner_id'), CAST(COUNT(*) AS STRING)
FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015
  AND d LIKE '%1244d552459d7230bdaf267c1d09a296282dc85251958434e670d9b9d561fac7%'
GROUP BY 1, 2, 3, 4
