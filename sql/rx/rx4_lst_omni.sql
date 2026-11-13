-- RX4. Who sends Intents wNEAR to lst-pool.near and omni.bridge.near (2026-07-07..2026-11-04): withdrawal events on intents.near naming either as receiver, with the Intents account that
-- initiated them, by month, token and amount. Only withdrawals of nep141:wrap.near are read (ft_withdraw/mt_withdraw/native paths are tried in turn by event name).
SELECT FORMAT_DATE('%Y-%m', day) AS month, event, JSON_VALUE(d, '$.receiver_id') AS receiver, JSON_VALUE(d, '$.account_id') AS src,
       COALESCE(JSON_VALUE(d, '$.token'), JSON_VALUE(d, '$.token_ids[0]')) AS token,
       CAST(SUM(SAFE_CAST(JSON_VALUE(d, '$.amount') AS BIGNUMERIC)) AS STRING) AS yocto, COUNT(*) AS n
FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015
  AND event IN ('ft_withdraw', 'mt_withdraw', 'native_withdraw', 'nft_withdraw')
  AND JSON_VALUE(d, '$.receiver_id') IN ('lst-pool.near', 'omni.bridge.near')
GROUP BY 1, 2, 3, 4, 5
