-- Q4. Where the chain-side volume is tagged: referral string on the swap legs (INFERRED to identify the front end),
-- whole window and daily for the 25 referrals with the most priced volume.
WITH top AS (
  SELECT IFNULL(referral, '(none)') AS r FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps` WHERE kind = 'simple'
  GROUP BY 1 ORDER BY SUM(IFNULL(usd, 0)) DESC LIMIT 25
)
SELECT day, IF(IFNULL(referral, '(none)') IN (SELECT r FROM top), IFNULL(referral, '(none)'), '(other)') AS referral,
       COUNT(*) AS n, COUNTIF(usd IS NOT NULL) AS priced, SUM(usd) AS usd
FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps`
WHERE kind = 'simple' AND day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015
GROUP BY 1, 2 ORDER BY 1, 2
