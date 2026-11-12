-- F2. wNEAR movements of bridge-mng.near (the signer of the family's external deposits, F1) from ft_events:
-- by month, counterparty (involved account), cause and direction. Transfers only; no balance is read.
SELECT FORMAT_DATE('%Y-%m', block_date) AS month, involved_account_id AS cp, cause,
       IF(CAST(delta_amount AS BIGNUMERIC) > 0, 'in', 'out') AS dir,
       CAST(SUM(ABS(CAST(delta_amount AS BIGNUMERIC))) AS STRING) AS yocto, COUNT(*) AS n
FROM `bigquery-public-data.crypto_near_mainnet_us.ft_events`
WHERE block_date BETWEEN '2026-07-07' AND '2026-11-04' AND block_height <= 223088015
  AND contract_account_id = 'wrap.near' AND affected_account_id = 'bridge-mng.near'
GROUP BY 1, 2, 3, 4 ORDER BY 1, 5 DESC
