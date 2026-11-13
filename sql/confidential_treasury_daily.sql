-- Exploratory (written 2026-11-13, after the freeze). What the Confidential Intents treasury flow is, day by day.
-- Every successful dip4 transfer into ("in", a shield) or out of ("out", an unshield) the treasury
-- (PRIVATE_TREASURY_ACCOUNT_ID 51e8f94d...7cbe) from 2026-07-01 to 2026-11-04, summed per day, direction, token and
-- counterparty class, in raw units. cls = 'solver' when, over the whole period, the counterparty made at least 20
-- shields and at least 20 unshields and the two counts differ by at most 5% (a solver shields what it gives and
-- unshields what it receives, once per confidential swap); every other counterparty is 'other'. Ends on 2026-11-04 so that it reads no day of the
-- forward-test window. USD prices are applied in pipeline/compute.py (confidential_flow).
WITH ev AS (
  SELECT o.block_date AS day, l.element AS el
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o, UNNEST(o.logs.list) l
  WHERE o.block_date BETWEEN '2026-07-01' AND '2026-11-04'
    AND o.executor_account_id = 'intents.near'
    AND o.status NOT LIKE '%FAIL%'
    AND l.element LIKE 'EVENT_JSON:{"standard":"dip4"%'
    AND l.element LIKE '%"event":"transfer"%'
    AND l.element LIKE '%51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe%'
),
d AS (SELECT day, x FROM ev, UNNEST(JSON_QUERY_ARRAY(SUBSTR(el, 12), '$.data')) x),
t AS (
  SELECT day,
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
cls AS (
  SELECT DISTINCT t.cp, IF(s.cp IS NULL, 'other', 'solver') AS cls FROM t LEFT JOIN solvers s USING (cp)
),
kv AS (
  SELECT t.day, t.dir, c.cls, REGEXP_EXTRACT(m, r'^"([^"]+)"') AS token,
         CAST(REGEXP_EXTRACT(m, r'(-?[0-9]+)"?$') AS FLOAT64) AS amt
  FROM t JOIN cls c USING (cp), UNNEST(REGEXP_EXTRACT_ALL(t.tokens, r'"[^"]+":"?-?[0-9]+"?')) m
)
SELECT day, dir, cls, token, SUM(amt) AS amt, COUNT(*) AS n
FROM kv GROUP BY day, dir, cls, token
ORDER BY day, dir, cls, token
