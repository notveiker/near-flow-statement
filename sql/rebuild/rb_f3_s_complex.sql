-- F3 STAGE. Complex token_diff receipts (not exactly two legs from two accounts) anchored on their single user.
-- Solver set = the 61 accounts classified as solver in simple swaps (swaps_solver.solver_cps). A complex receipt is
-- "anchored" when exactly one participant is neither a solver nor intents.near and at least one participant is a solver.
-- Value = the largest priced token amount in the user's legs (same price rules as stage 2). Others are counted, not valued.
CREATE OR REPLACE TABLE `inlaid-backbone-501715-q6.nfs_rebuild.swaps_complex` AS
WITH ss AS (SELECT DISTINCT solver_cps AS acct FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver` WHERE solver_cps IS NOT NULL),
base AS (
  SELECT day, h, rid, JSON_VALUE(d, '$.account_id') AS acct, JSON_VALUE(d, '$.referral') AS referral, JSON_QUERY(d, '$.diff') AS diffstr
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
  WHERE event = 'token_diff' AND day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015
),
r AS (
  SELECT rid, ANY_VALUE(day) AS day, MIN(h) AS h, COUNT(*) AS n_legs, COUNT(DISTINCT acct) AS n_acct,
         COUNT(DISTINCT IF(acct NOT IN (SELECT acct FROM ss) AND acct != 'intents.near', acct, NULL)) AS n_user,
         COUNTIF(acct IN (SELECT acct FROM ss)) AS n_solver_legs,
         MAX(IF(acct NOT IN (SELECT acct FROM ss) AND acct != 'intents.near', acct, NULL)) AS user_acct,
         MAX(IF(acct NOT IN (SELECT acct FROM ss) AND acct != 'intents.near', referral, NULL)) AS referral
  FROM base GROUP BY rid
  HAVING NOT (COUNT(*) = 2 AND COUNT(DISTINCT acct) = 2)
),
pairs AS (
  SELECT b.rid, b.day, REGEXP_EXTRACT(p, r'^"([^"]+)"') AS tid, SAFE_CAST(REGEXP_EXTRACT(p, r':"(-?[0-9]+)"$') AS BIGNUMERIC) AS amt
  FROM base b JOIN r USING (rid), UNNEST(REGEXP_EXTRACT_ALL(b.diffstr, r'"[^"]+":"-?[0-9]+"')) p
  WHERE r.n_user = 1 AND r.n_solver_legs >= 1 AND b.acct = r.user_acct
),
val AS (
  SELECT x.rid, MAX(SAFE_DIVIDE(ABS(CAST(x.amt AS FLOAT64)), POW(10, t.decimals)) * IF(t.is_stable, 1.0, pr.usd)) AS usd,
         ARRAY_AGG(IF(t.is_stable, 'stable', IF(pr.usd IS NOT NULL, 'major', NULL)) IGNORE NULLS ORDER BY IF(t.is_stable, 0, 1) LIMIT 1)[SAFE_OFFSET(0)] AS basis
  FROM pairs x LEFT JOIN `inlaid-backbone-501715-q6.nfs_rebuild.tokens` t ON t.asset_id = x.tid LEFT JOIN `inlaid-backbone-501715-q6.nfs_rebuild.prices` pr ON pr.symbol = t.symbol AND pr.day = x.day
  GROUP BY x.rid
)
SELECT r.rid, r.day, r.h, r.n_legs, r.n_acct, r.n_solver_legs, r.user_acct, r.referral,
       (r.n_user = 1 AND r.n_solver_legs >= 1) AS anchored, v.usd, v.basis
FROM r LEFT JOIN val v USING (rid)
