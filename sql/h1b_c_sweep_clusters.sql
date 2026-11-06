-- c_h1b_sweep_clusters.sql  (lane h1b-exchange, phase 1a: written and dry-run only, NOT run)
-- Sweep-detection pass for the deposit-address clustering disclosed in PREREG-ADDENDUM.md
-- ("accounts that receive from many users and sweep to a single account").
-- COUNT-BASED and args-free, so it reads only block_date, action_kind and the two account columns
-- (~24 GB for 90 days instead of ~262 GB with args). It is a cheap preview to review cluster structure
-- and thresholds BEFORE a_h1b_native_flows.sql runs. a_*.sql re-derives the same clusters with
-- amount-based rules inside its own scan, so the labelled set used for H1b comes from a_*.sql only.
--
-- WINDOW (edit here only): block_date BETWEEN '2026-08-07' AND '2026-11-04'
--
-- Deposit-like (count version of a_*.sql D-rules):
--   C1 >= 1 incoming transfer; C2 >= 1 outgoing transfer; C3 >= 90% of outgoing transfers go to one
--   destination; C4 <= 3 distinct destinations; C5 not a named (tier-1) account.
-- Hub = that destination. "Many users" is applied at the cluster level: a hub with fan-in >= 25
-- deposit-like accounts (H1), whose deposit-like accounts together have many distinct senders.
-- A hub is exchange-linked if it is a named account, or (H2, count version) >= 80% of its outgoing
-- transfers go to named accounts.
--
-- Output, column `leg`:
--   hub        account, n=fan-in (deposit-like accounts), n2=distinct senders into those accounts,
--              n3=hub outgoing transfers, n4=of which to named accounts, exchange (named or via H2),
--              is_named; top 1000 hubs with fan-in >= 25, by fan-in
--   named      per named account: deposit-like fan-in (n), distinct senders behind it (n2)
--   qa         totals
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
t AS (
  SELECT receipt_predecessor_account_id AS sender, receipt_receiver_account_id AS receiver
  FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
  WHERE block_date BETWEEN '2026-08-07' AND '2026-11-04'
    AND action_kind = 'TRANSFER'
    AND receipt_predecessor_account_id != 'system'
    AND receipt_predecessor_account_id != receipt_receiver_account_id
),
e AS (SELECT sender, receiver, COUNT(*) AS n FROM t GROUP BY sender, receiver),
acct_in AS (SELECT receiver AS acct, SUM(n) AS in_n, COUNT(*) AS n_senders FROM e GROUP BY receiver),
acct_out AS (
  SELECT sender AS acct, SUM(n) AS out_n, COUNT(*) AS n_dests,
         ARRAY_AGG(STRUCT(receiver AS dest, n AS n) ORDER BY n DESC LIMIT 1)[OFFSET(0)] AS top
  FROM e GROUP BY sender
),
dep AS (
  SELECT o.acct, o.top.dest AS dest, i.n_senders
  FROM acct_out o JOIN acct_in i USING (acct)
  WHERE i.in_n >= 1 AND o.out_n >= 1
    AND o.top.n >= 0.9 * o.out_n
    AND o.n_dests <= 3
    AND o.acct NOT IN (SELECT account FROM named)
),
hubs AS (
  SELECT dest AS hub, COUNT(*) AS n_dep, SUM(n_senders) AS dep_senders
  FROM dep GROUP BY dest
),
hub_to_named AS (
  SELECT e.sender AS hub, SUM(e.n) AS n_named,
         ARRAY_AGG(STRUCT(nm.exchange, e.n) ORDER BY e.n DESC LIMIT 1)[OFFSET(0)].exchange AS exchange
  FROM e JOIN named nm ON e.receiver = nm.account
  WHERE e.sender IN (SELECT hub FROM hubs WHERE n_dep >= 25)
  GROUP BY e.sender
)
SELECT 'hub' AS leg, h.hub AS account, h.n_dep AS n, h.dep_senders AS n2, o.out_n AS n3,
       hn.n_named AS n4, COALESCE(nm.exchange, hn.exchange) AS exchange, nm.account IS NOT NULL AS is_named
FROM (SELECT * FROM hubs WHERE n_dep >= 25 ORDER BY n_dep DESC LIMIT 1000) h
LEFT JOIN acct_out o ON o.acct = h.hub
LEFT JOIN hub_to_named hn USING (hub)
LEFT JOIN named nm ON nm.account = h.hub
UNION ALL
SELECT 'named', nm.account, COALESCE(h.n_dep, 0), h.dep_senders, NULL, NULL, nm.exchange, TRUE
FROM named nm LEFT JOIN hubs h ON h.hub = nm.account
UNION ALL
SELECT 'qa', 'deposit_like_accounts', COUNT(*), SUM(n_senders), NULL, NULL, NULL, NULL FROM dep
UNION ALL
SELECT 'qa', 'transfers_total', COUNT(*), NULL, NULL, NULL, NULL, NULL FROM t
