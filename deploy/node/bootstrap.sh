#!/bin/bash
set -e
H=/data/near/home; mkdir -p $H
BOOT=$(curl -s -X POST https://free.rpc.fastnear.com -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"network_info\",\"params\":[],\"id\":1}" | jq -r ".result.active_peers as \$a | .result.known_producers as \$p | \$a[] as \$x | \$p[] | select(.peer_id == \$x.id) | \"\(.peer_id)@\(\$x.addr)\"" | paste -sd "," -)
echo "boot nodes: $(echo $BOOT | tr "," "\n" | wc -l)"
[ -f $H/config.json ] || neard --home $H init --chain-id mainnet --download-genesis --download-config rpc --boot-nodes "$BOOT"
jq --arg b "$BOOT" ".network.boot_nodes = \$b | .tracked_shards_config = \"AllShards\" | del(.tracked_shards, .tracked_accounts, .tracked_shard_schedule, .tracked_shadow_validator) | .gc_num_epochs_to_keep = 30 | .rpc.addr = \"0.0.0.0:3030\"" $H/config.json > $H/config.tmp && mv $H/config.tmp $H/config.json
jq "{tracked_shards_config, gc_num_epochs_to_keep, rpc: .rpc.addr, boot: (.network.boot_nodes|split(\",\")|length), archive}" $H/config.json
