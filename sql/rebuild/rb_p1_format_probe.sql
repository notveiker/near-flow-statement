-- P1. Format probe only (not a result): shape of transaction_actions rows with receiver bridge-mng.near on one day (2026-10-01), five rows.
SELECT action_kind, signer_account_id, SUBSTR(args, 1, 300) AS args_head
FROM `bigquery-public-data.crypto_near_mainnet_us.transaction_actions`
WHERE block_date = '2026-10-01' AND block_height <= 223088015 AND receiver_account_id = 'bridge-mng.near'
LIMIT 5
