-- a_h1b_native_flows.sql  (lane h1b-exchange, phase 1a: written and dry-run only, NOT run)
-- PREREG H1b/H1c, native-NEAR leg, plus the top-100 receivers needed for labelled coverage.
-- ONE scan of receipt_actions serves every native leg: labelled flows, coverage list, the amount-based
-- sweep clustering (rules D1-D5, H1-H2 below) and the upper-bound set. CTE `t` is referenced several
-- times; BigQuery bills the referenced columns once (verified by dry run, see dryrun.md).
--
-- WINDOW (edit here only; literal dates because pipeline/bq_run.py passes raw SQL, no --parameter):
--   block_date BETWEEN '2026-08-07' AND '2026-11-04'   (90 days, PREREG "Hypotheses on flows")
--
-- Transfers: action_kind = 'TRANSFER', predecessor != 'system' (gas refunds and refunds of failed
-- transfers), self-transfers dropped. Amount = args.deposit (yocto -> NEAR). Clustering and the top-100
-- use TRANSFER only (same convention as sql/spike_top_receivers_7d.sql).
-- Side component, same bytes (args and action_kind are already read): FUNCTION_CALL attached deposits
-- (> 0) crossing a set boundary, reported with kind = 'fcall_deposit' and NOT mixed into kind =
-- 'transfer'. Reason: an exchange restaking via deposit_and_stake is a FunctionCall (invisible to the
-- transfer leg) while the matching pool withdrawal arrives as a Transfer (visible), which would bias
-- net inflow upward. Every flow row also carries cp = counterparty class (pool | intents | wrap | other);
-- cp=wrap marks near_deposit wraps (NEAR -> wNEAR at wrap.near), which are a change of form, not an exit.
--
-- Labelled sets, nested; every rule is fixed here before the query runs:
--   tier 1  named accounts from exchange_accounts.json (cited; generated block below).
--   tier 2  deposit-like accounts whose sweep destination is a tier-1 account. Deposit-like (D1-D5):
--           D1 inflow >= 1 NEAR; D2 0.9 <= outflow/inflow <= 1.5; D3 top destination >= 90% of outflow;
--           D4 <= 3 distinct destinations; D5 not itself tier 1.
--   tier 3  unlabelled hubs with fan-in >= 25 deposit-like accounts (H1) that send >= 80% of their
--           outflow to tier-1 accounts (H2), plus the deposit-like accounts sweeping into them.
--   tier 4  (upper bound only) top-100 receivers by gross inflow that are not in tiers 1-3.
--   Exchange name of a tier-2/3 account = exchange of the tier-1 account it (or its hub) sweeps to.
-- Level L set = tiers <= L. Net exchange inflow(L) = transfers from outside set(L) into set(L) minus
-- transfers from set(L) to outside. Transfers inside the set (deposit->hot sweeps, hot->cold,
-- exchange->exchange) cancel by construction.
--   lower bound (PREREG "0% of unlabelled is exchange-bound") = level 1, 2 or 3 (report all three)
--   upper bound (PREREG "100%")                                = level 4
--
-- Output: one table, column `leg`:
--   flow    day, lvl, direction (in|out), exchange, near, n, note='kind=<transfer|fcall_deposit>;cp=<pool|intents|wrap|other>'
--   top100  rk, account, tier, exchange, near=gross inflow, near2=gross outflow, n=in transfers,
--           n2=distinct senders, note=deposit_like|hub|NULL              (labelled coverage)
--   hub     account, n=fan-in of deposit-like accounts, near=swept in, near2=sent to tier 1,
--           tier, exchange (top 500 by swept)                            (clusters for review)
--   member  account, tier, exchange, near=inflow, near2=outflow (tiers 2-3; feeds b_*.sql lists)
--   qa      note=metric, near, n
WITH named AS (
  SELECT exchange, account FROM UNNEST([
    -- GENERATED from exchange_accounts.json (40 accounts, all with a cited source); do not hand-edit
    STRUCT('binance' AS exchange, '10da3e6516672e0317d9c20e0bf89018271b18c5e3b01ac7b246b2417636a57b' AS account),
    ('binance', '1fc0d96bc0304bfaa1672d2ee84bfeed86ed2db1bdccedab95fa9792a4438a24'),
    ('binance', '27ddc83845172d5ee380af7ba6bcc524145892ff0b91a6078e9ae6d26655e56a'),
    ('binance', '451913e633c72fb951effe076d3bd2977e3f08083dcf6c87fa89992b0d437c5c'),
    ('binance', '56203c5b21b828175fa9c1fd4161ecaca76de9a1f6008935eeb9b4d6dc821a22'),
    ('binance', '5c33c6218d47e00ef229f60da78d0897e1ee9665312550b8afd5f9c7bc6957d2'),
    ('binance', '7747991786f445efb658b69857eadc7a57b6b475beec26ed14da8bc35bb2b5b6'),
    ('binance', '7e6e17fcb8e8e6a22ecd47bbd1b58b1af3582b97bbfd4a8d974bb9c266fa282b'),
    ('binance', '9c484fa5d2d069569ba063fc555c34e621ccd88fdbb0295fc79bad232621c5c1'),
    ('binance', 'b8caf00f8f925cc7b3925def6db361974403082ac7e7710b8342e0b20ac496e9'),
    ('binance', 'bc2fa68aa5d9a0d4e75fbe5659369aa13e1bccf7cabf81ac5d007ae0e51fcac3'),
    ('binance', 'binance1.near'),
    ('binance', 'binancecold3.near'),
    ('binance', 'c6f10c6993a97c90e34ce60c5ea3ccb4915cf731daff0e7a2e5d93ebc879cc74'),
    ('binance', 'ce766fc85f14b52d177bb0620a3be19585783644282b16ff3cfe3f4f699ece03'),
    ('binance', 'd04204b6591fefb973a8ed60929f8211af89ee38020da9faf905acdc7a320063'),
    ('binance', 'e1074e251c7350b8a4480816fffd897b727011df579e04cc19f890fd48fd8830'),
    ('binance', 'e1a70d1d2b8df95e0742c5aa18eb9089d84d5365fead073ac77d4c115cf3e264'),
    ('binance', 'e37e1cf6cd9c8601881799e531c958cd0ca01c734a6349aa88a23489c4258d05'),
    ('bitfinex', '383e50ea1a754ed3acd0d59116f221add87adb82559f31ca6d377f058fe83375'),
    ('bitfinex', '965c8b57b7f36fe9a40ce6188d444ca78708e4d83843b108f7f53d0fe5332076'),
    ('bitget', '241754260760e04e3a90acf27b1c54296b81e52a3b21fab8347ae88066946092'),
    ('bitget', '454e9a19b4552d08132efb9db354f8cdb1ceb155d8c2c9806f6cb15d947187cf'),
    ('gate', '0d584a4cbbfd9a4878d816512894e65918e54fae13df39a6f520fc90caea2fb0'),
    ('gate', 'f857de8a2a882488235eda61d3f41c4a60591d7f8daec1299ec0f20426a4cc3f'),
    ('gate', 'e10e284823bc0728f1850486fd4ccd5546249140e96823ac09f96b30363cd251'),
    ('gate', 'bc02e51d5f4c03611ef28d8fdbdba01b237f5a870fad7670d0a17a1a14934b97'),
    ('kucoin', 'kucoinc.near'),
    ('kucoin', 'e589457354361489a89039b8be6737cbc2db4d13919b6ccf23889a60f3b0d8f3'),
    ('kucoin', '7b865db190b966fe6ea30d0e7cc44ce42c4ea4f159a4b0b937122f166fc3ae28'),
    ('mexc', 'dba256d942a6fbfef9c8d42a2960f89a1f6dcc1e8490c7531d89a470d1d00405'),
    ('swissborg', 'dc6b4c8821dbe652b763e3bfadfea548137b29b97408c8b411ad72acff94e63f'),
    ('swissborg', '1c0dc521827821f1695538ff9312df15f32837bbfe95bc937f9faaafd4125552'),
    ('swissborg', '9b23bfd45a028e7a28326007b221cf8bd8b288630dde5ca714a0524f4865db89'),
    ('swissborg', '034e29f9703726c1f7b955fa5f7b16f6293adec615f668a73bc3b3b0255392df'),
    ('swissborg', 'c298ef5c3754dbcb6c23b481b514641f91d46845a256be4fd6ad742d5f3c251c'),
    ('flipster', 'd09904357488c186e9105396dc32f1a1180bf9870a09c037b3282372e337e770'),
    ('gate_us', '679760352e80fca56d416fdbe8c9e060ed96a5a2c7b4bb5add51f99a08fd8afe'),
    ('gate_us', 'c2566b91e059eb97e2acaa57fe1647db65970fe43f50a7264483d717737f2348'),
    ('bitlo', '6ab1742337f2734a9da8bc75091c0a4558280adc951be7db04feb4c1cea0edc1')
  ])
),
t0 AS (
  SELECT block_date AS day, action_kind AS kind,
         receipt_predecessor_account_id AS sender,
         receipt_receiver_account_id AS receiver,
         args
  FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
  WHERE block_date BETWEEN '2026-08-07' AND '2026-11-04'
    AND action_kind IN ('TRANSFER', 'FUNCTION_CALL')
    AND receipt_predecessor_account_id != 'system'
    AND receipt_predecessor_account_id != receipt_receiver_account_id
),
t AS (
  SELECT day, sender, receiver, CAST(JSON_VALUE(args, '$.deposit') AS BIGNUMERIC) / 1e24 AS near
  FROM t0 WHERE kind = 'TRANSFER'
),
e AS (SELECT sender, receiver, SUM(near) AS near, COUNT(*) AS n FROM t GROUP BY sender, receiver),
acct_in AS (
  SELECT receiver AS acct, SUM(near) AS in_near, SUM(n) AS in_n, COUNT(*) AS n_senders
  FROM e GROUP BY receiver
),
acct_out AS (
  SELECT sender AS acct, SUM(near) AS out_near, SUM(n) AS out_n, COUNT(*) AS n_dests,
         ARRAY_AGG(STRUCT(receiver AS dest, near AS near) ORDER BY near DESC LIMIT 1)[OFFSET(0)] AS top
  FROM e GROUP BY sender
),
dep AS (  -- deposit-like accounts, rules D1-D5
  SELECT o.acct, o.top.dest AS dest, i.in_near, o.out_near, i.n_senders
  FROM acct_out o JOIN acct_in i USING (acct)
  WHERE i.in_near >= 1
    AND o.out_near BETWEEN 0.9 * i.in_near AND 1.5 * i.in_near
    AND o.top.near >= 0.9 * o.out_near
    AND o.n_dests <= 3
    AND o.acct NOT IN (SELECT account FROM named)
),
hubs AS (
  SELECT dest AS hub, COUNT(*) AS n_dep, SUM(out_near) AS swept
  FROM dep GROUP BY dest
),
hub_to_named AS (
  SELECT e.sender AS hub, nm.exchange, SUM(e.near) AS near
  FROM e JOIN named nm ON e.receiver = nm.account
  WHERE e.sender IN (SELECT hub FROM hubs WHERE n_dep >= 25)
  GROUP BY e.sender, nm.exchange
),
hub_named AS (
  SELECT hub, SUM(near) AS to_named,
         ARRAY_AGG(STRUCT(exchange, near) ORDER BY near DESC LIMIT 1)[OFFSET(0)].exchange AS exchange
  FROM hub_to_named GROUP BY hub
),
hub3 AS (  -- tier-3 hubs, rules H1-H2
  SELECT h.hub, hn.exchange
  FROM hubs h JOIN hub_named hn USING (hub) JOIN acct_out o ON o.acct = h.hub
  WHERE h.n_dep >= 25
    AND h.hub NOT IN (SELECT account FROM named)
    AND hn.to_named >= 0.8 * o.out_near
),
mem_raw AS (
  SELECT account AS acct, 1 AS tier, exchange FROM named
  UNION ALL SELECT d.acct, 2, nm.exchange FROM dep d JOIN named nm ON d.dest = nm.account
  UNION ALL SELECT hub, 3, exchange FROM hub3
  UNION ALL SELECT d.acct, 3, h.exchange FROM dep d JOIN hub3 h ON d.dest = h.hub
),
mem AS (
  SELECT acct, MIN(tier) AS tier,
         ARRAY_AGG(exchange ORDER BY tier LIMIT 1)[OFFSET(0)] AS exchange
  FROM mem_raw GROUP BY acct
),
top100 AS (
  SELECT acct, in_near, in_n, n_senders, ROW_NUMBER() OVER (ORDER BY in_near DESC) AS rk
  FROM (SELECT * FROM acct_in ORDER BY in_near DESC LIMIT 100)
),
mem4 AS (
  SELECT acct, tier, exchange FROM mem
  UNION ALL
  SELECT p.acct, 4, CONCAT('top100:', p.acct) FROM top100 p LEFT JOIN mem m USING (acct) WHERE m.acct IS NULL
),
tf0 AS (  -- boundary candidates first (cheap join), then parse FunctionCall deposits only for those
  SELECT t0.day, LOWER(t0.kind) AS kind, t0.sender, t0.receiver, t0.args,
         s.tier AS s_tier, s.exchange AS s_ex, r.tier AS r_tier, r.exchange AS r_ex
  FROM t0
  LEFT JOIN mem4 s ON t0.sender = s.acct
  LEFT JOIN mem4 r ON t0.receiver = r.acct
  WHERE s.acct IS NOT NULL OR r.acct IS NOT NULL
),
tf AS (
  SELECT day, IF(kind = 'transfer', 'transfer', 'fcall_deposit') AS kind, near, s_tier, s_ex, r_tier, r_ex,
         CASE WHEN cp LIKE '%.poolv1.near' OR cp LIKE '%.pool.near' THEN 'pool'
              WHEN cp = 'intents.near' THEN 'intents'
              WHEN cp = 'wrap.near' THEN 'wrap' ELSE 'other' END AS cp_in,
         CASE WHEN cr LIKE '%.poolv1.near' OR cr LIKE '%.pool.near' THEN 'pool'
              WHEN cr = 'intents.near' THEN 'intents'
              WHEN cr = 'wrap.near' THEN 'wrap' ELSE 'other' END AS cp_out
  FROM (SELECT *, sender AS cp, receiver AS cr,
               CAST(JSON_VALUE(args, '$.deposit') AS BIGNUMERIC) / 1e24 AS near FROM tf0)
  WHERE near > 0
),
flow AS (
  SELECT day, lvl, 'in' AS direction, r_ex AS exchange, kind, cp_in AS cp, SUM(near) AS near, COUNT(*) AS n
  FROM tf, UNNEST([1, 2, 3, 4]) AS lvl
  WHERE r_tier <= lvl AND (s_tier IS NULL OR s_tier > lvl)
  GROUP BY day, lvl, r_ex, kind, cp_in
  UNION ALL
  SELECT day, lvl, 'out', s_ex, kind, cp_out, SUM(near), COUNT(*)
  FROM tf, UNNEST([1, 2, 3, 4]) AS lvl
  WHERE s_tier <= lvl AND (r_tier IS NULL OR r_tier > lvl)
  GROUP BY day, lvl, s_ex, kind, cp_out
)
SELECT 'flow' AS leg, day, lvl, CAST(NULL AS INT64) AS rk, CAST(NULL AS STRING) AS account,
       CAST(NULL AS INT64) AS tier, exchange, direction, ROUND(near, 6) AS near,
       CAST(NULL AS BIGNUMERIC) AS near2, n, CAST(NULL AS INT64) AS n2,
       CONCAT('kind=', kind, ';cp=', cp) AS note
FROM flow
UNION ALL
SELECT 'top100', NULL, NULL, p.rk, p.acct, m.tier, m.exchange, NULL, ROUND(p.in_near, 6),
       ROUND(o.out_near, 6), p.in_n, p.n_senders,
       CASE WHEN d.acct IS NOT NULL THEN CONCAT('deposit_like->', d.dest)
            WHEN hb.n_dep >= 25 THEN CONCAT('hub fan-in ', CAST(hb.n_dep AS STRING)) END
FROM top100 p LEFT JOIN mem m USING (acct) LEFT JOIN acct_out o USING (acct)
LEFT JOIN dep d USING (acct) LEFT JOIN hubs hb ON hb.hub = p.acct
UNION ALL
SELECT 'hub', NULL, NULL, NULL, h.hub, m.tier, COALESCE(m.exchange, hn.exchange), NULL,
       ROUND(h.swept, 6), ROUND(hn.to_named, 6), h.n_dep, NULL, NULL
FROM (SELECT * FROM hubs WHERE n_dep >= 25 ORDER BY swept DESC LIMIT 500) h
LEFT JOIN hub_named hn USING (hub) LEFT JOIN mem m ON m.acct = h.hub
UNION ALL
SELECT 'member', NULL, NULL, NULL, m.acct, m.tier, m.exchange, NULL, ROUND(i.in_near, 6),
       ROUND(o.out_near, 6), i.in_n, o.out_n, NULL
FROM mem m LEFT JOIN acct_in i USING (acct) LEFT JOIN acct_out o USING (acct)
WHERE m.tier IN (2, 3)
UNION ALL
SELECT 'qa', NULL, NULL, NULL, NULL, NULL, NULL, NULL, ROUND(SUM(near), 6), NULL, COUNT(*),
       COUNTIF(near IS NULL), 'transfers_total (n2 = rows with unparsable deposit)'
FROM t
UNION ALL
SELECT 'qa', NULL, NULL, NULL, NULL, NULL, NULL, NULL, ROUND(SUM(in_near), 6), NULL, COUNT(*), NULL,
       'deposit_like_accounts'
FROM dep
