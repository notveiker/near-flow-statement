-- Sanity check for staking_flows_daily: total NEAR held by staking pools at the end of
-- {SEED} and of {END} (last balance change of each pool on that day).
-- Expected: end - start = rewards + gas rebate + inflow - outflow from staking_flows_daily.
WITH last_state AS (
  SELECT block_date, affected_account_id AS acct,
         (affected_account_staked_balance + affected_account_nonstaked_balance) / 1e24 AS total,
         affected_account_staked_balance / 1e24 AS staked,
         ROW_NUMBER() OVER (PARTITION BY block_date, affected_account_id
                            ORDER BY block_height DESC, index_in_block DESC) AS rn
  FROM `bigquery-public-data.crypto_near_mainnet_us.account_changes`
  WHERE block_date IN ('{SEED}', '{END}') AND block_height <= 223088015
    AND (affected_account_id LIKE '%.poolv1.near' OR affected_account_id LIKE '%.pool.near')
)
SELECT block_date, COUNT(*) AS pools, ROUND(SUM(total), 0) AS pool_total_near, ROUND(SUM(staked), 0) AS pool_staked_near
FROM last_state WHERE rn = 1
GROUP BY block_date ORDER BY block_date
