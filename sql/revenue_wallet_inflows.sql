-- NEAR's Intents revenue wallets: native NEAR arriving from outside the wallet set, per day,
-- wallet and sender. Mirrors the `moves` CTE of DefiLlama's near-intents adapter (native part;
-- wNEAR inflows are checked separately). Window: the 30 days of the Explorer pull, 2026-10-06 to 2026-11-04 (a since-switch window scans ~890 GB).
WITH w AS (
  SELECT * FROM UNNEST(['fefundsadmin.sputnik-dao.near', '1csfundsadmin.sputnik-dao.near',
                        'buybacks.multisignature.near']) AS wallet
)
SELECT block_date AS day,
       receipt_receiver_account_id AS wallet,
       receipt_predecessor_account_id AS sender,
       ROUND(SUM(CAST(JSON_VALUE(args, '$.deposit') AS BIGNUMERIC) / 1e24), 4) AS near,
       COUNT(*) AS n
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date BETWEEN '2026-10-06' AND '2026-11-04'
  AND action_kind = 'TRANSFER'
  AND receipt_receiver_account_id IN (SELECT wallet FROM w)
  AND receipt_predecessor_account_id NOT IN (SELECT wallet FROM w)
  AND receipt_predecessor_account_id != 'system'
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
