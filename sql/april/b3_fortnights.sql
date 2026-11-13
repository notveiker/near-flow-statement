-- Ask B(3). The fortnights either side of 2026-04-02: before = 2026-03-19..2026-04-01, after = 2026-04-02..2026-04-15 (14 days each).
-- Parts: (a) summary (totals, gross drop = sum over signers of max(before - after, 0), signers needed for 50% / 80% of it);
-- (b) the 60 signers with the largest drop, with before, after and their largest receiver; (c) the receiver families that carry the drop
-- (family = the receiver itself for the 40 receivers with the largest drop, else '<64hex>', '<0x-eth>', or the suffix after the first dot, or '<top-level name>').
WITH s AS (
  SELECT signer_account_id AS sg, COUNTIF(block_date < '2026-04-02') AS b, COUNTIF(block_date >= '2026-04-02') AS a
  FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
  WHERE block_date BETWEEN '2026-03-19' AND '2026-04-15' AND block_height <= 223088015
  GROUP BY 1
),
sd AS (SELECT sg, b, a, GREATEST(b - a, 0) AS drop FROM s),
ranked AS (
  SELECT sg, b, a, drop, SUM(drop) OVER (ORDER BY drop DESC, sg ROWS UNBOUNDED PRECEDING) AS cum, SUM(drop) OVER () AS tot,
         ROW_NUMBER() OVER (ORDER BY drop DESC, sg) AS rk
  FROM sd WHERE drop > 0
),
r AS (
  SELECT receiver_account_id AS rc, COUNTIF(block_date < '2026-04-02') AS b, COUNTIF(block_date >= '2026-04-02') AS a
  FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
  WHERE block_date BETWEEN '2026-03-19' AND '2026-04-15' AND block_height <= 223088015
  GROUP BY 1
),
rd AS (SELECT rc, b, a, GREATEST(b - a, 0) AS drop, ROW_NUMBER() OVER (ORDER BY GREATEST(b - a, 0) DESC, rc) AS rk FROM r),
fam AS (
  SELECT IF(rk <= 40, rc,
            CASE WHEN REGEXP_CONTAINS(rc, r'^[0-9a-f]{64}$') THEN '<64hex>' WHEN REGEXP_CONTAINS(rc, r'^0x[0-9a-f]{40}$') THEN '<0x-eth>'
                 WHEN STRPOS(rc, '.') > 0 THEN SUBSTR(rc, STRPOS(rc, '.') + 1) ELSE '<top-level name>' END) AS family, b, a, drop
  FROM rd
)
SELECT 'summary' AS part, '' AS k, CAST(SUM(b) AS FLOAT64) AS x1, CAST(SUM(a) AS FLOAT64) AS x2, CAST(SUM(drop) AS FLOAT64) AS x3, CAST(COUNT(*) AS FLOAT64) AS x4, CAST(COUNTIF(drop > 0) AS FLOAT64) AS x5
FROM sd
UNION ALL
SELECT 'n_signers_for_share', '0.5', CAST(MIN(rk) AS FLOAT64), NULL, NULL, NULL, NULL FROM ranked WHERE cum >= 0.5 * tot
UNION ALL
SELECT 'n_signers_for_share', '0.8', CAST(MIN(rk) AS FLOAT64), NULL, NULL, NULL, NULL FROM ranked WHERE cum >= 0.8 * tot
UNION ALL
SELECT 'n_signers_for_share', '0.9', CAST(MIN(rk) AS FLOAT64), NULL, NULL, NULL, NULL FROM ranked WHERE cum >= 0.9 * tot
UNION ALL
SELECT 'top_signer', sg, CAST(b AS FLOAT64), CAST(a AS FLOAT64), CAST(drop AS FLOAT64), CAST(rk AS FLOAT64), cum / tot FROM ranked WHERE rk <= 60
UNION ALL
SELECT 'family', family, CAST(SUM(b) AS FLOAT64), CAST(SUM(a) AS FLOAT64), CAST(SUM(drop) AS FLOAT64), NULL, NULL FROM fam GROUP BY family HAVING SUM(drop) > 0
