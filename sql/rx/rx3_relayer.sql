-- RX3. Who signs the transactions sent to intents.near (exact, full chain), 2025-01-01..2026-11-04. Per month: transactions, distinct signers, the top signer and its share,
-- the top-5 share; per 7-day block ending 2026-11-04 (the last 16 blocks): the same.
WITH t AS (
  SELECT block_date AS day, signer_account_id AS sg
  FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
  WHERE block_date BETWEEN '2025-01-01' AND '2026-11-04' AND block_height <= 223088015 AND receiver_account_id = 'intents.near'
),
m AS (SELECT FORMAT_DATE('%Y-%m', day) AS per, 'month' AS kind, sg, COUNT(*) AS n FROM t GROUP BY 1, 2, 3),
w AS (SELECT FORMAT_DATE('%F', DATE_SUB(DATE '2026-11-04', INTERVAL DIV(DATE_DIFF(DATE '2026-11-04', day, DAY), 7) * 7 DAY)) AS per, 'week_ending' AS kind, sg, COUNT(*) AS n
      FROM t WHERE day >= DATE '2026-07-16' GROUP BY 1, 2, 3),
a AS (SELECT * FROM m UNION ALL SELECT * FROM w),
r AS (SELECT per, kind, sg, n, ROW_NUMBER() OVER (PARTITION BY per, kind ORDER BY n DESC, sg) AS rk, SUM(n) OVER (PARTITION BY per, kind) AS tot, COUNT(*) OVER (PARTITION BY per, kind) AS signers FROM a)
SELECT per, kind, ANY_VALUE(tot) AS tx, ANY_VALUE(signers) AS signers, MAX(IF(rk = 1, sg, NULL)) AS top1, MAX(IF(rk = 1, n, 0)) AS top1_n,
       SUM(IF(rk <= 5, n, 0)) AS top5_n, MAX(IF(rk = 2, sg, NULL)) AS top2, MAX(IF(rk = 2, n, 0)) AS top2_n
FROM r GROUP BY per, kind ORDER BY kind, per
