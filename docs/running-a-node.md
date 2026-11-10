# Running our own NEAR node

Why: the keyless public block API is too slow to follow the chain (see [rpc-sources.md](rpc-sources.md)), and regular public RPCs keep only about 36 hours. A node of our own has no rate limit, keeps everything from the day it syncs (we raise `gc_num_epochs_to_keep` to 30, about 15 days), and its data can be hashed and handed to a reviewer.

## Machine

Any Linux VM with 8 vCPU, 32 GiB of RAM and a 3 TiB volume, running `nearprotocol/nearcore:2.14.0` (protocol 88). We used 8 vCPU, 32 GiB and 3 TiB. The scripts in [`deploy/node/`](../deploy/node) are the whole setup.

## Steps (10 Nov 2026)

1. `deploy/node/bootstrap.sh` reads the live peer list from a public RPC (`network_info` on `free.rpc.fastnear.com`), runs `neard init --chain-id mainnet --download-genesis --download-config rpc --boot-nodes "<peers>"`, and patches `config.json`: `tracked_shards_config = "AllShards"`, the deprecated `tracked_*` keys removed, `gc_num_epochs_to_keep = 30`, `rpc.addr = 0.0.0.0:3030`.
2. `deploy/node/start.sh` starts `neard run` under tmux. An empty data directory makes a non-archival node use Epoch Sync, then header sync, state sync and block sync.

## What went wrong, and the fixes

- **State sync stalled at "header" for 10 shards** with `Tier3 connectivity` warnings. Peers must connect back to deliver state parts, and a VM behind NAT advertises the wrong address. Fix: set `network.experimental.tier3_public_addr` to `<public IP>:<external port>`, restart, and check `curl localhost:3030/metrics | grep near_tier3_public_addr`. Parts then downloaded at about 3 a second.
- **A restart left the old process running.** Killing the tmux session does not stop `neard` (it sits behind a `tee` pipe), so the second start failed on the RocksDB `LOCK`. Stop it with `kill -TERM <pid>` and wait for it to exit before restarting.
- **Disk speed.** The volume wrote about 71 MB/s in a direct 1 MiB test, well under NEAR's recommended 800 MiB/s. State sync and block sync still ran, so this is noted and not a blocker.

## Timeline we saw

Headers took about 15 minutes. State sync was 7,837 parts across 10 shards: the downloads took about 1.5 hours, and applying the state took about 3 more. Block sync then closed about 28,000 blocks in about 1.5 hours, at 3 to 9 blocks a second against a chain that makes about 1.7 a second. In all, about 6 hours from an empty disk to the tip.

## What the node can and cannot give

The last 30 epochs from the sync point, with unlimited local RPC. It cannot give older history; use the sampled history (`docs/history-sample-prereg.md`) or an archival RPC for point lookups.
