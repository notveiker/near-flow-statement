-- RX9/RX10. Route mix and swap size of public simple swaps priced by the rebuild rule, 2026-08-07..2026-11-04 (staged tables, megabytes).
-- Parts: class (stable/volatile classes), pair (top pairs), near (NEAR token on either side), xchain (tokens on different chains), weekly (stable-to-stable share per 7-day block),
-- size (bucket counts and volume), pct (percentiles of swap size), topday (daily volume), top (largest swaps, first 8 characters of the receipt id).
WITH s AS (
  SELECT rid, day, usd FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps`
  WHERE kind = 'simple' AND usd IS NOT NULL AND day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015
),
tk AS (
  SELECT e.rid, JSON_VALUE(e.d, '$.account_id') AS acct,
         REGEXP_EXTRACT(p, r'^"([^"]+)"') AS tid
  FROM (SELECT rid, d FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
        WHERE event = 'token_diff' AND day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015) e
  JOIN s USING (rid),
  UNNEST(REGEXP_EXTRACT_ALL(JSON_QUERY(e.d, '$.diff'), r'"[^"]+":"-?[0-9]+"')) p
),
pt AS (
  SELECT DISTINCT t.rid, t.tid FROM tk t
),
c AS (
  SELECT s.rid, s.day, s.usd, COUNT(*) AS n_tok,
         LOGICAL_OR(k.asset_id IS NULL) AS any_unk,
         COUNTIF(IFNULL(k.is_stable, FALSE)) AS n_st,
         STRING_AGG(IFNULL(k.symbol, 'UNKNOWN'), '/' ORDER BY IFNULL(k.symbol, 'UNKNOWN')) AS pair,
         COUNT(DISTINCT IFNULL(k.blockchain, '?')) AS n_chain,
         LOGICAL_OR(IFNULL(k.symbol, '') IN ('NEAR', 'wNEAR')) AS has_near,
         DIV(DATE_DIFF(ANY_VALUE(s.day), DATE '2026-08-07', DAY), 7) AS blk
  FROM s JOIN pt USING (rid) LEFT JOIN `inlaid-backbone-501715-q6.nfs_rebuild.tokens` k ON k.asset_id = pt.tid
  GROUP BY s.rid, s.day, s.usd
),
qs AS (SELECT APPROX_QUANTILES(usd, 1000) AS q FROM s)
SELECT 'class' AS part, CASE WHEN n_tok != 2 THEN 'other_n_tok' WHEN any_unk THEN 'unknown' WHEN n_st = 2 THEN 'stable_stable' WHEN n_st = 1 THEN 'stable_volatile' ELSE 'volatile_volatile' END AS k,
       CAST(COUNT(*) AS FLOAT64) AS x1, SUM(usd) AS x2, NULL AS x3 FROM c GROUP BY 2
UNION ALL SELECT 'pair', pair, CAST(COUNT(*) AS FLOAT64), SUM(usd), CAST(MAX(n_chain) AS FLOAT64) FROM c WHERE n_tok = 2 GROUP BY pair
UNION ALL SELECT 'near', CAST(has_near AS STRING), CAST(COUNT(*) AS FLOAT64), SUM(usd), NULL FROM c WHERE n_tok = 2 AND NOT any_unk GROUP BY 2
UNION ALL SELECT 'xchain', CAST(n_chain > 1 AS STRING), CAST(COUNT(*) AS FLOAT64), SUM(usd), NULL FROM c WHERE n_tok = 2 AND NOT any_unk GROUP BY 2
UNION ALL SELECT 'weekly', CAST(blk AS STRING), SUM(IF(n_st = 2, usd, 0)), SUM(usd), CAST(COUNT(*) AS FLOAT64) FROM c WHERE n_tok = 2 AND NOT any_unk GROUP BY blk
UNION ALL SELECT 'size', CASE WHEN usd < 100 THEN 'a_<100' WHEN usd < 1000 THEN 'b_100-1k' WHEN usd < 10000 THEN 'c_1k-10k' WHEN usd < 100000 THEN 'd_10k-100k' WHEN usd < 1000000 THEN 'e_100k-1m' ELSE 'f_>=1m' END,
       CAST(COUNT(*) AS FLOAT64), SUM(usd), NULL FROM s GROUP BY 2
UNION ALL SELECT 'pct', CAST(i AS STRING), qs.q[OFFSET(i)], NULL, NULL FROM qs, UNNEST([100, 250, 500, 750, 900, 990, 999]) i
UNION ALL SELECT 'topday', CAST(day AS STRING), SUM(usd), CAST(COUNT(*) AS FLOAT64), NULL FROM s GROUP BY day
UNION ALL SELECT 'top', SUBSTR(rid, 1, 8), usd, NULL, NULL FROM (SELECT rid, usd FROM s ORDER BY usd DESC LIMIT 10)
