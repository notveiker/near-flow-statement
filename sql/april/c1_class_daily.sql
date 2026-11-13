-- Class C (docs/history-class-adjusted-method.md) counted exactly on the full chain: per day, transactions by part and in total, 2023-01-01..2026-11-04.
-- Parts: signer hotwallet.kaiching; signer sweat-migration.near; signer users.kaiching; other transactions whose receiver ends in .users.kaiching.
SELECT block_date AS day,
       COUNTIF(signer_account_id = 'hotwallet.kaiching') AS tx_hotwallet,
       COUNTIF(signer_account_id = 'sweat-migration.near') AS tx_sweat,
       COUNTIF(signer_account_id = 'users.kaiching') AS tx_users_signer,
       COUNTIF(signer_account_id NOT IN ('hotwallet.kaiching', 'sweat-migration.near', 'users.kaiching') AND ENDS_WITH(receiver_account_id, '.users.kaiching')) AS tx_recv_family,
       COUNT(*) AS tx
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date BETWEEN '2023-01-01' AND '2026-11-04' AND block_height <= 223088015
GROUP BY 1 ORDER BY 1
