-- F10. Intents-wide wNEAR ledger on wrap.near: kind (unwrap = "Withdraw N NEAR from intents.near"; in/out = Transfer to/from intents.near;
-- refund_in/refund_out), counterparty, month, amount (yocto string) and count.
WITH p AS (
  SELECT FORMAT_DATE('%Y-%m', day) AS month,
    CASE WHEN REGEXP_CONTAINS(line, r'^Withdraw \d+ NEAR from intents\.near$') THEN 'unwrap'
         WHEN REGEXP_CONTAINS(line, r'^Transfer \d+ from \S+ to intents\.near$') THEN 'in'
         WHEN REGEXP_CONTAINS(line, r'^Transfer \d+ from intents\.near to \S+$') THEN 'out'
         WHEN REGEXP_CONTAINS(line, r'^Refund \d+ from \S+ to intents\.near$') THEN 'refund_in'
         WHEN REGEXP_CONTAINS(line, r'^Refund \d+ from intents\.near to \S+$') THEN 'refund_out'
         ELSE 'other' END AS kind,
    REGEXP_EXTRACT(line, r'^(?:Withdraw|Transfer|Refund) (\d+)') AS amt,
    CASE WHEN line LIKE '%from intents.near to %' THEN REGEXP_EXTRACT(line, r' to (\S+)$')
         WHEN line LIKE '% to intents.near' THEN REGEXP_EXTRACT(line, r' from (\S+) to ')
         ELSE '' END AS cp
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.wrap_intents`
)
SELECT month, kind, cp, CAST(SUM(SAFE_CAST(amt AS BIGNUMERIC)) AS STRING) AS yocto, COUNT(*) AS n
FROM p GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
