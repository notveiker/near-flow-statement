-- F2b-a. bridge-mng.near's wNEAR ledger on wrap.near per day: kind, counterparty, amount (yoctoNEAR strings), count.
WITH p AS (
  SELECT day,
    CASE WHEN REGEXP_CONTAINS(line, r'^Deposit \d+ NEAR to bridge-mng\.near$') THEN 'wrap'
         WHEN REGEXP_CONTAINS(line, r'^Transfer \d+ from bridge-mng\.near to ') THEN 'out'
         WHEN REGEXP_CONTAINS(line, r'^Transfer \d+ from \S+ to bridge-mng\.near$') THEN 'in'
         WHEN REGEXP_CONTAINS(line, r'^Refund \d+ from \S+ to bridge-mng\.near$') THEN 'refund_in'
         WHEN REGEXP_CONTAINS(line, r'^Refund \d+ from bridge-mng\.near to ') THEN 'refund_out'
         ELSE 'other' END AS kind,
    REGEXP_EXTRACT(line, r'^(?:Deposit|Transfer|Refund) (\d+)') AS amt,
    CASE WHEN line LIKE 'Transfer % from bridge-mng.near to %' OR line LIKE 'Refund % from bridge-mng.near to %' THEN REGEXP_EXTRACT(line, r' to (\S+)$')
         WHEN line LIKE '% to bridge-mng.near' AND line NOT LIKE 'Deposit%' THEN REGEXP_EXTRACT(line, r' from (\S+) to ')
         ELSE '' END AS cp
  FROM `inlaid-backbone-501715-q6.nfs_rebuild.wrap_bridge`
)
SELECT day, kind, cp, CAST(SUM(SAFE_CAST(amt AS BIGNUMERIC)) AS STRING) AS yocto, COUNT(*) AS n
FROM p GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
