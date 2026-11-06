-- Q3: on 2026-10-08, intents.near / wrap.near log lines naming bridge-mng.near, the two accounts n1-transit.near paid
-- natively that day (611db101..., 1d1de23c...), the intents account that withdrew USDC to n1-treasury (f63172c1...),
-- or the amount 54,823.5795 NEAR in yocto prefix. Checks whether that NEAR entered intents.near.
SELECT o.block_date, o.block_height, o.executor_account_id AS executor, SUBSTR(l.element, 1, 3000) AS element
FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o, UNNEST(o.logs.list) l
WHERE o.block_date = '2026-10-08'
  AND o.executor_account_id IN ('intents.near', 'wrap.near')
  AND (l.element LIKE '%bridge-mng.near%'
    OR l.element LIKE '%611db1013ed5840d692d2e9fe9eb34d9b1f8b1910a9dc1db7aa912e731f53d2e%'
    OR l.element LIKE '%1d1de23c317505e65867518a20caa01c69b99d4209c27b4d756f83b7d122e302%'
    OR l.element LIKE '%f63172c1e7e8580837ac1141d915808fc6f1751ed5c974f2aff5f7029c02ecbf%'
    OR l.element LIKE '%5482357950%')
ORDER BY o.block_height
