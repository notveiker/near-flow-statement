-- STAGE 1. Who sent each deposit. For every mt_mint receipt: originating transaction (receipt_origin_transaction),
-- its signer and receiver (transactions). Signer is the depositor when the transaction's receiver is the token contract;
-- otherwise the deposit was routed by a contract and the signer is only the initiator (tagged in the analysis).
CREATE OR REPLACE TABLE `inlaid-backbone-501715-q6.nfs_rebuild.mint_origin` AS
WITH m AS (SELECT rid, day, h, d FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events` WHERE event = 'mt_mint'),
o AS (
  SELECT receipt_id AS rid, originated_from_transaction_hash AS tx
  FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_origin_transaction`
  WHERE block_date BETWEEN '2026-07-07' AND '2026-11-04' AND block_height <= 223088015
    AND receipt_id IN (SELECT rid FROM m)
),
t AS (
  SELECT transaction_hash AS tx, signer_account_id AS signer, receiver_account_id AS tx_receiver
  FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
  WHERE block_date BETWEEN '2026-07-07' AND '2026-11-04' AND block_height <= 223088015
    AND transaction_hash IN (SELECT tx FROM o)
)
SELECT m.rid, m.day, m.h, m.d, o.tx, t.signer, t.tx_receiver
FROM m LEFT JOIN o USING (rid) LEFT JOIN t USING (tx)
