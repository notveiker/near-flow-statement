-- F2b STAGE. wrap.near legacy log lines that name bridge-mng.near, window 2026-07-07..2026-11-04. One scan; later queries read this table.
-- Line shapes (from the one-day format probe rb_p0): "Deposit N NEAR to A", "Transfer N from A to B", "Refund N from A to B".
CREATE OR REPLACE TABLE `inlaid-backbone-501715-q6.nfs_rebuild.wrap_bridge` AS
SELECT x.block_date AS day, x.block_height AS h, x.receipt_id AS rid, l.element AS line
FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` x, UNNEST(x.logs.list) l
WHERE x.block_date BETWEEN '2026-07-07' AND '2026-11-04' AND x.block_height <= 223088015
  AND x.executor_account_id = 'wrap.near' AND x.status NOT LIKE '%FAIL%'
  AND l.element LIKE '%bridge-mng.near%'
