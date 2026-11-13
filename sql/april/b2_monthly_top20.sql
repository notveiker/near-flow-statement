-- Ask B(2). Per month, the 20 most-called receivers (transactions sent to them), their count and share of the month's transactions.
WITH m AS (
  SELECT FORMAT_DATE('%Y-%m', block_date) AS month, receiver_account_id AS receiver, COUNT(*) AS n
  FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
  WHERE block_date BETWEEN '2025-07-01' AND '2026-11-04' AND block_height <= 223088015
  GROUP BY 1, 2
),
t AS (SELECT month, SUM(n) AS month_total FROM m GROUP BY 1)
SELECT month, receiver, n, month_total, n / month_total AS share,
       ROW_NUMBER() OVER (PARTITION BY month ORDER BY n DESC) AS rk
FROM m JOIN t USING (month)
QUALIFY ROW_NUMBER() OVER (PARTITION BY month ORDER BY n DESC) <= 20
ORDER BY month, rk
