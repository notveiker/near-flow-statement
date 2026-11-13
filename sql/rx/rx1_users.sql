-- RX1. Intents users on chain, 2026-08-07..2026-11-04: the user of a simple swap is the participant that is not the inferred solver (Q3 distance rule; staged table swaps_solver).
-- Priced volume = swaps.usd (largest priced leg). Parts: (summary) users, fills, priced volume; (conc) share of volume held by the top 1/10/100/1000 users and the count of users above
-- $100K; (size) users and volume by total-volume bucket; (top) the 10 largest users (first 8 characters shown only); (weekly) active and new users per 7-day block from 08-07;
-- (retention) of users first seen in blocks 0..3, how many are active in a block at least 4 blocks after their first.
WITH s AS (
  SELECT day, IF(a = solver_cps, b, a) AS usr, usd, referral
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver`
  WHERE solver_cps IS NOT NULL AND day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015
),
u AS (
  SELECT usr, COUNT(*) AS fills, SUM(IFNULL(usd, 0)) AS vol, MIN(day) AS first_day, MAX(day) AS last_day,
         DIV(DATE_DIFF(MIN(day), DATE '2026-08-07', DAY), 7) AS first_blk
  FROM s GROUP BY usr
),
r AS (SELECT *, ROW_NUMBER() OVER (ORDER BY vol DESC, usr) AS rk, SUM(vol) OVER (ORDER BY vol DESC, usr ROWS UNBOUNDED PRECEDING) AS cum, SUM(vol) OVER () AS tot FROM u),
wk AS (SELECT usr, DIV(DATE_DIFF(day, DATE '2026-08-07', DAY), 7) AS blk FROM s GROUP BY 1, 2)
SELECT 'summary' AS part, '' AS k, CAST(COUNT(*) AS FLOAT64) AS x1, CAST(SUM(fills) AS FLOAT64) AS x2, SUM(vol) AS x3, NULL AS x4 FROM u
UNION ALL SELECT 'conc', CAST(n AS STRING), SUM(vol), NULL, NULL, NULL FROM r, UNNEST([1, 10, 100, 1000]) n WHERE rk <= n GROUP BY n
UNION ALL SELECT 'ge_100k', '', CAST(COUNTIF(vol >= 100000) AS FLOAT64), SUM(IF(vol >= 100000, vol, 0)), NULL, NULL FROM u
UNION ALL SELECT 'size', CASE WHEN vol < 100 THEN 'a_<100' WHEN vol < 1000 THEN 'b_100-1k' WHEN vol < 10000 THEN 'c_1k-10k' WHEN vol < 100000 THEN 'd_10k-100k' ELSE 'e_>=100k' END,
       CAST(COUNT(*) AS FLOAT64), SUM(vol), SUM(fills), NULL FROM u GROUP BY 2
UNION ALL SELECT 'top', SUBSTR(usr, 1, 8), vol, CAST(fills AS FLOAT64), CAST(DATE_DIFF(last_day, first_day, DAY) AS FLOAT64), CAST(rk AS FLOAT64) FROM r WHERE rk <= 10
UNION ALL SELECT 'weekly', CAST(blk AS STRING), CAST(COUNT(*) AS FLOAT64), CAST(COUNTIF(first_blk = blk) AS FLOAT64), NULL, NULL
FROM wk JOIN u USING (usr) GROUP BY blk
UNION ALL SELECT 'retention', 'first_blk_0_3', CAST(COUNT(DISTINCT u.usr) AS FLOAT64), CAST(COUNT(DISTINCT IF(wk.blk >= u.first_blk + 4, u.usr, NULL)) AS FLOAT64), NULL, NULL
FROM u JOIN wk USING (usr) WHERE u.first_blk <= 3
