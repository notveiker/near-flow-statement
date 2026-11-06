-- b_h1b_wnear_flows_logs.sql  (lane h1b-exchange, phase 1a: written and dry-run only, NOT run)
-- PREREG H1b/H1c wNEAR leg: wrap.near transfers into and out of the labelled exchange sets, from the
-- logs of wrap.near receipts in execution_outcomes (no receipt_actions, no args).
--
-- WINDOW (edit here only): block_date BETWEEN '2026-08-07' AND '2026-11-04'
--
-- IMPORTANT, checked 2026-11-06 by RPC (evidence/wrap_near_tx_6jxE7zxh_logs.json): wrap.near does NOT
-- emit NEP-297 EVENT_JSON logs. It emits the legacy near-contract-standards lines
--   "Transfer <yocto> from <sender> to <receiver>"   (ft_transfer, ft_transfer_call)
--   "Refund <yocto> from <receiver> to <sender>"     (ft_resolve_transfer; a reverse movement)
-- Both are parsed as a movement first-account -> second-account. EVENT_JSON nep141 ft_transfer lines
-- are also parsed, in case the contract is upgraded; each format is kept in its own `fmt` column so a
-- double emission would be visible rather than silently summed. Deposit/Withdraw (wrap/unwrap) lines
-- are ignored: they are not transfers between accounts. Receipts whose status contains FAIL are dropped
-- (status value spelling unverified; see notes.md).
--
-- Labelled sets: identical tiers to a_h1b_native_flows.sql. Tier 1 = named block below (from
-- exchange_accounts.json). Tiers 2-4 are pasted into `extra` from a_*.sql output (legs `member` and
-- `top100` with tier 4) before this query runs; bytes scanned do not depend on the list length.
-- Net wNEAR inflow(L) = movements from outside set(L) into it minus movements out of it.
--
-- Output, column `leg`: flow (day, lvl, direction, exchange, fmt, near, n) and qa (fmt, near, n).
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
extra AS (  -- GENERATED from a_h1b_native_flows.sql output before running (tiers 2, 3, 4)
  SELECT acct, tier, exchange
  FROM UNNEST(ARRAY<STRUCT<acct STRING, tier INT64, exchange STRING>>[
    -- ('<account>', <tier>, '<exchange or top100:account>'),
  ])
),
mem AS (
  SELECT acct, MIN(tier) AS tier, ARRAY_AGG(exchange ORDER BY tier LIMIT 1)[OFFSET(0)] AS exchange
  FROM (SELECT account AS acct, 1 AS tier, exchange FROM named UNION ALL SELECT * FROM extra)
  GROUP BY acct
),
lg AS (
  SELECT o.block_date AS day, l.element AS log
  FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` o, UNNEST(o.logs.list) l
  WHERE o.block_date BETWEEN '2026-08-07' AND '2026-11-04'
    AND o.executor_account_id = 'wrap.near'
    AND o.status NOT LIKE '%FAIL%'
    AND (STARTS_WITH(l.element, 'Transfer ') OR STARTS_WITH(l.element, 'Refund ')
         OR STARTS_WITH(l.element, 'EVENT_JSON:'))
),
mv AS (
  SELECT day, 'legacy' AS fmt,
         CAST(REGEXP_EXTRACT(log, r'^(?:Transfer|Refund) ([0-9]+) from ') AS BIGNUMERIC) / 1e24 AS near,
         REGEXP_EXTRACT(log, r' from (\S+) to ') AS sender,
         REGEXP_EXTRACT(log, r' to (\S+)$') AS receiver
  FROM lg
  WHERE REGEXP_CONTAINS(log, r'^(?:Transfer|Refund) [0-9]+ from \S+ to \S+$')
  UNION ALL
  SELECT day, 'event_json',
         CAST(JSON_VALUE(d, '$.amount') AS BIGNUMERIC) / 1e24,
         JSON_VALUE(d, '$.old_owner_id'), JSON_VALUE(d, '$.new_owner_id')
  FROM lg, UNNEST(JSON_QUERY_ARRAY(SUBSTR(log, 12), '$.data')) d
  WHERE STARTS_WITH(log, 'EVENT_JSON:')
    AND JSON_VALUE(SUBSTR(log, 12), '$.standard') = 'nep141'
    AND JSON_VALUE(SUBSTR(log, 12), '$.event') = 'ft_transfer'
),
tf AS (
  SELECT mv.day, mv.fmt, mv.near, s.tier AS s_tier, s.exchange AS s_ex, r.tier AS r_tier, r.exchange AS r_ex
  FROM mv
  LEFT JOIN mem s ON mv.sender = s.acct
  LEFT JOIN mem r ON mv.receiver = r.acct
  WHERE (s.acct IS NOT NULL OR r.acct IS NOT NULL) AND mv.sender != mv.receiver
),
flow AS (
  SELECT day, lvl, 'in' AS direction, r_ex AS exchange, fmt, SUM(near) AS near, COUNT(*) AS n
  FROM tf, UNNEST([1, 2, 3, 4]) AS lvl
  WHERE r_tier <= lvl AND (s_tier IS NULL OR s_tier > lvl)
  GROUP BY day, lvl, r_ex, fmt
  UNION ALL
  SELECT day, lvl, 'out', s_ex, fmt, SUM(near), COUNT(*)
  FROM tf, UNNEST([1, 2, 3, 4]) AS lvl
  WHERE s_tier <= lvl AND (r_tier IS NULL OR r_tier > lvl)
  GROUP BY day, lvl, s_ex, fmt
)
SELECT 'flow' AS leg, day, lvl, direction, exchange, fmt, ROUND(near, 6) AS near, n FROM flow
UNION ALL
SELECT 'qa', NULL, NULL, NULL, NULL, fmt, ROUND(SUM(near), 6), COUNT(*) FROM mv GROUP BY fmt
