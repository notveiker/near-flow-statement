# Raw-chain sources: what each one gives, measured 10 Nov 2026

Probed from a laptop and from a cloud VM (Australia), with one request at a time. Short probes only; no source was loaded beyond a few dozen requests.

| Source | History | Measured limit | Use |
|---|---|---|---|
| `mainnet.neardata.xyz` `/v0/block/<h>` (no key) | Genesis (9,820,210) to tip; block and all shards in one reply | Documented 180 a minute. Measured: about 15 requests, then HTTP 429 (`Retry-After: 0`), then roughly 15 more each 40 seconds, even at 1 request a second. That is about 20 to 25 blocks a minute, below the chain's 60 a minute | Spot checks only. Not enough to follow the chain or to backfill |
| `free.rpc.fastnear.com` (no key) | About 36 hours (older heights return `UNKNOWN_BLOCK`) | 100 `block` calls at 5 a second with no 429 | Recent blocks; one block needs `block` plus one `chunk` call per shard (10 shards at the tip) |
| `rpc.intea.rs` (no key) | About 36 hours | 429 after 19 calls at 5 a second | Not for collection |
| `archival-rpc.mainnet.near.org` (no key) | Genesis to tip | NEAR's notice sets 4 requests a minute; each call took about 3 seconds | Point lookups at old heights (issuance reads, a specific receipt) |
| `archival-rpc.mainnet.fastnear.com` | Genesis to tip | Paid key | Not used |

Block sizes from `neardata`: 3 KB at genesis, about 1 MB around height 93.6M, 126 KB at the tip.

`pipeline/near_collect.py` is a resumable, checksummed archiver for `neardata` that respects a request rate and backs off on 429. At the measured limit it cannot keep pace with the chain, so it is a verification tool, not a bulk source.
