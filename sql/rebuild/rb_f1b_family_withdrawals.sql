-- F1. wNEAR leaving the solver family to the outside: mt_burn of wrap.near by a family account (all withdrawals burn),
-- plus the receiver of the matching ft_withdraw / native_withdraw events (family account, wrap.near or native NEAR).
WITH fam AS (SELECT * FROM UNNEST(['solver-priv-liq.near', 'solver-multichain-asset.near', 'solver-multichain-asset-escrow.near', 'solver-multichain-asset-2.near']) AS a)
SELECT day, event, JSON_VALUE(d, '$.account_id') AS account_id, JSON_VALUE(d, '$.owner_id') AS owner_id, JSON_VALUE(d, '$.receiver_id') AS receiver_id,
       JSON_VALUE(d, '$.token') AS token,
       CAST(SUM(IFNULL(SAFE_CAST(JSON_VALUE(d, '$.amount') AS BIGNUMERIC),
         (SELECT SUM(SAFE_CAST(JSON_VALUE_ARRAY(d, '$.amounts')[SAFE_OFFSET(i)] AS BIGNUMERIC))
            FROM UNNEST(JSON_VALUE_ARRAY(d, '$.token_ids')) tid WITH OFFSET i WHERE tid = 'nep141:wrap.near'))) AS STRING) AS yocto,
       COUNT(*) AS n
FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015
  AND event IN ('mt_burn', 'ft_withdraw', 'native_withdraw')
  AND (JSON_VALUE(d, '$.owner_id') IN (SELECT a FROM fam) OR JSON_VALUE(d, '$.account_id') IN (SELECT a FROM fam))
  AND (d LIKE '%wrap.near%' OR event = 'native_withdraw')
GROUP BY 1, 2, 3, 4, 5, 6 ORDER BY 1, 2, 3, 4, 5
