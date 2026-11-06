-- Token inflows to the two intents.near accounts that withdraw NEAR to buybacks.multisignature.near
-- on a recurring basis (identified from native_withdraw events, 2026-10-06..11-04):
--   5880ad2b... ("collector A"): receives the explicit buyback appFee on each 1Click swap
--   143f2bb4... ("collector B"): receives a variable share consistent with quote-improvement sharing
-- Per day, collector and token: summed raw amounts (token base units) and transfer counts.
WITH c AS (
  SELECT * FROM UNNEST(['5880ad2b362620fadf759cbceb1cd5737ce8c6ed7fb8e9942881e6731f9247dd',
                        '143f2bb439575c286f4f585163f0e5fb4e464f8ce57ec06ae80741407d3cfb31']) AS acct
),
t AS (
  SELECT o.block_date AS day, JSON_VALUE(d, '$.receiver_id') AS collector, JSON_QUERY(d, '$.tokens') AS tokens
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o, UNNEST(o.logs.list) l,
    UNNEST(JSON_QUERY_ARRAY(SUBSTR(l.element, 12), '$.data')) d
  WHERE o.block_date BETWEEN '2026-10-06' AND '2026-11-04'
    AND o.executor_account_id = 'intents.near'
    AND l.element LIKE 'EVENT_JSON:{"standard":"dip4"%"event":"transfer"%'
    AND (l.element LIKE '%"receiver_id":"5880ad2b362620fadf759cbceb1cd5737ce8c6ed7fb8e9942881e6731f9247dd"%'
      OR l.element LIKE '%"receiver_id":"143f2bb439575c286f4f585163f0e5fb4e464f8ce57ec06ae80741407d3cfb31"%')
)
SELECT day, collector, REGEXP_EXTRACT(kv, r'^"([^"]+)"') AS token,
       CAST(SUM(CAST(REGEXP_EXTRACT(kv, r':"([0-9]+)"$') AS BIGNUMERIC)) AS STRING) AS amount,
       COUNT(*) AS n
FROM t, UNNEST(REGEXP_EXTRACT_ALL(tokens, r'"[^"]+":"[0-9]+"')) AS kv
WHERE collector IN (SELECT acct FROM c)
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
