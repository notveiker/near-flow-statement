-- Q5: 2026-09-19..09-20, intents.near / wrap.near log lines with the 535,164.92 NEAR amount (yocto prefix 53516492),
-- the fresh account sheckwes.near paid (5cec4b8f...), or sheckwes.near. Checks whether bridge-mng.near deposited it
-- into intents.near and which intents account was credited / what happened next.
SELECT o.block_date, o.block_height, o.executor_account_id AS executor, SUBSTR(l.element, 1, 3000) AS element
FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o, UNNEST(o.logs.list) l
WHERE o.block_date BETWEEN '2026-09-19' AND '2026-09-20'
  AND o.executor_account_id IN ('intents.near', 'wrap.near')
  AND (l.element LIKE '%53516492%'
    OR l.element LIKE '%5cec4b8f928abc936e530049a8f266f6ba97dbf83d407d64dfe4cd3d7cbbd2f9%'
    OR l.element LIKE '%sheckwes.near%')
ORDER BY o.block_height
