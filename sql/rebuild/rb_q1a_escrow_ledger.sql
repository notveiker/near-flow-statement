-- Q1. Every wNEAR (nep141:wrap.near) movement that touches the Confidential Intents escrow inside intents.near.
-- Escrow = 51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe. Grouped by day, event type and the
-- role fields; amounts in yoctoNEAR as strings. role_hit = the escrow is in an owner/old_owner/new_owner/account_id field.
WITH x AS (
  SELECT day, h, event,
         JSON_VALUE(d, '$.owner_id') AS owner, JSON_VALUE(d, '$.old_owner_id') AS old_owner,
         JSON_VALUE(d, '$.new_owner_id') AS new_owner, JSON_VALUE(d, '$.account_id') AS account_id,
         (SELECT SUM(SAFE_CAST(JSON_VALUE_ARRAY(d, '$.amounts')[SAFE_OFFSET(i)] AS BIGNUMERIC))
            FROM UNNEST(JSON_VALUE_ARRAY(d, '$.token_ids')) tid WITH OFFSET i WHERE tid = 'nep141:wrap.near') AS mt_amt,
         SAFE_CAST(JSON_VALUE(d, '$.diff."nep141:wrap.near"') AS BIGNUMERIC) AS diff_amt
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.intents_events`
  WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015
    AND d LIKE '%51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe%'
    AND d LIKE '%nep141:wrap.near%'
)
SELECT day, event, owner, old_owner, new_owner, account_id,
       '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe' IN UNNEST([IFNULL(owner,''), IFNULL(old_owner,''), IFNULL(new_owner,''), IFNULL(account_id,'')]) AS role_hit,
       CAST(SUM(IFNULL(mt_amt, 0)) AS STRING) AS mt_yocto, CAST(SUM(IFNULL(diff_amt, 0)) AS STRING) AS diff_yocto,
       COUNT(*) AS n, MIN(h) AS min_h, MAX(h) AS max_h
FROM x
GROUP BY day, event, owner, old_owner, new_owner, account_id, role_hit
ORDER BY day, event, owner, old_owner, new_owner, account_id
