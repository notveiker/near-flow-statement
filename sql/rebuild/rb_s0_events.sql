-- STAGE 0. One scan of intents.near EVENT_JSON logs for the window, flattened to one row per event data element.
-- Window 2026-07-07..2026-11-04, cutoff block 223,088,015 (the pre-registered data cutoff). Failed receipts dropped
-- (status containing FAIL, as in the 2026-11-06 H1b method).
CREATE OR REPLACE TABLE `inlaid-backbone-501715-q6.nfs_rebuild.intents_events` AS
SELECT o.day, o.h, o.rid,
       JSON_VALUE(o.e, '$.standard') AS std, JSON_VALUE(o.e, '$.event') AS event, TO_JSON_STRING(d) AS d
FROM (
  SELECT x.block_date AS day, x.block_height AS h, x.receipt_id AS rid, SAFE.PARSE_JSON(SUBSTR(l.element, 12)) AS e
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` x, UNNEST(x.logs.list) l
  WHERE x.block_date BETWEEN '2026-07-07' AND '2026-11-04'
    AND x.block_height <= 223088015
    AND x.executor_account_id = 'intents.near'
    AND x.status NOT LIKE '%FAIL%'
    AND l.element LIKE 'EVENT_JSON:%'
) o, UNNEST(JSON_QUERY_ARRAY(o.e, '$.data')) d
