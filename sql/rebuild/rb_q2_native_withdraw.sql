-- Q2. NEAR delivered to the three revenue wallets by intents.near native_withdraw events, per day, source account
-- and wallet, for the whole window (the 2026-10-06 query covered only the last 30 days). Transfers TO the wallets only;
-- no balance of any wallet is read.
SELECT day, JSON_VALUE(d, '$.account_id') AS src, JSON_VALUE(d, '$.receiver_id') AS wallet,
       CAST(SUM(CAST(JSON_VALUE(d, '$.amount') AS BIGNUMERIC)) AS STRING) AS yocto, COUNT(*) AS n
FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015
  AND event = 'native_withdraw'
  AND JSON_VALUE(d, '$.receiver_id') IN ('buybacks.multisignature.near', 'fefundsadmin.sputnik-dao.near', '1csfundsadmin.sputnik-dao.near')
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
