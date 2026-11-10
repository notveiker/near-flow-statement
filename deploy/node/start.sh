#!/bin/bash
# starts the node under tmux (idempotent); used by the container entrypoint after a restart
tmux has-session -t neard 2>/dev/null || tmux new-session -d -s neard "neard --home /data/near/home run 2>&1 | tee -a /data/near/neard.log"
