-- F1. External wNEAR deposits into the solver family (mt_mint of nep141:wrap.near to a family account), by day, depositor
-- (transaction signer) and the transaction's receiver. Family = solver-priv-liq.near, solver-multichain-asset.near,
-- solver-multichain-asset-escrow.near, solver-multichain-asset-2.near (the accounts the escrow trades with most, Q3).
SELECT m.day, JSON_VALUE(m.d, '$.owner_id') AS owner, m.signer, m.tx_receiver,
       CAST(SUM((SELECT SUM(SAFE_CAST(JSON_VALUE_ARRAY(m.d, '$.amounts')[SAFE_OFFSET(i)] AS BIGNUMERIC))
                  FROM UNNEST(JSON_VALUE_ARRAY(m.d, '$.token_ids')) tid WITH OFFSET i WHERE tid = 'nep141:wrap.near')) AS STRING) AS yocto,
       COUNT(*) AS n
FROM `inlaid-backbone-501715-q6.nfs_rebuild.mint_origin` m
WHERE m.day BETWEEN '2026-07-07' AND '2026-11-04' AND m.h <= 223088015
  AND JSON_VALUE(m.d, '$.owner_id') IN ('solver-priv-liq.near', 'solver-multichain-asset.near', 'solver-multichain-asset-escrow.near', 'solver-multichain-asset-2.near')
  AND m.d LIKE '%nep141:wrap.near%'
GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4
