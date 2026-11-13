-- Exploratory (written 2026-11-13, after the freeze). A reproducible funding scan for the deliveries to NEAR's
-- three revenue wallets in the 30-day window 2026-10-06..11-04. The scan that filled the funding columns of
-- data/raw/escrow/deliveries.csv (BigQuery job bqjob_r275b038b73d7c093_000001a1af3708a8_1) has no committed
-- SQL; this query re-derives those columns independently, from the public dataset alone.
-- One row per dip4 native_withdraw from intents.near to a revenue wallet in the window:
--   receipt_id, block_height, src, wallet, amount_yocto       the delivery
--   src_deliveries_window      deliveries by the same src in the window (1 = single-use)
--   n_treasury_fundings        dip4 transfers of nep141:wrap.near from the treasury
--                              (PRIVATE_TREASURY_ACCOUNT_ID 51e8f94d...7cbe) to src, 2026-09-22..delivery block
--   fund_block_height, fund_receipt_id, fund_amount_yocto   the last such funding at or before the delivery
--   n_other_inflows            dip4 transfers to src from any other account in the same span
WITH ev AS (
  SELECT o.block_date AS day, o.block_height AS h, o.receipt_id AS rid, l.element AS el
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o, UNNEST(o.logs.list) l
  WHERE o.block_date BETWEEN '2026-09-22' AND '2026-11-04'
    AND o.executor_account_id = 'intents.near'
    AND l.element LIKE 'EVENT_JSON:{"standard":"dip4"%'
    AND (l.element LIKE '%"event":"transfer"%' OR l.element LIKE '%"event":"native_withdraw"%')
),
rows_ AS (
  SELECT day, h, rid, REGEXP_EXTRACT(el, r'"event":"([a-z_]+)"') AS event,
         JSON_VALUE(d, '$.account_id') AS sender, JSON_VALUE(d, '$.receiver_id') AS receiver,
         JSON_VALUE(d, '$.amount') AS native_amount,
         JSON_VALUE(JSON_QUERY(d, '$.tokens'), '$."nep141:wrap.near"') AS wnear_amount
  FROM ev, UNNEST(JSON_QUERY_ARRAY(SUBSTR(el, 12), '$.data')) d
),
deliv AS (
  SELECT day, h, rid, sender AS src, receiver AS wallet, native_amount AS amount_yocto
  FROM rows_
  WHERE event = 'native_withdraw' AND day >= '2026-10-06'
    AND receiver IN ('buybacks.multisignature.near', 'fefundsadmin.sputnik-dao.near', '1csfundsadmin.sputnik-dao.near')
),
nsrc AS (SELECT src, COUNT(*) AS src_deliveries_window FROM deliv GROUP BY src),
inflow AS (
  SELECT r.receiver AS acct, r.sender, r.h, r.rid, r.wnear_amount
  FROM rows_ r WHERE r.event = 'transfer' AND r.receiver IN (SELECT src FROM deliv)
),
pairs AS (
  SELECT dv.rid, dv.h, i.sender, i.h AS ih, i.rid AS irid, i.wnear_amount,
         i.sender = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe' AND i.wnear_amount IS NOT NULL AS is_fund
  FROM deliv dv JOIN inflow i ON i.acct = dv.src AND i.h <= dv.h
),
agg AS (
  SELECT rid, COUNTIF(is_fund) AS n_treasury_fundings, COUNTIF(NOT is_fund) AS n_other_inflows,
         ARRAY_AGG(IF(is_fund, STRUCT(ih AS fund_block_height, irid AS fund_receipt_id, wnear_amount AS fund_amount_yocto), NULL)
                   IGNORE NULLS ORDER BY ih DESC LIMIT 1)[SAFE_OFFSET(0)] AS f
  FROM pairs GROUP BY rid
)
SELECT CAST(dv.day AS STRING) AS day, dv.rid AS receipt_id, dv.h AS block_height, dv.src, dv.wallet, dv.amount_yocto,
       n.src_deliveries_window, IFNULL(a.n_treasury_fundings, 0) AS n_treasury_fundings,
       a.f.fund_block_height, a.f.fund_receipt_id, a.f.fund_amount_yocto, IFNULL(a.n_other_inflows, 0) AS n_other_inflows
FROM deliv dv JOIN nsrc n USING (src) LEFT JOIN agg a ON a.rid = dv.rid
ORDER BY block_height, receipt_id
