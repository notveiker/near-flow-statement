-- F7 STAGE. Transactions touching 1244d552... (the top direct funder of bridge-mng.near, F2b): NEAR transfers it receives and every
-- transaction action it signs, window 2026-07-07..2026-11-04. Direct (transaction-level) flows only; contract-originated transfers are not here.
CREATE OR REPLACE TABLE `inlaid-backbone-501715-q6.nfs_rebuild.acct_1244` AS
SELECT block_date AS day, block_height AS h, transaction_hash AS tx, signer_account_id AS signer, receiver_account_id AS receiver,
       action_kind AS kind, transaction_status AS status, SAFE_CAST(REGEXP_EXTRACT(args, r'"deposit":"([0-9.]+) NEAR"') AS FLOAT64) AS near
FROM `bigquery-public-data.crypto_near_mainnet_us.transaction_actions`
WHERE block_date BETWEEN '2026-07-07' AND '2026-11-04' AND block_height <= 223088015
  AND ((receiver_account_id = '1244d552459d7230bdaf267c1d09a296282dc85251958434e670d9b9d561fac7' AND action_kind = 'TRANSFER')
    OR signer_account_id = '1244d552459d7230bdaf267c1d09a296282dc85251958434e670d9b9d561fac7')
