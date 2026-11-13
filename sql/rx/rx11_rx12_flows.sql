-- RX11/RX12. Direction, assets and chains of public simple swaps priced by the rebuild rule, 2026-08-07..2026-11-04 (staged tables).
-- The user is the participant that is not the inferred solver (swaps_solver, as in RX1). Sold = the user's token with a negative diff, bought = positive.
-- Parts: flow (from_chain|to_chain), asset (group: user-sold usd, user-bought usd, swaps), asset_week (blk|group: usd involved, swaps), week_total (blk), vnet (blk: non-stable bought, sold),
-- touch (swaps involving a NEAR-chain token and swaps with a non-stable leg vs all), top3 inputs are derived locally, excl (swaps excluded: direction not exactly one sold and one bought).
WITH s AS (
  SELECT rid, day, usr, usd FROM (
    SELECT ss.rid, ss.day, IF(ss.a = ss.solver_cps, ss.b, ss.a) AS usr, sw.usd
    FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver` ss JOIN `inlaid-backbone-501715-q6.nfs_rebuild.swaps` sw USING (rid)
    WHERE ss.solver_cps IS NOT NULL AND sw.kind = 'simple' AND sw.usd IS NOT NULL
      AND ss.day BETWEEN '2026-08-07' AND '2026-11-04' AND ss.h <= 223088015)
),
pp AS (
  SELECT e.rid, JSON_VALUE(e.d, '$.account_id') AS acct,
         REGEXP_EXTRACT(p, r'^"([^"]+)"') AS tid, STARTS_WITH(REGEXP_EXTRACT(p, r':"(-?[0-9]+)"$'), '-') AS neg
  FROM (SELECT rid, d FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
        WHERE event = 'token_diff' AND day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015) e
  JOIN s USING (rid),
  UNNEST(REGEXP_EXTRACT_ALL(JSON_QUERY(e.d, '$.diff'), r'"[^"]+":"-?[0-9]+"')) p
),
u AS (
  SELECT s.rid, s.day, s.usd, DIV(DATE_DIFF(s.day, DATE '2026-08-07', DAY), 7) AS blk,
         COUNTIF(pp.neg) AS n_sold, COUNTIF(NOT pp.neg) AS n_bought,
         ANY_VALUE(IF(pp.neg, pp.tid, NULL)) AS sold_tid, ANY_VALUE(IF(NOT pp.neg, pp.tid, NULL)) AS bought_tid
  FROM s JOIN pp ON pp.rid = s.rid AND pp.acct = s.usr
  GROUP BY s.rid, s.day, s.usd
),
tk AS (
  SELECT asset_id, blockchain, is_stable,
         CASE WHEN REGEXP_REPLACE(symbol, r'\(DEPRECATED\)$', '') = 'USDT0' THEN 'USDT'
              WHEN REGEXP_REPLACE(symbol, r'\(DEPRECATED\)$', '') = 'WBTC' THEN 'BTC'
              WHEN REGEXP_REPLACE(symbol, r'\(DEPRECATED\)$', '') = 'wNEAR' THEN 'NEAR'
              ELSE REGEXP_REPLACE(symbol, r'\(DEPRECATED\)$', '') END AS grp
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.tokens`
),
d AS (
  SELECT u.rid, u.day, u.usd, u.blk, ts.blockchain AS from_chain, tb.blockchain AS to_chain, ts.grp AS from_grp, tb.grp AS to_grp,
         IFNULL(ts.is_stable, FALSE) AS from_st, IFNULL(tb.is_stable, FALSE) AS to_st, ts.asset_id IS NULL OR tb.asset_id IS NULL AS unk
  FROM u LEFT JOIN tk ts ON ts.asset_id = u.sold_tid LEFT JOIN tk tb ON tb.asset_id = u.bought_tid
  WHERE u.n_sold = 1 AND u.n_bought = 1
),
inv AS (
  SELECT g, SUM(usd) AS v FROM (
    SELECT from_grp AS g, usd FROM d WHERE NOT unk AND NOT from_st
    UNION ALL SELECT to_grp, usd FROM d WHERE NOT unk AND NOT to_st AND to_grp != from_grp) GROUP BY g
),
t3 AS (SELECT ARRAY_AGG(g ORDER BY v DESC LIMIT 3) AS gs FROM inv)
SELECT 'flow' AS part, CONCAT(from_chain, '|', to_chain) AS k, CAST(COUNT(*) AS FLOAT64) AS x1, SUM(usd) AS x2, NULL AS x3 FROM d WHERE NOT unk GROUP BY 2
UNION ALL SELECT 'asset', g, SUM(sold), SUM(bought), SUM(n) FROM (
  SELECT from_grp AS g, usd AS sold, 0.0 AS bought, 1 AS n FROM d WHERE NOT unk
  UNION ALL SELECT to_grp, 0.0, usd, 1 FROM d WHERE NOT unk) GROUP BY g
UNION ALL SELECT 'asset_week', CONCAT(CAST(blk AS STRING), '|', g), SUM(usd), CAST(COUNT(*) AS FLOAT64), NULL FROM (
  SELECT blk, from_grp AS g, usd FROM d WHERE NOT unk
  UNION ALL SELECT blk, to_grp, usd FROM d WHERE NOT unk AND to_grp != from_grp) GROUP BY blk, g
UNION ALL SELECT 'week_total', CAST(blk AS STRING), SUM(usd), CAST(COUNT(*) AS FLOAT64), NULL FROM d WHERE NOT unk GROUP BY blk
UNION ALL SELECT 'vnet', CAST(blk AS STRING), SUM(IF(NOT to_st, usd, 0)), SUM(IF(NOT from_st, usd, 0)), NULL FROM d WHERE NOT unk GROUP BY blk
UNION ALL SELECT 'touch', 'near_chain', CAST(COUNTIF(from_chain = 'near' OR to_chain = 'near') AS FLOAT64), SUM(IF(from_chain = 'near' OR to_chain = 'near', usd, 0)), SUM(usd) FROM d WHERE NOT unk
UNION ALL SELECT 'touch', 'nonstable_leg', CAST(COUNTIF(NOT from_st OR NOT to_st) AS FLOAT64), SUM(IF(NOT from_st OR NOT to_st, usd, 0)), SUM(usd) FROM d WHERE NOT unk
UNION ALL SELECT 'top3', ARRAY_TO_STRING(gs, ','), SUM(IF((from_grp IN UNNEST(gs) AND NOT from_st) OR (to_grp IN UNNEST(gs) AND NOT to_st), usd, 0)), SUM(IF(NOT from_st OR NOT to_st, usd, 0)), NULL FROM d, t3 WHERE NOT unk GROUP BY gs
UNION ALL SELECT 'excl', 'direction_not_1_1_or_unknown', CAST((SELECT COUNT(*) FROM s) - COUNTIF(NOT unk) AS FLOAT64), (SELECT SUM(usd) FROM s) - SUM(IF(NOT unk, usd, 0)), CAST((SELECT COUNT(*) FROM s) AS FLOAT64) FROM d
