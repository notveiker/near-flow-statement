-- RX8b. Who sends the direct transactions to v1.signer: per signer, transactions in 2025Q3 (a) and 2026Q3 (b); top 15 by 2026Q3 and the totals.
WITH s AS (
  SELECT signer_account_id AS sg, COUNTIF(block_date < '2026-01-01') AS a, COUNTIF(block_date >= '2026-01-01') AS b
  FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
  WHERE (block_date BETWEEN '2025-07-01' AND '2025-09-30' OR block_date BETWEEN '2026-07-01' AND '2026-09-30') AND block_height <= 223088015 AND receiver_account_id = 'v1.signer'
  GROUP BY 1
)
SELECT 'total' AS part, '' AS sg, SUM(a) AS a, SUM(b) AS b, COUNT(*) AS n FROM s
UNION ALL SELECT 'top', sg, a, b, ROW_NUMBER() OVER (ORDER BY b DESC, sg) FROM s QUALIFY ROW_NUMBER() OVER (ORDER BY b DESC, sg) <= 15
