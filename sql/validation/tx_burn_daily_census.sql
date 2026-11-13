-- Sampler validation, burn part: NEAR burnt when a transaction is converted to its first receipt (the sampler counts it in tokens_burnt of the transaction outcome),
-- per UTC day, 2025-01-01..2026-09-30. Units: the table's receipt_conversion_tokens_burnt (yocto, float) / 1e24.
SELECT block_date AS day, SUM(receipt_conversion_tokens_burnt) / 1e24 AS tx_burnt_near
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date BETWEEN '2025-01-01' AND '2026-09-30' AND block_height <= 223088015
GROUP BY 1 ORDER BY 1
