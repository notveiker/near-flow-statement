-- RX8. Chain Signatures usage, direct calls counted exactly: transactions whose receiver is v1.signer, per UTC day, 2025-01-01..2026-11-04, with distinct signers.
-- (Requests that reach v1.signer through another contract's receipt are not in this table; the receipt-level count was priced at 4.7 TB and not run.)
SELECT block_date AS day, COUNT(*) AS tx, COUNT(DISTINCT signer_account_id) AS signers, COUNTIF(status LIKE '%FAIL%') AS failed
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date BETWEEN '2025-01-01' AND '2026-11-04' AND block_height <= 223088015 AND receiver_account_id = 'v1.signer'
GROUP BY 1 ORDER BY 1
