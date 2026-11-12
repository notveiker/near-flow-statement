-- STAGE 3. Solver side of each simple swap, INFERRED: the participant with more distinct counterparties across all
-- simple swaps in the window (sensitivity: more fills). Ties leave the solver NULL (unclassified).
CREATE OR REPLACE TABLE `inlaid-backbone-501715-q6.nfs_rebuild.swaps_solver` AS
WITH s AS (SELECT * FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps` WHERE kind = 'simple'),
e AS (SELECT a AS x, b AS y FROM s UNION ALL SELECT b, a FROM s),
deg AS (SELECT x AS acct, COUNT(DISTINCT y) AS cps, COUNT(*) AS fills FROM e GROUP BY 1)
SELECT s.rid, s.day, s.h, s.a, s.b, s.referral, s.usd, s.basis,
       da.cps AS cps_a, db.cps AS cps_b, da.fills AS fills_a, db.fills AS fills_b,
       CASE WHEN da.cps > db.cps THEN s.a WHEN db.cps > da.cps THEN s.b END AS solver_cps,
       CASE WHEN da.fills > db.fills THEN s.a WHEN db.fills > da.fills THEN s.b END AS solver_fills
FROM s JOIN deg da ON da.acct = s.a JOIN deg db ON db.acct = s.b
