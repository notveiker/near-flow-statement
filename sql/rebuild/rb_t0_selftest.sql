-- Self-test of the JSON path and token-diff parsing used by every rb_ query. SYNTHETIC input only: no chain data is read.
-- Expected output is asserted in tests/test_rebuild.py.
WITH t AS (
  SELECT '{"standard":"nep245","event":"mt_mint","data":[{"owner_id":"E","token_ids":["nep141:wrap.near","nep141:x"],"amounts":["5","7"],"memo":"deposit"}]}' AS e
  UNION ALL SELECT '{"standard":"dip4","event":"token_diff","data":[{"account_id":"E","diff":{"nep141:wrap.near":"-12","nep141:usdc":"34"},"referral":"r1"}]}'
)
SELECT JSON_VALUE(PARSE_JSON(e), '$.event') AS event,
       JSON_VALUE(d, '$.owner_id') AS owner,
       (SELECT SUM(SAFE_CAST(JSON_VALUE_ARRAY(d, '$.amounts')[SAFE_OFFSET(i)] AS BIGNUMERIC))
          FROM UNNEST(JSON_VALUE_ARRAY(d, '$.token_ids')) tid WITH OFFSET i WHERE tid = 'nep141:wrap.near') AS wnear_mt,
       SAFE_CAST(JSON_VALUE(d, '$.diff."nep141:wrap.near"') AS BIGNUMERIC) AS wnear_diff,
       ARRAY_TO_STRING(REGEXP_EXTRACT_ALL(TO_JSON_STRING(JSON_QUERY(d, '$.diff')), r'"[^"]+":"-?[0-9]+"'), '|') AS pairs
FROM t, UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(e), '$.data')) d
ORDER BY event
