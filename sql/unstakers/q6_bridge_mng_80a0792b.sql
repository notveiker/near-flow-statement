-- Q6: on 2026-09-11, 09-20 and 10-03, bridge-mng.near wrap/deposit lines and intents.near mt_mint lines for amounts of
-- ~100,000 or ~300,000 NEAR. Confirms that the three native transfers from top-50 #39's recipients
-- (1657182f..., d2ac944f..., 4cfa4a5f... -> bridge-mng.near) were deposited into intents.near, and which account was credited.
SELECT o.block_date, o.block_height, o.executor_account_id AS executor, SUBSTR(l.element, 1, 1500) AS element
FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o, UNNEST(o.logs.list) l
WHERE o.block_date IN ('2026-09-11', '2026-09-20', '2026-10-03')
  AND o.executor_account_id IN ('intents.near', 'wrap.near')
  AND (REGEXP_CONTAINS(l.element, r'^(Deposit|Transfer) (9999\d{25}|10000\d{25}|2999\d{26}|3000\d{26}) (NEAR to|from) bridge-mng\.near')
    OR (l.element LIKE '%"mt_mint"%' AND REGEXP_CONTAINS(l.element, r'"amounts":\["(9999\d{25}|10000\d{25}|2999\d{26}|3000\d{26})"\]')))
ORDER BY o.block_height
