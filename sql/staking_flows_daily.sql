-- Daily NEAR flows into and out of staking pools, from account_changes (balances, not call args).
-- A pool's total = staked + nonstaked balance. Each change is attributed by update_reason:
--   validator_accounts_update  -> epoch staking rewards credited to the pool
--   action_receipt_gas_reward  -> 30% gas rebate to the pool contract (removed at protocol v87)
--   receipt_processing         -> deposits in minus withdrawals out (delegator flows) and the pool's own gas
-- Pools: *.poolv1.near and *.pool.near. Liquid-staking contracts (meta-pool.near, linear-protocol.near)
-- are excluded because they stake through these pools; including them would double count.
-- Window: 2026-08-07 .. 2026-11-04 (90 days, PREREG H1a); 2026-08-06 seeds the first delta.
WITH ch AS (
  SELECT block_date, affected_account_id AS acct, block_height, index_in_block, update_reason,
         (affected_account_staked_balance + affected_account_nonstaked_balance) / 1e24 AS total
  FROM `bigquery-public-data.crypto_near_mainnet_us.account_changes`
  WHERE block_date BETWEEN '2026-08-06' AND '2026-11-04'
    AND (affected_account_id LIKE '%.poolv1.near' OR affected_account_id LIKE '%.pool.near')
),
d AS (
  SELECT *, total - LAG(total) OVER (PARTITION BY acct ORDER BY block_height, index_in_block) AS delta
  FROM ch
)
SELECT block_date,
       ROUND(SUM(IF(update_reason = 'validator_accounts_update', delta, 0)), 3) AS rewards_near,
       ROUND(SUM(IF(update_reason = 'action_receipt_gas_reward', delta, 0)), 3) AS gas_rebate_near,
       ROUND(SUM(IF(update_reason = 'receipt_processing' AND delta > 0, delta, 0)), 3) AS inflow_near,
       ROUND(SUM(IF(update_reason = 'receipt_processing' AND delta < 0, -delta, 0)), 3) AS outflow_near,
       COUNT(DISTINCT acct) AS pools
FROM d
WHERE block_date >= '2026-08-07' AND delta IS NOT NULL
GROUP BY block_date
ORDER BY block_date
