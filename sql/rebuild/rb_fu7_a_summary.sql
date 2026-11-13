-- F7. Flows of 1244d552...: inflows by sender, outflows by receiver and action kind, daily totals (successful transactions).
SELECT 'in_by_sender' AS part, CAST(NULL AS DATE) AS day, signer AS a, '' AS kind, SUM(near) AS near, COUNT(*) AS n
FROM `inlaid-backbone-501715-q6.nfs_rebuild.acct_1244`
WHERE receiver = '1244d552459d7230bdaf267c1d09a296282dc85251958434e670d9b9d561fac7' AND kind = 'TRANSFER' AND status NOT LIKE '%FAIL%' GROUP BY 1, 3, 4
UNION ALL
SELECT 'out_by_receiver', CAST(NULL AS DATE), receiver, kind, SUM(near), COUNT(*)
FROM `inlaid-backbone-501715-q6.nfs_rebuild.acct_1244`
WHERE signer = '1244d552459d7230bdaf267c1d09a296282dc85251958434e670d9b9d561fac7' AND status NOT LIKE '%FAIL%' GROUP BY 1, 3, 4
UNION ALL
SELECT 'out_by_day', day, '', '', SUM(near), COUNT(*)
FROM `inlaid-backbone-501715-q6.nfs_rebuild.acct_1244`
WHERE signer = '1244d552459d7230bdaf267c1d09a296282dc85251958434e670d9b9d561fac7' AND receiver = 'bridge-mng.near' AND status NOT LIKE '%FAIL%' GROUP BY 1, 2
