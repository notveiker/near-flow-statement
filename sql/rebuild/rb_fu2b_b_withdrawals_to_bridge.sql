-- F2b-b. Every intents.near withdrawal event that names bridge-mng.near as receiver (any withdrawal event type), by day, event, source account,
-- token and amount; and, for context, the top 25 receivers of native_withdraw over the window. Transfers TO accounts only; no balance read.
WITH w AS (
  SELECT day, event, JSON_VALUE(d, '$.account_id') AS src, JSON_VALUE(d, '$.receiver_id') AS receiver,
         COALESCE(JSON_VALUE(d, '$.token'), 'native') AS token, SAFE_CAST(JSON_VALUE(d, '$.amount') AS BIGNUMERIC) AS amt
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
  WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015
    AND event IN ('native_withdraw', 'ft_withdraw', 'mt_withdraw', 'nft_withdraw')
)
SELECT 'to_bridge' AS part, day, event, src, receiver, token, CAST(SUM(amt) AS STRING) AS yocto, COUNT(*) AS n
FROM w WHERE receiver = 'bridge-mng.near' GROUP BY 1, 2, 3, 4, 5, 6
UNION ALL
SELECT 'top_native_receivers', CAST(NULL AS DATE), event, CAST(NULL AS STRING), receiver, token, CAST(SUM(amt) AS STRING), COUNT(*)
FROM w WHERE event = 'native_withdraw' GROUP BY 1, 3, 5, 6 QUALIFY ROW_NUMBER() OVER (ORDER BY SUM(amt) DESC) <= 25
