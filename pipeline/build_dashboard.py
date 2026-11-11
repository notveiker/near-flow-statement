"""Build dashboard/index.html: one self-contained page (no network requests) from committed data.

Run: python3 -m pipeline.build_dashboard   (or: make dashboard)
Open dashboard/index.html in a browser. The page embeds its data as JSON, so it also works from GitHub Pages or a file.
"""
from __future__ import annotations

import json
import sys

from .common import ROOT
from .dashboard_data import build

TEMPLATE = ROOT / "dashboard" / "template.html"
OUT = ROOT / "dashboard" / "index.html"
REQUIRED_METRICS = [
    "intents_share_peerset_30d_pct", "intents_share_peerset_365d_pct", "intents_rev_30d_m", "intents_rev_365d_m", "intents_vol_30d_b",
    "intents_vol_prior30d_b", "buyback_wallet_near_m", "rating_g_obs_pct", "rating_g_req_pct", "rating_g_obs_near_pct",
    "ladder_all_wallets_pct_of_issuance", "ladder_buyback_only_pct_of_issuance", "ladder_public_collectors_pct_of_issuance",
    "ladder_escrow_unshields_pct_of_issuance", "revwallets_near_k", "revwallets_vs_llama_rev_pct", "escrow_funded_exact_30d_n",
    "take_b1_bb_explicit_bp", "take_b3_bb_explicit_bp", "take_b1_vol_with_bb_pct", "take_b3_vol_with_bb_pct", "take_captured_bp_30d",
    "take_gross_bp_30d", "capture_share_30d_pct", "intents_rev_vs_l1fees_30d_x", "volume_channel_hhi", "volume_channel_hhi_swapkit_merged",
    "net_supply_growth_30d_annualized_pct", "total_supply_m", "mcap_to_rev_30d_annualized_x", "mcap_to_rev_365d_x", "h1a_ratio_as_written_x",
    "h1b_net_inflow_lower_m", "h1b_net_inflow_upper_m", "h1a_gross_issuance_90d_m", "h1c_identified_buying_m", "h1b_coverage_count_pct",
    "rating_output", "partners_kept_vs_near_rev_low_tight_x", "swapkit_vol_share_pct", "escrow_share_of_buyback_near_30d_pct",
    "explorer_out_of_near_usd_m", "explorer_into_near_usd_m", "explorer_near_side_swap_share_pct", "peers",
]


def render(data: dict) -> str:
    missing = [k for k in REQUIRED_METRICS if k not in data["metrics"]]
    if missing:
        raise SystemExit(f"dashboard needs metrics that are missing from data/metrics.json: {missing}")
    # `<` is escaped so no string in the data can close the script tag
    blob = json.dumps(data, separators=(",", ":"), sort_keys=True).replace("<", "\\u003c")
    html = TEMPLATE.read_text()
    if "__DATA__" not in html:
        raise SystemExit("template.html has no __DATA__ placeholder")
    return html.replace("__DATA__", blob)


def main() -> int:
    OUT.write_text(render(build()))
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
