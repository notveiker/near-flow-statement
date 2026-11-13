-- Exploratory (written 2026-11-13, after the freeze). The brief's usage queries: daily transactions, daily
-- active accounts and active contracts, from the NEAR BigQuery public dataset, 2025-10-06..2026-11-04.
-- Per block_date:
--   n_tx                 transactions (every row of `transactions`)
--   n_signers            distinct transaction signers (what a relayer signs counts once, for the relayer)
--   n_signers_implicit   ... of which 64-hex implicit accounts
--   n_receivers          distinct transaction receivers
--   top10_signer_tx      transactions signed by that day's ten most active signers
--   top1_signer          that day's most active signer, and top1_signer_tx its transactions
-- Contract usage and meta-transaction users are in sql/usage_receipts.sql (fewer days: that table is larger).
WITH t AS (
  SELECT block_date AS day, signer_account_id AS s, receiver_account_id AS r
  FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
  WHERE block_date BETWEEN '2025-10-06' AND '2026-11-04'
),
per_signer AS (
  SELECT day, s, COUNT(*) AS n,
         ROW_NUMBER() OVER (PARTITION BY day ORDER BY COUNT(*) DESC, s) AS rk
  FROM t GROUP BY day, s
),
top AS (
  SELECT day,
         SUM(IF(rk <= 10, n, 0)) AS top10_signer_tx,
         MAX(IF(rk = 1, s, NULL)) AS top1_signer,
         MAX(IF(rk = 1, n, NULL)) AS top1_signer_tx,
         COUNT(*) AS n_signers,
         COUNTIF(REGEXP_CONTAINS(s, r'^[0-9a-f]{64}$')) AS n_signers_implicit
  FROM per_signer GROUP BY day
),
base AS (
  SELECT day, COUNT(*) AS n_tx, COUNT(DISTINCT r) AS n_receivers FROM t GROUP BY day
)
SELECT CAST(b.day AS STRING) AS day, b.n_tx, top.n_signers, top.n_signers_implicit, b.n_receivers,
       top.top10_signer_tx, top.top1_signer, top.top1_signer_tx
FROM base b JOIN top USING (day)
ORDER BY day
