-- F9. Daily wNEAR (nep141:wrap.near) paid by solver accounts to the persistent fee accounts 5880ad2b..., 143f2bb4..., 176121bd... (mt_transfer), by payer.
SELECT day, JSON_VALUE(d, '$.old_owner_id') AS payer,
       CAST(SUM((SELECT SUM(SAFE_CAST(JSON_VALUE_ARRAY(d, '$.amounts')[SAFE_OFFSET(i)] AS BIGNUMERIC)) FROM UNNEST(JSON_VALUE_ARRAY(d, '$.token_ids')) tid WITH OFFSET i WHERE tid = 'nep141:wrap.near')) AS STRING) AS yocto,
       COUNT(*) AS n
FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
WHERE day BETWEEN '2026-08-07' AND '2026-11-04' AND h <= 223088015 AND event = 'mt_transfer' AND d LIKE '%nep141:wrap.near%'
  AND (JSON_VALUE(d, '$.new_owner_id') LIKE '5880ad2b%' OR JSON_VALUE(d, '$.new_owner_id') LIKE '143f2bb4%' OR JSON_VALUE(d, '$.new_owner_id') LIKE '176121bd%')
  AND JSON_VALUE(d, '$.old_owner_id') IN ('blockzen-1-main.near', 'crux-solver.near', 'solver-priv-liq.near')
GROUP BY 1, 2 ORDER BY 1, 2
