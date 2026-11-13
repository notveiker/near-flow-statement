-- Sampler validation against the full chain (docs/history-sample-validation.md): transactions per UTC day, every day from the first block to the cutoff.
SELECT block_date AS day, COUNT(*) AS tx
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date BETWEEN '2020-07-21' AND '2026-11-04' AND block_height <= 223088015
GROUP BY 1 ORDER BY 1
