-- Q1 (senders). Escrow wNEAR deposits made by mt_mint (the public deposit path), with the transaction signer.
SELECT m.day, m.signer, m.tx_receiver,
       CAST(SUM((SELECT SUM(SAFE_CAST(JSON_VALUE_ARRAY(m.d, '$.amounts')[SAFE_OFFSET(i)] AS BIGNUMERIC))
                  FROM UNNEST(JSON_VALUE_ARRAY(m.d, '$.token_ids')) tid WITH OFFSET i WHERE tid = 'nep141:wrap.near')) AS STRING) AS yocto,
       COUNT(*) AS n
FROM `inlaid-backbone-501715-q6.nfs_rebuild.mint_origin` m
WHERE m.day BETWEEN '2026-07-07' AND '2026-11-04' AND m.h <= 223088015
  AND JSON_VALUE(m.d, '$.owner_id') = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe'
  AND m.d LIKE '%nep141:wrap.near%'
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
