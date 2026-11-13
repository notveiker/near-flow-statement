-- F2b step 3. Direct NEAR transfers into bridge-mng.near by signer (successful transactions only), window totals and daily totals.
SELECT 'by_signer' AS part, CAST(NULL AS DATE) AS day, signer, SUM(near) AS near, COUNT(*) AS n
FROM `inlaid-backbone-501715-q6.nfs_rebuild.bridge_direct` WHERE status NOT LIKE '%FAIL%' GROUP BY 1, 3
UNION ALL
SELECT 'by_day', day, '', SUM(near), COUNT(*) FROM `inlaid-backbone-501715-q6.nfs_rebuild.bridge_direct` WHERE status NOT LIKE '%FAIL%' GROUP BY 1, 2
