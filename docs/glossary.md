# Glossary

Plain-language definitions of the terms a first-time reader meets in the [README](../README.md), [`THESIS.md`](../THESIS.md) and the other write-ups. Each entry restates what the repository already says; it adds no result and no number. The hedges ("our word", "inferred", "unattested") are kept on purpose. The rating rule's outputs are labels of a frozen rule, not recommendations.

## How results are labelled

- **Pre-registered.** Written into `PREREG.md` at the freeze (below) and not edited since. The pre-registered items are the hypotheses H1a to H1c, the rating rule, the forward tests F1 to F4 and the longer-dated predictions P1 to P3.
- **Exploratory.** Chosen after the freeze, so not pre-registered. The repository labels such results as exploratory wherever they appear, and the ladder, for example, does not feed the rating rule.
- **The freeze.** The commit and git tag `prereg-freeze` at which `PREREG.md` was fixed. Its time rests on git and manifest timestamps written by the author's machine, and on one external record: GitHub's activity log dates the push of the freeze commit to 2026-11-05 22:53:33 UTC (`PREREG-ADDENDUM.md`, 2026-11-12 23:50 UTC entry, item 2). No on-chain anchor is committed to check.
- **Addendum.** `PREREG-ADDENDUM.md`, the dated record of post-freeze results, method choices and corrections. It never changes `PREREG.md`.
- **Prior.** The probability the author wrote down in `PREREG.md` at the freeze for each pre-registered test and prediction; the data already seen then are listed in that file.
- **Token flow statement.** A statement of how a token moves. Here it covers NEAR's issuance, staking withdrawals, exchange inflows and identified buying.

## The pre-registered tests

- **H1a.** "Most staking rewards stay staked." It passes if net staking outflow is less than half of staking rewards. Because that outflow nets large principal flows in both directions, the test measures net principal churn; it does not show whether rewards themselves stay staked.
- **H1b.** "Less NEAR reaches exchanges than is minted." It passes if net exchange inflow is below gross issuance over the window. When label coverage is below half, H1b can come out pass or inconclusive but never fail.
- **H1c.** Identified buyers absorb a larger share of exchange-bound supply than of issuance. It passes if identified buying is at least a quarter of net exchange inflow.
- **Inconclusive.** The verdict of H1b or H1c when label coverage is below half and the test does not pass under both bounds. It is neither a pass nor a fail.
- **Net staking outflow.** NEAR withdrawn from staking pools minus NEAR deposited into them. It includes exchange-owned stake moving, which is not a sale.
- **Staking rewards.** The part of gross issuance that goes to stakers; the remainder goes to `treasury.near`.
- **Gross issuance and net issuance.** Gross issuance is the NEAR minted over a window, read from epoch-boundary block headers. Net issuance is minted minus burned.
- **Net exchange inflow.** Native NEAR plus wNEAR transferred into labelled exchange accounts, minus transfers out of them.
- **wNEAR.** NEAR wrapped as a token (`wrap.near`). Wrapping is a change of form, not an exit.
- **Identified buying.** The increase in the NEAR balance of `buybacks.multisignature.near` over the window.

## Exchange labels and the range

- **Exchange label.** A mark that an account belongs to a centralised exchange. Tier 1 labels come from a committed, cited list; tiers 2 and 3 come from our own sweep rule.
- **Label coverage.** The share of the biggest receivers of NEAR (the top hundred by inflow) that carry an exchange label. The pre-registration needs half before H1b and H1c can fail; below that they are reported as ranges. The headline coverage counts tiers 1 to 3; tier 1 alone is the strictly cited share.
- **Tiers 1 to 3.** Tier 1 is the cited list of exchange accounts. Tier 2 is accounts that look like deposit addresses sweeping into a tier 1 account. Tier 3 is unlabelled hubs that mostly feed tier 1, plus the deposit-like accounts feeding them.
- **Sweep rule.** Our own rule, fixed in the SQL headers, that produces tiers 2 and 3. It is not a cited source.
- **Lower and upper bound.** The two ends of the range for net exchange inflow when coverage is low. The lower bound treats every unlabelled account as not an exchange; the upper bound treats every unlabelled top receiver as an exchange. A test passes only if it passes under both.
- **Buyback wallet.** `buybacks.multisignature.near`, one of NEAR's three Intents revenue wallets. At the last read its NEAR was held, not burned.

## The rating rule

- **Rating rule.** The frozen rule that turns the results into a rating. Buy if G_obs is at least G_req and H1b passes; Avoid if G_obs is below half of G_req (the "Avoid line") and H1b fails; Hold otherwise. Hold carries no view on NEAR.
- **G_req.** The yearly growth in captured Intents revenue needed for it to equal the USD value of net issuance by a fixed date. It assumes HSP-029's ramp and a constant price.
- **G_obs.** The observed yearly growth of captured revenue: the most recent window of about half a year against the window of the same length before it. Over the 180 days to 2026-11-04 it measures a step in the share of fees NEAR captures, not growth in activity ([second review](second-review.md), section 6).
- **HSP-029.** A NEAR governance proposal to lower the issuance cap gradually over two years. The rating rule assumes its ramp is in force. After its timelock, a Directors' decision on execution follows; it then needs validator adoption through a protocol upgrade, a further step the repository does not date.
- **Timelock.** The stage of the on-chain proposal after voting. The repository assumes it starts when voting ends and first added up its end date itself, 2026-11-16; two published sources give the same date (`PREREG-ADDENDUM.md`, 2026-11-12 23:50 UTC entry, item 3). Under the House of Stake procedures a Directors' decision on execution follows the timelock.

## Forward tests

- **Forward tests F1 to F4.** Four predictions fixed in `PREREG.md` for a window that opened after the freeze: the buyback wallet's balance, supply growth per day, the captured take rate and Intents' share of the peer set. They are scored after the window by `pipeline/score_forward.py`, and every result is published, misses included.
- **Not scorable.** The score of a forward test with missing data. A missing value is never estimated.
- **Dry run.** A run of the scorer on current data to see that it works. It is not a score of F1-F4. A dry run made during the window reads days of the window, and the addendum discloses the ones that did.
- **Longer-dated predictions P1 to P3.** Three further pre-registered predictions that resolve on dates after the hackathon. They cannot be scored yet.

## NEAR Intents and its revenue

- **NEAR Intents.** The cross-chain swap venue whose fees the thesis follows. Its account `intents.near` pays out the withdrawals that reach NEAR's wallets.
- **1Click.** NEAR Intents' swap API. The docs say it does not take custody of the assets, so it is non-custodial.
- **Explorer API.** The NEAR Intents Explorer API, which lists swaps and the fees each lists for partners. It needs a partner key, so the repository commits daily aggregates and a sample of swaps, not every swap.
- **Captured revenue.** The NEAR that arrives at NEAR's three revenue wallets from outside that set, as DefiLlama's adapter defines revenue. Transfers between the three are excluded.
- **Adapter (DefiLlama).** DefiLlama's published code (on GitHub) that defines how a metric is computed. The near-intents fee adapter defines which wallets count as NEAR's revenue wallets.
- **The three revenue wallets.** `buybacks.multisignature.near`, `fefundsadmin.sputnik-dao.near` and `1csfundsadmin.sputnik-dao.near`: the wallets that DefiLlama's adapter counts as NEAR's revenue wallets.
- **Front-end fund.** `fefundsadmin.sputnik-dao.near`, the wallet that receives the fees of NEAR's own front ends; the fee docs name it for the near-intents.org fee.
- **Listed partner fees.** The app fees that 1Click swaps list for partner accounts (wallets and front ends). Who owns the receiving accounts is not shown.
- **Value capture.** Used narrowly here: the NEAR that verifiably reaches NEAR's revenue wallets, as a share of net issuance. It is not a valuation.
- **Attestation and unattested.** An attestation would be a statement by NEAR of which fee stream funds the escrow releases. Unattested means that no such statement exists in the sources the repository read. Evidence from the chain, such as the releases tracking confidential volume, can make a reading likely but does not attest it.
- **Point.** One percentage point of net issuance. The ladder's rungs are given in points: 4.53<!--n:ladder_public_collectors_pct_of_issuance--> points means NEAR equal to 4.53<!--n:ladder_public_collectors_pct_of_issuance-->% of net issuance over the window.
- **Peer set.** The native cross-chain venues that Intents is compared with: THORChain, Chainflip and Maya.
- **Take rate.** Revenue as basis points of volume. The captured take is DefiLlama revenue over reported volume.
- **Basis point (bp).** One hundredth of one percent.
- **HHI.** A concentration index: the sum of the squared shares of volume (or fees) across channels. Higher means more concentrated.

## The ladder and the escrow

- **The ladder.** The exploratory table in `THESIS.md` that splits the NEAR arriving in the revenue wallets, as shares of net issuance. Each line is a rung. The rungs are not nested: the buyback-wallet rung is a subset of the total, while collectors, escrow and the other source add up to it. The collector rung (4.53<!--n:ladder_public_collectors_pct_of_issuance--> points) splits into 3.97<!--n:ladder_collectors_public_swap_pct_of_issuance--> from publicly settled swaps and 0.56<!--n:ladder_collectors_escrow_funded_pct_of_issuance--> from fees paid by escrow-funded single-use accounts, so 11.81<!--n:ladder_escrow_all_pct_of_issuance--> points passed through the escrow in all ([`collector-funders.md`](collector-funders.md)).
- **Delivery.** A native-NEAR transfer from `intents.near` to one of the revenue wallets. Every delivery is a row of `data/raw/escrow/deliveries.csv`.
- **Collector A and collector B.** The two recurring public fee collectors that deliver NEAR to the buyback wallet. Collector A receives the explicit buyback fee. Collector B receives a variable cut that fits a share of quote improvement, a role that is inferred, not proven.
- **Quote improvement.** The case where a swap is filled at a better price than quoted. According to the fee docs, that difference is split between the integrator and the protocol.
- **Confidential Intents escrow.** Our word for the Treasury account that NEAR's Confidential Intents docs say backs each confidential token one for one.
- **Unshield.** A confidential withdrawal: the Treasury releases the backing tokens. On chain it shows as the escrow paying the exact amount to a fresh account, which then withdraws it to a revenue wallet. That pattern is an observation; the documentation describes the release, not the pattern.
- **Single-use account.** A fresh account that receives NEAR from the escrow and withdraws it to a revenue wallet. It appears in exactly one row of the delivery table.
- **FAR, shield, IMT.** FAR is the permissioned chain on which confidential swaps settle; its RPC is private. A shield moves tokens from `intents.near` to the escrow, after which the bridge mints the same amount on FAR as an IMT (Intents Multi-Token). An unshield burns the IMT and releases the tokens from the escrow.
- **Solver pair.** Our name for the public trace of a confidential swap on a solver's side: the solver shields one token and, about eight blocks later, unshields another token of the same value ([`confidential-flow.md`](confidential-flow.md)).
- **Funding hop.** The transfer from the escrow that funds a single-use account. Every single-use delivery in the ladder's window has a traced funding hop; before the window, most funding hops are sampled.

- **Signer, active account.** The account that signs a transaction. Nearblocks' "active accounts" are the distinct signers of a day, which BigQuery reproduces exactly (`docs/usage.md`). A signer is an account, not a person.
- **Relayed user, meta-transaction.** A user whose action a relayer signs and pays for (a `DELEGATE_ACTION`). It counts as a signer for the relayer, not for the user.

## Sources and how the repository checks itself

- **DefiLlama, Nearblocks, CoinGecko, FastNEAR, BigQuery.** The public sources of the data. DefiLlama gives Intents volume, fees and revenue and the peers' series; Nearblocks gives daily transactions, active accounts and total supply; CoinGecko gives prices; FastNEAR gives RPC reads, including archival balances at fixed blocks, and a transaction API; BigQuery's public NEAR dataset gives the on-chain flows.
- **Snapshot.** A copy of a source's data stored in the repository ("committed") under `data/raw/`. The numbers are computed from these copies, not from live sources.
- **Manifest.** `data/MANIFEST.json`, which records the SHA-256 of every file under `data/raw/`. `python3 -m pipeline.check --manifest` fails on any mismatch, missing file or unlisted file.
- **Metrics.** `data/metrics.json`: the numbers that `pipeline/compute.py` computes from the committed snapshots.
- **Marker.** A comment of the form `<!--n:…-->`, with a metric key in place of the dots, placed right after a number in the write-up. `python3 -m pipeline.check --numbers` fails if the number differs from the metric of that key.
- **Dashboard.** `site/index.html`, the static page that `python3 -m pipeline.render` rebuilds offline from the metrics.
- **Data fingerprint.** A short prefix of the SHA-256 of the manifest. The render command prints it and the dashboard shows it, so a page can be tied to the data it was built from.
