-- Exploratory (written 2026-11-13, after the freeze). Does DefiLlama's NEAR Intents volume count one leg or both?
-- Five full UTC days, all on or before 2026-10-22: 2026-08-18, 08-31, 09-02, 10-08, 10-22.
-- Per day and token (raw units, before decimals), from every successful dip4 event that intents.near emitted:
--   td_pos, td_neg   sums of the positive and of the negative token_diff amounts over all signers (public swaps:
--                    each swap appears once for the user and once for the solver, so td_pos + td_neg is four legs)
--   tr_in, tr_out    dip4 transfer amounts into / out of the Confidential Intents treasury
--                    (PRIVATE_TREASURY_ACCOUNT_ID 51e8f94d...7cbe)
--   tr_other         dip4 transfer amounts that do not touch the treasury
--   n_td, n_tr       how many diff entries / transfer entries carried the token
-- USD prices are applied in pipeline/compute.py (leg_count) from data/raw/coingecko/leg_count_prices.json.
WITH ev AS (
  SELECT o.block_date AS day, l.element AS el
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o, UNNEST(o.logs.list) l
  WHERE o.block_date IN ('2026-08-18', '2026-08-31', '2026-09-02', '2026-10-08', '2026-10-22')
    AND o.executor_account_id = 'intents.near'
    AND o.status NOT LIKE '%FAIL%'
    AND l.element LIKE 'EVENT_JSON:{"standard":"dip4"%'
    AND (l.element LIKE '%"event":"transfer"%' OR l.element LIKE '%"event":"token_diff"%')
),
d AS (
  SELECT day, REGEXP_EXTRACT(el, r'"event":"([a-z_]+)"') AS event, x
  FROM ev, UNNEST(JSON_QUERY_ARRAY(SUBSTR(el, 12), '$.data')) x
),
kv AS (
  SELECT day, event,
         JSON_VALUE(x, '$.account_id') AS sender, JSON_VALUE(x, '$.receiver_id') AS receiver,
         REGEXP_EXTRACT(m, r'^"([^"]+)"') AS token,
         CAST(REGEXP_EXTRACT(m, r'(-?[0-9]+)"?$') AS FLOAT64) AS amt
  FROM d, UNNEST(REGEXP_EXTRACT_ALL(
            IF(event = 'token_diff', JSON_QUERY(x, '$.diff'), JSON_QUERY(x, '$.tokens')),
            r'"[^"]+":"?-?[0-9]+"?')) m
  WHERE event IN ('token_diff', 'transfer')
)
SELECT day, token,
  SUM(IF(event = 'token_diff' AND amt > 0, amt, 0)) AS td_pos,
  SUM(IF(event = 'token_diff' AND amt < 0, -amt, 0)) AS td_neg,
  SUM(IF(event = 'transfer' AND receiver = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe', amt, 0)) AS tr_in,
  SUM(IF(event = 'transfer' AND sender = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe', amt, 0)) AS tr_out,
  SUM(IF(event = 'transfer' AND sender != '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe'
         AND receiver != '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe', amt, 0)) AS tr_other,
  COUNTIF(event = 'token_diff') AS n_td, COUNTIF(event = 'transfer') AS n_tr
FROM kv
GROUP BY day, token
ORDER BY day, token
