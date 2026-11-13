-- Exploratory (written 2026-11-13, after the freeze). Who the daily transaction signers are, on the 30 days
-- to 2026-11-04, the same 30 days a year earlier, and 2026-03-30..04-03 around the step in the daily
-- transaction count. Signers are grouped by the last label of the account id (`.tg`, `.near`, `.sweat`, ...;
-- 64-hex implicit accounts as `implicit`, 0x-prefixed ones as `eth_implicit`), per day:
--   n_signers   distinct signers in the group, n_tx their transactions.
-- Also, for the five step days, the 15 signers with the most transactions (grp = 'top_signer:<account>').
WITH t AS (
  SELECT block_date AS day, signer_account_id AS s
  FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
  WHERE block_date BETWEEN '2026-10-06' AND '2026-11-04'
     OR block_date BETWEEN '2025-10-06' AND '2025-11-04'
     OR block_date BETWEEN '2026-03-30' AND '2026-04-03'
),
g AS (
  SELECT day, s,
    CASE WHEN REGEXP_CONTAINS(s, r'^[0-9a-f]{64}$') THEN 'implicit'
         WHEN STARTS_WITH(s, '0x') THEN 'eth_implicit'
         ELSE REGEXP_EXTRACT(s, r'\.([^.]+)$') END AS grp
  FROM t
),
by_group AS (
  SELECT CAST(day AS STRING) AS day, IFNULL(grp, '(no dot)') AS grp,
         COUNT(DISTINCT s) AS n_signers, COUNT(*) AS n_tx
  FROM g GROUP BY day, grp
),
top AS (
  SELECT CAST(day AS STRING) AS day, CONCAT('top_signer:', s) AS grp, 1 AS n_signers, n AS n_tx
  FROM (SELECT day, s, COUNT(*) AS n, ROW_NUMBER() OVER (PARTITION BY day ORDER BY COUNT(*) DESC, s) AS rk
        FROM t WHERE day BETWEEN '2026-03-30' AND '2026-04-03' GROUP BY day, s)
  WHERE rk <= 15
)
SELECT * FROM by_group WHERE n_signers >= 100 OR n_tx >= 10000
UNION ALL SELECT * FROM top
ORDER BY day, grp
