-- F10 STAGE (second part). Transactions touching d6b77389... (the destination of the solver family's native withdrawals, F1): NEAR transfers
-- received and every action signed, window 2026-07-07..2026-11-04. Direct (transaction-level) flows only.
CREATE OR REPLACE TABLE `inlaid-backbone-501715-q6.nfs_rebuild.acct_d6b7` AS
SELECT block_date AS day, block_height AS h, transaction_hash AS tx, signer_account_id AS signer, receiver_account_id AS receiver,
       action_kind AS kind, transaction_status AS status, SAFE_CAST(REGEXP_EXTRACT(args, r'"deposit":"([0-9.]+) NEAR"') AS FLOAT64) AS near
FROM `bigquery-public-data.crypto_near_mainnet_us.transaction_actions`
WHERE block_date BETWEEN '2026-07-07' AND '2026-11-04' AND block_height <= 223088015
  AND ((receiver_account_id LIKE 'd6b77389%' AND action_kind = 'TRANSFER') OR signer_account_id LIKE 'd6b77389%')
