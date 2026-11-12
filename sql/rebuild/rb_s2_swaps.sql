-- STAGE 2. One row per token_diff receipt (a settlement) in the Q3/Q4 window 2026-08-07..2026-11-04.
-- simple  = exactly 2 token_diff legs from 2 distinct accounts (one side is a solver, the other a user: INFERRED).
-- complex = anything else (batches, 3+ legs, one account on both sides); counted, never valued.
-- usd = the largest priced token amount in the swap. Stable tokens (rule in tokens table) are priced at 1.00; majors at
-- that UTC day's CoinGecko close (nearest day when a day is missing); tokens with neither price leave usd NULL.
CREATE OR REPLACE TABLE `inlaid-backbone-501715-q6.nfs_rebuild.swaps` AS
WITH base AS (
  SELECT day, h, rid, JSON_VALUE(d, '$.account_id') AS acct, JSON_VALUE(d, '$.referral') AS referral,
         JSON_QUERY(d, '$.diff') AS diffstr
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
  WHERE event = 'token_diff' AND day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015
),
r AS (
  SELECT rid, ANY_VALUE(day) AS day, MIN(h) AS h, COUNT(*) AS n_legs, COUNT(DISTINCT acct) AS n_acct,
         ARRAY_AGG(STRUCT(acct, referral, diffstr) ORDER BY acct, diffstr) AS legs
  FROM base GROUP BY rid
),
pairs AS (
  SELECT r.rid, r.day, p,
         REGEXP_EXTRACT(p, r'^"([^"]+)"') AS tid,
         SAFE_CAST(REGEXP_EXTRACT(p, r':"(-?[0-9]+)"$') AS BIGNUMERIC) AS amt
  FROM r, UNNEST(r.legs) lg, UNNEST(REGEXP_EXTRACT_ALL(lg.diffstr, r'"[^"]+":"-?[0-9]+"')) p
  WHERE r.n_legs = 2 AND r.n_acct = 2
),
val AS (
  SELECT x.rid,
         MAX(SAFE_DIVIDE(ABS(CAST(x.amt AS FLOAT64)), POW(10, t.decimals)) * IF(t.is_stable, 1.0, pr.usd)) AS usd,
         ARRAY_AGG(IF(t.is_stable, 'stable', IF(pr.usd IS NOT NULL, 'major', NULL)) IGNORE NULLS ORDER BY IF(t.is_stable, 0, 1) LIMIT 1)[SAFE_OFFSET(0)] AS basis
  FROM pairs x
  LEFT JOIN `inlaid-backbone-501715-q6.nfs_rebuild.tokens` t ON t.asset_id = x.tid
  LEFT JOIN `inlaid-backbone-501715-q6.nfs_rebuild.prices` pr ON pr.symbol = t.symbol AND pr.day = x.day
  GROUP BY x.rid
)
SELECT r.rid, r.day, r.h, IF(r.n_legs = 2 AND r.n_acct = 2, 'simple', 'complex') AS kind, r.n_legs,
       IF(r.n_legs = 2 AND r.n_acct = 2, r.legs[OFFSET(0)].acct, NULL) AS a,
       IF(r.n_legs = 2 AND r.n_acct = 2, r.legs[OFFSET(1)].acct, NULL) AS b,
       IF(r.n_legs = 2 AND r.n_acct = 2, COALESCE(r.legs[OFFSET(0)].referral, r.legs[OFFSET(1)].referral), NULL) AS referral,
       v.usd, v.basis
FROM r LEFT JOIN val v USING (rid)
