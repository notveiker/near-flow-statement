-- F11. What users pay on stable-to-stable simple swaps, from the two legs of each settlement. Simple swap = Q3 stage (2 token_diff legs, 2 accounts); the user is the
-- account that is not the inferred solver (distance rule). Both user legs must be stable tokens (tokens.is_stable). Paid = |negative amount| / 10^decimals,
-- received = positive amount / 10^decimals; spread = paid - received. pair_class: same_symbol (e.g. USDC to USDC across chains, no peg difference) or diff_symbol.
-- referral class: 1click (tag starts with 1click-), other, none. Aggregated by month, solver, pair class, referral class and paid-size bucket.
WITH s AS (SELECT rid, day, solver_cps AS solver, referral FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver` WHERE solver_cps IS NOT NULL),
legs AS (
  SELECT e.rid, JSON_VALUE(e.d, '$.account_id') AS acct, JSON_QUERY(e.d, '$.diff') AS diffstr
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events` e JOIN s USING (rid)
  WHERE e.event = 'token_diff' AND e.day BETWEEN '2026-08-07' AND '2026-11-04' AND e.h <= 223088015
),
u AS (
  SELECT l.rid, s.day, s.solver, s.referral, p,
         REGEXP_EXTRACT(p, r'^"([^"]+)"') AS tid, SAFE_CAST(REGEXP_EXTRACT(p, r':"(-?[0-9]+)"$') AS BIGNUMERIC) AS amt
  FROM legs l JOIN s USING (rid), UNNEST(REGEXP_EXTRACT_ALL(l.diffstr, r'"[^"]+":"-?[0-9]+"')) p
  WHERE l.acct != s.solver
),
v AS (
  SELECT u.rid, ANY_VALUE(u.day) AS day, ANY_VALUE(u.solver) AS solver, ANY_VALUE(u.referral) AS referral,
         COUNT(*) AS n_tok, COUNTIF(t.is_stable) AS n_stable,
         MAX(IF(u.amt < 0, SAFE_DIVIDE(CAST(-u.amt AS FLOAT64), POW(10, t.decimals)), NULL)) AS paid,
         MAX(IF(u.amt > 0, SAFE_DIVIDE(CAST(u.amt AS FLOAT64), POW(10, t.decimals)), NULL)) AS received,
         MAX(IF(u.amt < 0, t.symbol, NULL)) AS sym_in, MAX(IF(u.amt > 0, t.symbol, NULL)) AS sym_out
  FROM u LEFT JOIN `inlaid-backbone-501715-q6.nfs_rebuild.tokens` t ON t.asset_id = u.tid
  GROUP BY u.rid
)
SELECT FORMAT_DATE('%Y-%m', day) AS month, solver, IF(sym_in = sym_out, 'same_symbol', 'diff_symbol') AS pair_class,
       CASE WHEN referral LIKE '1click-%' THEN '1click' WHEN referral IS NULL THEN 'none' ELSE 'other' END AS ref_class,
       CASE WHEN paid < 100 THEN 'a_<100' WHEN paid < 1000 THEN 'b_100-1k' WHEN paid < 10000 THEN 'c_1k-10k' WHEN paid < 100000 THEN 'd_10k-100k' ELSE 'e_>=100k' END AS size,
       COUNT(*) AS n, SUM(paid) AS paid, SUM(received) AS received,
       SUM(IF(received > paid, 1, 0)) AS n_negative_spread,
       APPROX_QUANTILES(SAFE_DIVIDE(paid - received, paid) * 1e4, 100)[OFFSET(50)] AS median_bp
FROM v
WHERE n_tok = 2 AND n_stable = 2 AND paid > 0 AND received > 0
GROUP BY 1, 2, 3, 4, 5
