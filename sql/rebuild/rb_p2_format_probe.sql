-- P2. Format probe only (not a result): shapes of wrap.near log lines naming intents.near on one day (2026-10-01), digits masked.
SELECT REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(l.element, r'[0-9]{4,}', 'N'), r'[0-9a-f]{64}', 'HEX'), r'[a-z0-9_-]+\.near', 'ACCT') AS shape, COUNT(*) AS n, ANY_VALUE(l.element) AS example
FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` x, UNNEST(x.logs.list) l
WHERE x.block_date = '2026-10-01' AND x.block_height <= 223088015
  AND x.executor_account_id = 'wrap.near' AND l.element LIKE '%intents.near%'
GROUP BY 1 ORDER BY n DESC LIMIT 15
