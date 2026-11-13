-- Exploratory (written 2026-11-13, after the freeze). Contract usage and meta-transaction users, from
-- receipt_actions, on three spans: the 30 days to 2026-11-04, the same 30 days a year earlier, and
-- 2026-03-25..04-08 around the step in Nearblocks' daily transaction count.
-- Per block_date:
--   n_fc_receipts        FUNCTION_CALL actions
--   n_contracts_called   distinct accounts that received a FUNCTION_CALL (active contracts)
--   n_contracts_called_by_tx_signer  ... counting only calls whose predecessor is the transaction signer
--                        (direct calls by a user, not cross-contract calls)
--   n_delegate_actions   DELEGATE_ACTION receipts (meta-transactions sent by a relayer)
--   n_delegate_senders   distinct accounts on whose behalf a relayer sent one (the receipt's receiver)
--   n_users              distinct signers of any action receipt with is_delegate_action false and
--                        predecessor = signer, plus the delegate senders (an upper bound on accounts
--                        that acted that day, relayed or not)
WITH a AS (
  SELECT block_date AS day, action_kind AS k, receipt_receiver_account_id AS r,
         receipt_predecessor_account_id AS p, signer_account_id AS s
  FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
  WHERE block_date BETWEEN '2026-10-06' AND '2026-11-04'
     OR block_date BETWEEN '2025-10-06' AND '2025-11-04'
     OR block_date BETWEEN '2026-03-25' AND '2026-04-08'
),
users AS (
  SELECT day, s AS u FROM a WHERE p = s AND k != 'DELEGATE_ACTION'
  UNION DISTINCT
  SELECT day, r AS u FROM a WHERE k = 'DELEGATE_ACTION'
),
agg AS (
SELECT day,
       COUNTIF(k = 'FUNCTION_CALL') AS n_fc_receipts,
       COUNT(DISTINCT IF(k = 'FUNCTION_CALL', r, NULL)) AS n_contracts_called,
       COUNT(DISTINCT IF(k = 'FUNCTION_CALL' AND p = s, r, NULL)) AS n_contracts_called_by_tx_signer,
       COUNTIF(k = 'DELEGATE_ACTION') AS n_delegate_actions,
       COUNT(DISTINCT IF(k = 'DELEGATE_ACTION', r, NULL)) AS n_delegate_senders,
FROM a GROUP BY day
),
nu AS (SELECT day, COUNT(*) AS n_users FROM users GROUP BY day)
SELECT CAST(day AS STRING) AS day, agg.* EXCEPT (day), nu.n_users
FROM agg JOIN nu USING (day)
ORDER BY day
