-- wNEAR (wrap.near) arriving at NEAR's Intents revenue wallets from outside the wallet set,
-- per day, wallet and counterparty. The token half of DefiLlama's `moves` CTE. Fee switch to 2026-11-04.
WITH w AS (
  SELECT * FROM UNNEST(['fefundsadmin.sputnik-dao.near', '1csfundsadmin.sputnik-dao.near',
                        'buybacks.multisignature.near']) AS wallet
)
SELECT block_date AS day, affected_account_id AS wallet, involved_account_id AS sender,
       ROUND(SUM(CAST(delta_amount AS BIGNUMERIC) / 1e24), 4) AS near, COUNT(*) AS n
FROM `bigquery-public-data.crypto_near_mainnet_us.ft_events`
WHERE block_date BETWEEN '2026-02-23' AND '2026-11-04'
  AND contract_account_id = 'wrap.near'
  AND affected_account_id IN (SELECT wallet FROM w)
  AND CAST(delta_amount AS BIGNUMERIC) > 0
  AND (involved_account_id IS NULL OR involved_account_id NOT IN (SELECT wallet FROM w))
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
