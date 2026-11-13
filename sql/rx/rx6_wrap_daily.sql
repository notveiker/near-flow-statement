-- RX6. Intents-wide wNEAR ledger per UTC day (staged wrap_intents, same line shapes as the FU10 ledger): kind in {in, out, refund_in, refund_out, unwrap}, amount (yocto string), count.
SELECT day,
  CASE WHEN REGEXP_CONTAINS(line, r'^Withdraw \d+ NEAR from intents\.near$') THEN 'unwrap'
       WHEN REGEXP_CONTAINS(line, r'^Transfer \d+ from \S+ to intents\.near$') THEN 'in'
       WHEN REGEXP_CONTAINS(line, r'^Transfer \d+ from intents\.near to \S+$') THEN 'out'
       WHEN REGEXP_CONTAINS(line, r'^Refund \d+ from \S+ to intents\.near$') THEN 'refund_in'
       WHEN REGEXP_CONTAINS(line, r'^Refund \d+ from intents\.near to \S+$') THEN 'refund_out' ELSE 'other' END AS kind,
  CAST(SUM(SAFE_CAST(REGEXP_EXTRACT(line, r'^(?:Withdraw|Transfer|Refund) (\d+)') AS BIGNUMERIC)) AS STRING) AS yocto, COUNT(*) AS n
FROM `inlaid-backbone-501715-q6.nfs_rebuild.wrap_intents`
WHERE day BETWEEN '2026-07-07' AND '2026-11-04' AND h <= 223088015
GROUP BY 1, 2 ORDER BY 1, 2
