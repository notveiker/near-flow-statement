-- Sampler validation, second metric group (docs/history-sample-validation.md, addendum): per UTC day over 2025-01-01..2026-09-30, from execution_outcomes:
-- outcomes (all rows), outcomes executed on intents.near, NEAR burnt (tokens_burnt, yocto -> NEAR), failed outcomes. Receipt vs transaction outcomes are not separated here.
SELECT block_date AS day, COUNT(*) AS outcomes, COUNTIF(executor_account_id = 'intents.near') AS on_intents,
       SUM(tokens_burnt) / 1e24 AS burnt_near, COUNTIF(status LIKE '%FAIL%') AS failed
FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes`
WHERE block_date BETWEEN '2025-01-01' AND '2026-09-30' AND block_height <= 223088015
GROUP BY 1 ORDER BY 1
