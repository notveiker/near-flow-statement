-- F2b STEP 3 STAGE (triggered: intents withdrawals explain under 80% of the wrapped NEAR). Direct NEAR transfers whose receiver is
-- bridge-mng.near, window 2026-07-07..2026-11-04. args format fixed by the one-day probe rb_p1: {"deposit":"0.281 NEAR"}.
CREATE OR REPLACE TABLE `inlaid-backbone-501715-q6.nfs_rebuild.bridge_direct` AS
SELECT block_date AS day, block_height AS h, transaction_hash AS tx, signer_account_id AS signer, transaction_status AS status,
       SAFE_CAST(REGEXP_EXTRACT(args, r'"deposit":"([0-9.]+) NEAR"') AS FLOAT64) AS near
FROM `bigquery-public-data.crypto_near_mainnet_us.transaction_actions`
WHERE block_date BETWEEN '2026-07-07' AND '2026-11-04' AND block_height <= 223088015
  AND receiver_account_id = 'bridge-mng.near' AND action_kind = 'TRANSFER'
