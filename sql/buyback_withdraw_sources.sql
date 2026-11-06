-- Which intents.near accounts deliver native NEAR to NEAR's revenue wallets (dip4 native_withdraw
-- events), 2026-10-06..11-04, per day, source account and wallet. Recurring sources are fee
-- collectors; single-use sources are fresh accounts that receive NEAR unshielded from the Confidential Intents
-- treasury (PRIVATE_TREASURY_ACCOUNT_ID 51e8f94d...7cbe, docs.near-intents.org) and withdraw it.
SELECT o.block_date AS day,
       JSON_VALUE(d, '$.account_id') AS src,
       JSON_VALUE(d, '$.receiver_id') AS wallet,
       COUNT(*) AS n,
       CAST(SUM(CAST(JSON_VALUE(d, '$.amount') AS BIGNUMERIC)) / 1e24 AS STRING) AS near
FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o, UNNEST(o.logs.list) l,
  UNNEST(JSON_QUERY_ARRAY(SUBSTR(l.element, 12), '$.data')) d
WHERE o.block_date BETWEEN '2026-10-06' AND '2026-11-04'
  AND o.executor_account_id = 'intents.near'
  AND l.element LIKE 'EVENT_JSON:%native_withdraw%'
  AND JSON_VALUE(d, '$.receiver_id') IN ('buybacks.multisignature.near', 'fefundsadmin.sputnik-dao.near',
                                         '1csfundsadmin.sputnik-dao.near')
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
