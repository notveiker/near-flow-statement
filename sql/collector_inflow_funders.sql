-- Exploratory (written 2026-11-12, after the freeze). Who funded the fees that reached NEAR's two fee collectors
-- (collector A 5880ad2b..., collector B 143f2bb4..., see sql/collector_inflows.sql), 2026-10-06..11-04.
-- Every dip4 transfer into A or B is classified by its sender (account_id):
--   escrow_direct  sender is the Confidential Intents treasury (PRIVATE_TREASURY_ACCOUNT_ID 51e8f94d...7cbe)
--   escrow_funded  sender received a dip4 transfer from that treasury between 2026-09-22 and the transfer's block
--   public_swap    otherwise, and the same receipt emits a dip4 token_diff for the sender (a public swap intent)
--   other          none of the above
-- Per day, collector, class and token: summed raw amounts, transfer count, distinct senders. Summed over class,
-- the rows equal data/raw/bq/collector_inflows.json.
WITH ev AS (
  SELECT o.block_date AS day, o.block_height AS h, o.receipt_id AS rid,
         l.element AS el
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o, UNNEST(o.logs.list) l
  WHERE o.block_date BETWEEN '2026-09-22' AND '2026-11-04'
    AND o.executor_account_id = 'intents.near'
    AND l.element LIKE 'EVENT_JSON:{"standard":"dip4"%'
    AND (l.element LIKE '%"event":"transfer"%' OR l.element LIKE '%"event":"token_diff"%')
),
rows_ AS (
  SELECT day, h, rid,
         REGEXP_EXTRACT(el, r'"event":"([a-z_]+)"') AS event,
         JSON_VALUE(d, '$.account_id') AS sender, JSON_VALUE(d, '$.receiver_id') AS receiver,
         JSON_QUERY(d, '$.tokens') AS tokens
  FROM ev, UNNEST(JSON_QUERY_ARRAY(SUBSTR(el, 12), '$.data')) d
),
funded AS (  -- first escrow funding of each account
  SELECT receiver AS acct, MIN(h) AS first_h
  FROM rows_ WHERE event = 'transfer' AND sender = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe' GROUP BY receiver
),
diffs AS (SELECT DISTINCT rid, sender FROM rows_ WHERE event = 'token_diff'),
inflow AS (
  SELECT r.day, r.receiver AS collector, r.sender, r.tokens,
         CASE WHEN r.sender = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe' THEN 'escrow_direct'
              WHEN f.first_h IS NOT NULL AND f.first_h <= r.h THEN 'escrow_funded'
              WHEN dd.rid IS NOT NULL THEN 'public_swap'
              ELSE 'other' END AS class
  FROM rows_ r
  LEFT JOIN funded f ON f.acct = r.sender
  LEFT JOIN diffs dd ON dd.rid = r.rid AND dd.sender = r.sender
  WHERE r.event = 'transfer' AND r.day >= '2026-10-06'
    AND r.receiver IN ('5880ad2b362620fadf759cbceb1cd5737ce8c6ed7fb8e9942881e6731f9247dd',
                       '143f2bb439575c286f4f585163f0e5fb4e464f8ce57ec06ae80741407d3cfb31')
)
SELECT day, collector, class, REGEXP_EXTRACT(kv, r'^"([^"]+)"') AS token,
       CAST(SUM(CAST(REGEXP_EXTRACT(kv, r':"([0-9]+)"$') AS BIGNUMERIC)) AS STRING) AS amount,
       COUNT(*) AS n, COUNT(DISTINCT sender) AS senders
FROM inflow, UNNEST(REGEXP_EXTRACT_ALL(tokens, r'"[^"]+":"[0-9]+"')) AS kv
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4
