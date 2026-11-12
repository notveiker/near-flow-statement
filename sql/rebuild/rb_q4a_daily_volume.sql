-- Q4. Chain-side daily swap counts and priced volume (simple swaps only; complex receipts counted, never valued).
SELECT day,
       COUNTIF(kind = 'simple') AS n_simple, COUNTIF(kind = 'simple' AND usd IS NOT NULL) AS n_priced,
       SUM(IF(kind = 'simple', usd, 0)) AS usd_all, SUM(IF(basis = 'stable', usd, 0)) AS usd_stable, SUM(IF(basis = 'major', usd, 0)) AS usd_major,
       COUNTIF(kind = 'complex') AS n_complex, SUM(IF(kind = 'complex', n_legs, 0)) AS legs_complex
FROM `inlaid-backbone-501715-q6.nfs_rebuild.swaps`
WHERE day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015
GROUP BY 1 ORDER BY 1
