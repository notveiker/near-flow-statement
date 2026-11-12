-- F3. Daily anchored complex receipts and their priced volume, beside the simple-swap series (Q4a).
SELECT day, COUNTIF(anchored) AS n_anchored, COUNTIF(anchored AND usd IS NOT NULL) AS n_priced,
       SUM(IF(anchored, usd, 0)) AS usd_anchored, COUNTIF(NOT anchored) AS n_unanchored
FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps_complex`
WHERE day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015
GROUP BY 1 ORDER BY 1
