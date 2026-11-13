-- F10. Flows of d6b77389...: inflows by sender, outflows by receiver and action kind (successful transactions).
SELECT 'in_by_sender' AS part, signer AS a, '' AS kind, SUM(near) AS near, COUNT(*) AS n
FROM `inlaid-backbone-501715-q6.nfs_rebuild.acct_d6b7` WHERE receiver LIKE 'd6b77389%' AND kind = 'TRANSFER' AND status NOT LIKE '%FAIL%' GROUP BY 1, 2, 3
UNION ALL
SELECT 'out_by_receiver', receiver, kind, SUM(near), COUNT(*)
FROM `inlaid-backbone-501715-q6.nfs_rebuild.acct_d6b7` WHERE signer LIKE 'd6b77389%' AND status NOT LIKE '%FAIL%' GROUP BY 1, 2, 3
