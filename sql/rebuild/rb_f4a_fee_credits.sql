-- F4a. wNEAR (nep141:wrap.near) credited inside intents.near to the accounts that delivered native NEAR to the three revenue wallets,
-- by period, account group, credit channel and counterparty. Groups: 5880ad2b..., 143f2bb4..., 176121bd..., rest (all other delivering accounts).
-- Channels: mt_transfer (counterparty = sender), mt_mint (deposit), token_diff (positive diff, swap proceeds). Credits only.
WITH srcs AS (
  SELECT DISTINCT JSON_VALUE(d, '$.account_id') AS a
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
  WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015 AND event = 'native_withdraw'
    AND JSON_VALUE(d, '$.receiver_id') IN ('buybacks.multisignature.near', 'fefundsadmin.sputnik-dao.near', '1csfundsadmin.sputnik-dao.near')
),
c AS (
  SELECT day, 'mt_transfer' AS channel, JSON_VALUE(d, '$.new_owner_id') AS acct, JSON_VALUE(d, '$.old_owner_id') AS cp,
         (SELECT SUM(SAFE_CAST(JSON_VALUE_ARRAY(d, '$.amounts')[SAFE_OFFSET(i)] AS BIGNUMERIC)) FROM UNNEST(JSON_VALUE_ARRAY(d, '$.token_ids')) tid WITH OFFSET i WHERE tid = 'nep141:wrap.near') AS amt
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
  WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015 AND event = 'mt_transfer' AND d LIKE '%nep141:wrap.near%'
    AND JSON_VALUE(d, '$.new_owner_id') IN (SELECT a FROM srcs)
  UNION ALL
  SELECT day, 'mt_mint', JSON_VALUE(d, '$.owner_id'), '',
         (SELECT SUM(SAFE_CAST(JSON_VALUE_ARRAY(d, '$.amounts')[SAFE_OFFSET(i)] AS BIGNUMERIC)) FROM UNNEST(JSON_VALUE_ARRAY(d, '$.token_ids')) tid WITH OFFSET i WHERE tid = 'nep141:wrap.near')
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
  WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015 AND event = 'mt_mint' AND d LIKE '%nep141:wrap.near%'
    AND JSON_VALUE(d, '$.owner_id') IN (SELECT a FROM srcs)
  UNION ALL
  SELECT day, 'token_diff', JSON_VALUE(d, '$.account_id'), '', SAFE_CAST(JSON_VALUE(d, '$.diff."nep141:wrap.near"') AS BIGNUMERIC)
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
  WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015 AND event = 'token_diff' AND d LIKE '%nep141:wrap.near%'
    AND JSON_VALUE(d, '$.account_id') IN (SELECT a FROM srcs)
    AND SAFE_CAST(JSON_VALUE(d, '$.diff."nep141:wrap.near"') AS BIGNUMERIC) > 0
)
SELECT CASE WHEN day < '2026-08-19' THEN 'pre_0819' WHEN day < '2026-08-29' THEN 'mid_0819_0828' ELSE 'post_0829' END AS period,
       CASE WHEN acct LIKE '5880ad2b%' THEN '5880ad2b' WHEN acct LIKE '143f2bb4%' THEN '143f2bb4' WHEN acct LIKE '176121bd%' THEN '176121bd' ELSE 'rest' END AS grp,
       channel,
       CASE WHEN acct LIKE '5880ad2b%' OR acct LIKE '143f2bb4%' OR acct LIKE '176121bd%' OR cp IN ('51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe', 'solver-priv-liq.near', 'bridge-mng.near') THEN cp ELSE 'other' END AS cp,
       CAST(SUM(amt) AS STRING) AS yocto, COUNT(*) AS n
FROM c GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4
