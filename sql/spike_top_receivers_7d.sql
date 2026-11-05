-- Spike: top native-NEAR receivers over 7 days, to size the exchange-labelling problem.
-- Native transfers only (action_kind = TRANSFER), excluding gas refunds (predecessor = 'system').
WITH t AS (
  SELECT receipt_receiver_account_id AS receiver,
         receipt_predecessor_account_id AS sender,
         CAST(JSON_VALUE(args, '$.deposit') AS BIGNUMERIC) / 1e24 AS near
  FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
  WHERE block_date BETWEEN '2026-10-29' AND '2026-11-04'
    AND action_kind = 'TRANSFER'
    AND receipt_predecessor_account_id != 'system'
)
SELECT receiver,
       ROUND(SUM(near), 1) AS inflow_near,
       COUNT(*) AS n_transfers,
       COUNT(DISTINCT sender) AS n_senders,
       ROUND(SUM(near) / (SELECT SUM(near) FROM t) * 100, 3) AS share_pct
FROM t
GROUP BY receiver
ORDER BY inflow_near DESC
LIMIT 100
