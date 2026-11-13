-- What else fell between 2025Q3 and 2026Q3, exactly: transactions per signer in 2025-07-01..2025-09-30 (a) and 2026-07-01..2026-09-30 (b), signers outside class C only.
-- Parts: (summary) totals and signer counts; (decline) gross decline = sum over signers of max(a - b, 0), signers needed for 50%/80% of it; (top) the 60 largest decliners
-- with their most frequent receiver; (growth) the 20 largest risers.
WITH s AS (
  SELECT signer_account_id AS sg, COUNTIF(block_date < '2026-01-01') AS a, COUNTIF(block_date >= '2026-01-01') AS b,
         APPROX_TOP_COUNT(receiver_account_id, 1)[OFFSET(0)].value AS top_receiver
  FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
  WHERE (block_date BETWEEN '2025-07-01' AND '2025-09-30' OR block_date BETWEEN '2026-07-01' AND '2026-09-30') AND block_height <= 223088015
    AND signer_account_id NOT IN ('hotwallet.kaiching', 'sweat-migration.near', 'users.kaiching') AND NOT ENDS_WITH(receiver_account_id, '.users.kaiching')
  GROUP BY 1
),
d AS (SELECT *, GREATEST(a - b, 0) AS dec, GREATEST(b - a, 0) AS inc FROM s),
rk AS (SELECT sg, a, b, dec, top_receiver, SUM(dec) OVER (ORDER BY dec DESC, sg) AS cum, SUM(dec) OVER () AS tot, ROW_NUMBER() OVER (ORDER BY dec DESC, sg) AS r FROM d WHERE dec > 0)
SELECT 'summary' AS part, '' AS k, CAST(SUM(a) AS FLOAT64) AS x1, CAST(SUM(b) AS FLOAT64) AS x2, CAST(SUM(dec) AS FLOAT64) AS x3, CAST(SUM(inc) AS FLOAT64) AS x4, CAST(COUNT(*) AS FLOAT64) AS x5, '' AS note FROM d
UNION ALL SELECT 'n_for_share', '0.5', CAST(MIN(r) AS FLOAT64), NULL, NULL, NULL, NULL, '' FROM rk WHERE cum >= 0.5 * tot
UNION ALL SELECT 'n_for_share', '0.8', CAST(MIN(r) AS FLOAT64), NULL, NULL, NULL, NULL, '' FROM rk WHERE cum >= 0.8 * tot
UNION ALL SELECT 'top_decline', sg, CAST(a AS FLOAT64), CAST(b AS FLOAT64), CAST(dec AS FLOAT64), CAST(r AS FLOAT64), cum / tot, top_receiver FROM rk WHERE r <= 60
UNION ALL SELECT 'top_rise', sg, CAST(a AS FLOAT64), CAST(b AS FLOAT64), CAST(inc AS FLOAT64), NULL, NULL, top_receiver FROM (SELECT * FROM d ORDER BY inc DESC LIMIT 20)
