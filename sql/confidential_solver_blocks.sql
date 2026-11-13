-- Exploratory (written 2026-11-13, after the freeze). Does each solver shield pair with an unshield, as in a swap?
-- On 2026-09-02, 10-08 and 10-22 (three days already measured by sql/leg_count_days.sql): every block in which a
-- solver shielded tokens into the Confidential Intents treasury (PRIVATE_TREASURY_ACCOUNT_ID 51e8f94d...7cbe) or
-- unshielded tokens from it, with the tokens and raw amounts, joined as "token=amount;...". A solver is defined as in
-- sql/confidential_treasury_daily.sql (at least 20 shields and 20 unshields, counts within 5%), here over these three
-- days. Each shield block is matched to an unshield block in pipeline/compute.py
-- (confidential_flow), where prices are applied.
WITH ev AS (
  SELECT o.block_date AS day, o.block_height AS blk, l.element AS el
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o, UNNEST(o.logs.list) l
  WHERE o.block_date IN ('2026-09-02', '2026-10-08', '2026-10-22')
    AND o.executor_account_id = 'intents.near'
    AND o.status NOT LIKE '%FAIL%'
    AND l.element LIKE 'EVENT_JSON:{"standard":"dip4"%'
    AND l.element LIKE '%"event":"transfer"%'
    AND l.element LIKE '%51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe%'
),
d AS (SELECT day, blk, x FROM ev, UNNEST(JSON_QUERY_ARRAY(SUBSTR(el, 12), '$.data')) x),
t AS (
  SELECT day, blk,
    IF(JSON_VALUE(x, '$.receiver_id') = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe', 'in', 'out') AS dir,
    IF(JSON_VALUE(x, '$.receiver_id') = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe',
       JSON_VALUE(x, '$.account_id'), JSON_VALUE(x, '$.receiver_id')) AS cp,
    JSON_QUERY(x, '$.tokens') AS tokens
  FROM d
  WHERE JSON_VALUE(x, '$.account_id') = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe'
     OR JSON_VALUE(x, '$.receiver_id') = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe'
),
solvers AS (
  SELECT cp FROM t GROUP BY cp
  HAVING COUNTIF(dir = 'in') >= 20 AND COUNTIF(dir = 'out') >= 20
     AND ABS(COUNTIF(dir = 'in') - COUNTIF(dir = 'out')) <= 0.05 * COUNTIF(dir = 'in')
),
kv AS (
  SELECT t.day, t.blk, t.dir, t.cp, REGEXP_EXTRACT(m, r'^"([^"]+)"') AS token, REGEXP_EXTRACT(m, r'(-?[0-9]+)"?$') AS amt
  FROM t JOIN solvers USING (cp), UNNEST(REGEXP_EXTRACT_ALL(t.tokens, r'"[^"]+":"?-?[0-9]+"?')) m
)
SELECT day, cp AS solver, blk, dir, STRING_AGG(CONCAT(token, '=', amt), ';' ORDER BY token, amt) AS legs
FROM kv GROUP BY day, cp, blk, dir
ORDER BY day, cp, blk, dir
