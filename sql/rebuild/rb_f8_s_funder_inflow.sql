-- F8 STAGE. Direct NEAR transfers received by every direct funder of bridge-mng.near (F2b step 3, table bridge_direct), window 2026-07-07..2026-11-04.
-- One hop upstream of the deposit path. Direct (transaction-level) transfers only.
CREATE OR REPLACE TABLE `inlaid-backbone-501715-q6.nfs_rebuild.funder_inflow` AS
SELECT block_date AS day, transaction_hash AS tx, signer_account_id AS sender, receiver_account_id AS funder, transaction_status AS status,
       SAFE_CAST(REGEXP_EXTRACT(args, r'"deposit":"([0-9.]+) NEAR"') AS FLOAT64) AS near
FROM `bigquery-public-data.crypto_near_mainnet_us.transaction_actions`
WHERE block_date BETWEEN '2026-07-07' AND '2026-11-04' AND block_height <= 223088015
  AND action_kind = 'TRANSFER'
  AND receiver_account_id IN (SELECT DISTINCT signer FROM `inlaid-backbone-501715-q6.nfs_rebuild.bridge_direct`)
