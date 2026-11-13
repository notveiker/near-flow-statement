-- Ask B(1). Per day, 2025-07-01..2026-11-04: transactions, distinct signers, distinct receivers (all transactions, any status).
SELECT block_date AS day, COUNT(*) AS tx, COUNT(DISTINCT signer_account_id) AS signers, COUNT(DISTINCT receiver_account_id) AS receivers
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date BETWEEN '2025-07-01' AND '2026-11-04' AND block_height <= 223088015
GROUP BY 1 ORDER BY 1
