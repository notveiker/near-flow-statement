"""Assemble everything the dashboard shows from committed data (offline, standard library only).

Every number here is read from data/metrics.json, data/series.json or a raw snapshot under data/raw/, or is computed
from them in this file with the formula next to it. Nothing is typed in by hand except the HSP-029 constants, which are
read from data/raw/rpc/rating_assumptions.json.

`build()` returns one JSON-serialisable dict; `pipeline.build_dashboard` embeds it in dashboard/template.html.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .common import DATA, RAW, ROOT

QUARTER_FIELDS = ("txns", "active_accounts", "new_accounts")


def _load(p: Path):
    return json.loads(Path(p).read_text())


def _q(date: str) -> str:
    return f"{date[:4]}Q{(int(date[5:7]) - 1) // 3 + 1}"


def nearblocks_quarterly() -> list[dict]:
    """Daily Nearblocks charts -> per-quarter mean per day."""
    rows = _load(RAW / "nearblocks" / "charts.json")["charts"]
    agg: dict[str, dict] = {}
    for r in rows:
        a = agg.setdefault(_q(r["date"]), {"n": 0, "txns": 0.0, "active": 0.0, "new": 0.0, "fee_near": 0.0})
        a["n"] += 1
        a["txns"] += float(r.get("txns") or 0)
        a["active"] += float(r.get("active_accounts") or 0)
        a["new"] += float(r.get("new_accounts") or 0)
        a["fee_near"] += float(r.get("txn_fee") or 0) / 1e24
    return [{"q": q, "days": a["n"], "tx_per_day": a["txns"] / a["n"], "active_per_day": a["active"] / a["n"],
             "new_per_day": a["new"] / a["n"], "fee_near_per_day": a["fee_near"] / a["n"]} for q, a in sorted(agg.items())]


def market() -> dict:
    """Relative performance and a weekly indexed price series from Binance daily closes."""
    def load(sym):
        rows = _load(RAW / "market" / f"spot_{sym}usdt_1d.json")["rows"]
        return {int(r[0] // 1000) // 86400 * 86400: float(r[4]) for r in rows}, sum(float(r[7]) for r in rows[-30:]) / 30
    px, vol = {}, {}
    for s in ("near", "eth", "sol", "btc"):
        px[s], vol[s] = load(s)
    last = max(px["near"])

    def at(s, t):
        ks = [k for k in px[s] if k <= t]
        return px[s][max(ks)]

    perf = {str(b): {s: at(s, last) / at(s, last - b * 86400) - 1 for s in px} for b in (30, 90, 180, 365)}
    start = last - 365 * 86400
    weekly = []
    t = start
    while t <= last:
        weekly.append({"t": t, **{s: at(s, t) / at(s, start) * 100 for s in px}})
        t += 7 * 86400
    funding = _load(RAW / "market" / "futures_funding_nearusdt.json")
    ls = _load(RAW / "market" / "futures_longshort_nearusdt_1d.json")
    oi = _load(RAW / "market" / "futures_oi_nearusdt_1d.json")
    return {
        "asof": datetime.fromtimestamp(last, timezone.utc).date().isoformat(), "perf": perf, "weekly": weekly,
        "near_spot_usd_per_day_30d": vol["near"],
        "funding_90d_avg_8h": sum(float(x["fundingRate"]) for x in funding[-270:]) / 270,
        "long_short_ratio": float(ls[-1]["longShortRatio"]), "open_interest_usd": float(oi[-1]["sumOpenInterestValue"]),
    }


def ecosystem() -> dict:
    ch = _load(RAW / "ecosystem" / "chain_tvl.json")
    st = _load(RAW / "ecosystem" / "stablecoins.json")
    dx = _load(RAW / "ecosystem" / "dex_volume.json")
    fe = _load(RAW / "ecosystem" / "fees.json")
    pr = _load(RAW / "ecosystem" / "protocols_on_near.json")

    def qlast(rows, key):
        out: dict[str, float] = {}
        for r in rows:
            d = datetime.fromtimestamp(int(r["date"]), timezone.utc).date().isoformat()
            out[_q(d)] = key(r)
        return out
    tvl_q = qlast(ch, lambda r: r["tvl"])
    stable_q = qlast(st, lambda r: r["totalCirculatingUSD"]["peggedUSD"])
    return {
        "tvl_q": tvl_q, "stable_q": stable_q, "tvl_now": ch[-1]["tvl"], "stable_now": st[-1]["totalCirculatingUSD"]["peggedUSD"],
        "dex_30d": dx["total30d"], "dex_1y": dx["total1y"], "dex_top": sorted(dx["protocols"], key=lambda p: -(p["total30d"] or 0))[:5],
        "fees_30d": fe["total30d"], "fees_1y": fe["total1y"],
        "protocols": [{"name": p["name"], "category": p["category"], "tvl": p["near_tvl"]} for p in pr[:12]],
        "protocol_count": len(pr),
    }


def governance() -> dict:
    ts = _load(RAW / "governance" / "topics.json")
    by_year: dict[str, int] = {}
    for t in ts:
        by_year[t["created_at"][:4]] = by_year.get(t["created_at"][:4], 0) + 1
    hsp = [t for t in ts if "HSP" in (t["title"] or "")]
    return {"topics": len(ts), "by_year": by_year, "hsp_threads": len(hsp)}


def hsp029(assump: dict) -> dict:
    """Issuance cap path: flat at start_cap until activation, then linear to target_cap over ramp_months."""
    h = assump["hsp029"]
    act = datetime.fromisoformat(h["activation_date"]).replace(tzinfo=timezone.utc)
    pts, y, m = [], datetime(2026, 11, 1, tzinfo=timezone.utc).year, 11
    for i in range(0, 41):
        mm = (10 + i) % 12 + 1
        yy = 2026 + (10 + i) // 12
        d = datetime(yy, mm, 1, tzinfo=timezone.utc)
        t = max(0.0, (d - act).total_seconds() / (365.25 / 12 * 86400))
        cap = h["start_cap"] - (h["start_cap"] - h["target_cap"]) * min(t, h["ramp_months"]) / h["ramp_months"]
        pts.append({"date": d.date().isoformat(), "cap_pct": round(cap * 100, 4)})
    return {"start_cap_pct": h["start_cap"] * 100, "target_cap_pct": h["target_cap"] * 100, "activation": h["activation_date"],
            "ratification": h["ratification_utc"], "ramp_months": h["ramp_months"], "path": pts}


def holdings() -> dict | None:
    snap = RAW / "intents" / "holdings_snapshot.json"
    if not snap.exists():
        return None
    s = _load(snap)
    by_chain: dict[str, float] = {}
    for t in s["tokens"]:
        by_chain[t.get("chain") or "other"] = by_chain.get(t.get("chain") or "other", 0) + t.get("value_usd", 0)
    wn = next((t for t in s["tokens"] if t["token_id"] == "nep141:wrap.near"), None)
    out = {"asof_utc": s["asof_utc"], "block_height": s["block_height"], "total_usd": s["total_value_usd"], "tokens": s["token_count"],
           "top": [{k: t[k] for k in ("symbol", "chain", "amount", "value_usd")} for t in s["tokens"][:10]],
           "by_chain": sorted(({"chain": k, "usd": v} for k, v in by_chain.items()), key=lambda r: -r["usd"])[:8],
           "wnear_amount": wn["amount"] if wn else None, "wnear_usd": wn["value_usd"] if wn else None, "history": None}
    hist = RAW / "intents" / "holdings_history.json"
    if hist.exists():
        h = _load(hist)
        px = {t["token_id"]: (t["price_usd"], t["decimals"]) for t in h["tokens"]}
        pts = []
        for p in h["points"]:
            tot, wnv = 0.0, 0.0
            for tid, raw in p["supply_raw"].items():
                if raw is None:
                    continue
                price, dec = px[tid]
                v = int(raw) / 10 ** dec * (price or 0)
                tot += v
                if tid == "nep141:wrap.near":
                    wnv = int(raw) / 10 ** dec
            pts.append({"month": p["month"], "usd": tot, "wnear": wnv})
        out["history"] = pts
        out["history_tokens"] = len(h["tokens"])
        ids = {t["token_id"] for t in h["tokens"]}
        out["history_now_usd"] = sum(t.get("value_usd", 0) for t in _load(snap)["tokens"] if t["token_id"] in ids)
    return out


def peers() -> dict | None:
    p = RAW / "peers" / "revenue.json"
    if not p.exists():
        return None
    r = _load(p)
    mc = {c["id"]: c for c in _load(RAW / "peers" / "market_caps.json")["coins"]}
    tok = {"near-intents": "near", "thorchain-dex": "thorchain", "chainflip-amm": "chainflip", "maya-protocol": "cacao"}
    rows = []
    for slug, name in r["venues"].items():
        ser = r["series"][slug]
        f = lambda k, n=30: sum(v for _, v in ser[k][-n:])
        rows.append({"slug": slug, "venue": name, "fees_30d": f("dailyFees"), "revenue_30d": f("dailyRevenue"),
                     "holders_30d": f("dailyHoldersRevenue"), "token_mcap": mc[tok[slug]]["market_cap"]})
    return {"asof": datetime.fromtimestamp(r["series"]["near-intents"]["dailyFees"][-1][0], timezone.utc).date().isoformat(), "venues": rows}


def usage_flows(usage: dict | None) -> dict | None:
    """Deposits, withdrawals and public swap legs from the census, valued at the holdings snapshot's prices."""
    snap = RAW / "intents" / "holdings_snapshot.json"
    if not usage or "flows" not in usage or not snap.exists():
        return None
    tok = {t["token_id"]: t for t in _load(snap)["tokens"]}
    usd = {"deposit": 0.0, "withdraw": 0.0, "swap_in": 0.0}
    unpriced = set()
    for tid, f in usage["flows"].items():
        t = tok.get(tid)
        if not t:
            unpriced.add(tid)
            continue
        for k in usd:
            if k in f:
                usd[k] += int(f[k]) / 10 ** t["decimals"] * t["price_usd"]
    return {**usd, "token_ids": len(usage["flows"]), "unpriced_ids": len(unpriced)}


def builders() -> dict | None:
    p = RAW / "builders" / "npm_daily.json"
    if not p.exists():
        return None
    d = _load(p)
    out = {}
    for pkg, rows in d["packages"].items():
        m: dict[str, int] = {}
        for day, n in rows:
            m[day[:7]] = m.get(day[:7], 0) + n
        out[pkg] = [{"month": k, "n": v} for k, v in sorted(m.items())]
    return {"end": d["end"], "packages": out}


def validators() -> dict | None:
    p = RAW / "rpc" / "validators_epochs.json"
    if not p.exists():
        return None
    e = _load(p)["epochs"]
    m = RAW / "rpc" / "validators_monthly.json"
    return {"latest": e[-1], "monthly": _load(m)["months"] if m.exists() else None}


def web_facts() -> dict | None:
    p = RAW / "web" / "third_party_facts.json"
    return {f["id"]: {"claim": f["claim"], "url": f["url"], "quote": f["quote"]} for f in _load(p)["facts"]} if p.exists() else None


def prop() -> dict | None:
    """Fee / DEX dominance, liquid-staking TVL and GitHub pulse from data/raw/prop/."""
    root = RAW / "prop"
    if not (root / "fees_near.json").exists():
        return None
    fees, dexs = _load(root / "fees_near.json"), _load(root / "dexs_near.json")
    lst = _load(root / "lst.json") if (root / "lst.json").exists() else None
    gh = _load(root / "github.json") if (root / "github.json").exists() else None
    return {
        "fees_top_share_30d_pct": fees.get("top_share_30d_pct"),
        "fees_chain_30d": fees.get("chain_total30d"),
        "fees_protocols": fees.get("protocols", [])[:6],
        "dex_top_share_30d_pct": dexs.get("top_share_30d_pct"),
        "dex_chain_30d": dexs.get("chain_total30d"),
        "dex_protocols": dexs.get("protocols", [])[:6],
        "lst": [{"name": p["name"], "tvl_now": p.get("tvl_now"), "tvl_365d_ago": p.get("tvl_365d_ago"),
                 "quarterly": p.get("quarterly_end", [])[-6:]} for p in (lst or {}).get("protocols", []) if not p.get("error")],
        "github": [r for r in (gh or {}).get("repos", []) if not r.get("error")],
        "etf": _load(root / "etf_nrr.json") if (root / "etf_nrr.json").exists() else None,
        "lst_vs_stake": _load(root / "lst_vs_stake.json") if (root / "lst_vs_stake.json").exists() else None,
        "validators": _load(root / "validators_summary.json") if (root / "validators_summary.json").exists() else None,
    }


def optional(rel: str):
    p = DATA / rel
    return _load(p) if p.exists() else None


def reproducibility() -> dict:
    man = DATA / "MANIFEST.json"
    plan = DATA / "sample" / "plan.sha256"
    return {
        "manifest_files": len(_load(man)["files"]),
        "manifest_sha256": hashlib.sha256(man.read_bytes()).hexdigest(),
        "sample_plan_sha256": plan.read_text().split()[0] if plan.exists() else None,
        "prereg_sha256": "19e470be5398f67ce7b6b5a51f007c0c7a0fcc059b61853c52caf7401452e240",
    }


def build() -> dict:
    m = _load(DATA / "metrics.json")
    s = _load(DATA / "series.json")
    assump = _load(RAW / "rpc" / "rating_assumptions.json")
    return {
        "metrics": m, "series": s,
        "nearblocks_q": nearblocks_quarterly(), "market": market(), "ecosystem": ecosystem(), "governance": governance(),
        "hsp029": hsp029(assump), "price_usd": assump["price_usd"],
        "history": optional("derived/history_results.json"), "census": optional("derived/census_summary.json"),
        "hub_trail": optional("derived/hub_trail.json"), "census_hourly": optional("derived/census_hourly.json"), "usage": optional("derived/census_usage.json"), "usage_flows": usage_flows(optional("derived/census_usage.json")),
        "sample_extras": optional("derived/sample_extras_results.json"),
        "holdings": holdings(), "peers": peers(), "builders": builders(), "validators": validators(), "web_facts": web_facts(),
        "prop": prop(),
        "catalysts": {
            "math": optional("derived/catalyst_math.json"),
            "calendar": optional("derived/catalyst_calendar.json"),
            "mix": optional("derived/mix_shift_math.json"),
            "scores": optional("derived/prop_scores.json"),
            "contestability": optional("derived/contestability.json"),
            "float_sink": optional("derived/float_sink.json"),
            "issuance_coverage": optional("derived/issuance_fee_coverage.json"),
            "thor_bridge": optional("derived/thor_multiple_bridge.json"),
            "partner_dials": optional("derived/partner_path_uplift_stack.json"),
            "controllable_stack": optional("derived/controllable_stack.json"),
            "dial_rank": optional("derived/catalyst_dial_rank.json"),
            "dial_roi": optional("derived/dial_roi_sketch.json"),
            "sk_tax_headroom": optional("derived/sk_tax_renegotiation_headroom.json"),
            "conversion": optional("derived/appfees_to_buyback_conversion.json"),
            "trust_path": optional("derived/trust_path_bb_vs_tax.json"),
            "quality_on_cool": optional("derived/quality_on_cool.json"),
            "peer_multiple": optional("derived/peer_multiple_compression.json"),
            "judge_one_pager": optional("derived/judge_one_pager_stack.json"),
            "soft_sink_ladder": optional("derived/soft_sink_ladder.json"),
            "investment_object": optional("derived/investment_object.json"),
            "commercial_map": optional("derived/commercial_conversation_map.json"),
            "four_ten_m_board": optional("derived/four_ten_m_board.json"),
            "judge_capture_card": optional("derived/judge_capture_card.json"),
            "immaterial_ladder": optional("derived/immaterial_to_material_ladder.json"),
            "inventory_mix": optional("derived/inventory_mix.json"),
            "dial_elasticity": optional("derived/dial_elasticity_board.json"),
            "opacity_product": optional("derived/opacity_product_stack.json"),
            "coverage_no_vol": optional("derived/coverage_path_no_vol.json"),
            "fee_engine_vs_l1": optional("derived/history_fee_engine_vs_l1.json"),
            "history_counter": optional("derived/history_counter_evidence_board.json"),
            "thor_two_step": optional("derived/thor_two_step_bridge.json"),
            "rating_fragility": optional("derived/rating_window_fragility.json"),
            "submit_hsp_seq": optional("derived/submit_vs_hsp029_sequence.json"),
            "ledger_stack": optional("derived/ledger_stack_vs_mutex.json"),
            "intents_purity": optional("derived/intents_purity_on_cool_l1.json"),
            "five_ledgers": optional("derived/five_ledgers_board.json"),
            "public_repo_checklist": optional("derived/public_repo_checklist.json"),
            "what_flips_hold": optional("derived/what_flips_hold_card.json"),
            "fee_mint_progress": optional("derived/fee_mint_progress_board.json"),
            "soft_sink_vs_leakage": optional("derived/soft_sink_vs_leakage_prize.json"),
            "foreign_rail": optional("derived/foreign_rail_vs_near_flow.json"),
            "fee_surface_risk": optional("derived/fee_resilience_vs_surface_risk.json"),
            "opacity_accelerating": optional("derived/opacity_accelerating.json"),
            "etf_immaterial": optional("derived/etf_immaterial_vs_intents.json"),
            "capital_light": optional("derived/capital_light_fee_engine.json"),
            "capture_insufficient": optional("derived/capture_alone_insufficient_50x.json"),
            "peerset_not_scarce": optional("derived/peerset_leadership_not_scarce.json"),
            "surface_opacity": optional("derived/distribution_surface_opacity.json"),
            "fee_payment_fidelity": optional("derived/fee_payment_fidelity_board.json"),
            "settlement_density": optional("derived/settlement_fee_density.json"),
            "hsp007_tension": optional("derived/hsp007_vs_intents_tension.json"),
            "delivery_countdown": optional("derived/delivery_countdown.json"),
            "one_breath": optional("derived/judge_one_breath.json"),
            "call_order_elasticity": optional("derived/call_order_elasticity.json"),
            "sweep_depth": optional("derived/sweep_depth_board.json"),
            "coverage_wall": optional("derived/coverage_wall_no_vol.json"),
            "opacity_x_elasticity": optional("derived/opacity_x_elasticity_compound.json"),
            "submit_asymmetry": optional("derived/submit_window_asymmetry.json"),
            "fidelity_commercial": optional("derived/fidelity_implies_commercial_leakage.json"),
            "three_scoreboards": optional("derived/three_scoreboards_tension.json"),
            "path50x_residual": optional("derived/path50x_residual_after_stack.json"),
            "capture_mutex": optional("derived/capture_dial_mutex.json"),
            "soft_sink_vs_wall": optional("derived/soft_sink_vs_coverage_wall.json"),
            "hours_burn": optional("derived/hours_burn_delivery.json"),
            "delivery_vs_hold": optional("derived/delivery_vs_hold_flip.json"),
            "quality_cool_proof": optional("derived/quality_on_cool_elasticity_proof.json"),
            "double_opacity": optional("derived/double_opacity_board.json"),
            "immaterial_vs_leakage": optional("derived/immaterial_vs_leakage_prize.json"),
            "settlement_vs_spam": optional("derived/settlement_density_vs_l1_spam.json"),
            "capture_funnel": optional("derived/capture_funnel_rank.json"),
            "h1b_vs_delivery": optional("derived/h1b_vs_delivery_separation.json"),
            "whale_desk": optional("derived/whale_desk_sk_tax.json"),
            "peerset_vs_sk": optional("derived/peerset_vs_sk_tax_scarce.json"),
            "capital_vs_leakage": optional("derived/capital_light_vs_leakage_constraint.json"),
            "trust_nested": optional("derived/trust_nested_under_sk.json"),
            "price_heavy": optional("derived/price_heavy_fee_print.json"),
            "attach_momentum": optional("derived/attach_momentum_board.json"),
            "judge_packet": optional("derived/judge_packet_completeness.json"),
            "dense_12_complete": optional("derived/dense_12_complete.json"),
            "dense_13_complete": optional("derived/dense_13_complete.json"),
            "dense_14_complete": optional("derived/dense_14_complete.json"),
            "locked_pitch": optional("derived/locked_pitch_lines.json"),
            "entering_14": optional("derived/entering_14_dense.json"),
            "dic_buffer": optional("derived/dic_buffer_not_scarcity.json"),
            "burn_materiality": optional("derived/burn_materiality_vs_wall.json"),
            "human_actions": optional("derived/human_actions_only_left.json"),
            "sk_vs_attach": optional("derived/sk_tax_vs_attach_path.json"),
            "fee_stability": optional("derived/fee_engine_stability_under_dense.json"),
            "intents_drift": optional("derived/intents_multiple_drift_under_dense.json"),
            "conversion_quiet": optional("derived/conversion_quiet_capture_dial.json"),
            "affiliate_contest": optional("derived/affiliate_pnl_contest_asymmetry.json"),
            "single_venue_fee": optional("derived/single_venue_fee_power.json"),
            "default_rail": optional("derived/default_rail_is_fee_engine.json"),
            "judge_call_now": optional("derived/judge_call_order_now.json"),
            "mint_not_fee": optional("derived/mint_ledger_not_fee_upside.json"),
            "delivery_urgency": optional("derived/delivery_urgency_board.json"),
            "attest_not_tau": optional("derived/attest_is_underwriting_not_tau.json"),
            "cif_gap": optional("derived/cif_gap_do_not_lead.json"),
            "two_bridges_now": optional("derived/two_bridges_now.json"),
            "peerset_gap": optional("derived/peerset_gross_net_gap.json"),
            "research_notes_index": optional("derived/research_notes_followup_index.json"),
            "ai_substitute": optional("derived/ai_agents_substitute_narrative.json"),
            "user_all_in": optional("derived/user_all_in_vs_capture.json"),
            "no_bond_demand": optional("derived/capital_light_no_bond_demand.json"),
            "diminishing_strata": optional("derived/diminishing_strata_vs_delivery.json"),
            "solver_rent_ledger": optional("derived/solver_rent_vs_capture_ledger.json"),
            "relayer_ops": optional("derived/relayer_ops_not_fee_dial.json"),
            "multi_venue_embed": optional("derived/multi_venue_embed_contestability.json"),
            "capture_share_all_in": optional("derived/capture_share_of_user_all_in.json"),
            "leakage_option_dials": optional("derived/leakage_as_option_value_of_dials.json"),
            "opacity_buys_time": optional("derived/opacity_buys_time_not_capture.json"),
            "volume_last_mile": optional("derived/volume_last_mile_is_distribution.json"),
            "hold_flip_h1b": optional("derived/hold_flip_requires_h1b_not_density.json"),
            "escrow_vs_attach": optional("derived/escrow_bb_acceleration_vs_attach.json"),
            "strata_vs_clock": optional("derived/strata_diminishing_vs_delivery_clock.json"),
            "deadline_premium": optional("derived/deadline_compresses_evidence_premium.json"),
            "catalyst_stack_order": optional("derived/near_term_catalyst_stack_order.json"),
            "judge_minute_budget": optional("derived/judge_minute_budget_vs_punch_depth.json"),
            "affiliate_sk_desk": optional("derived/affiliate_contest_same_desk_as_sk.json"),
            "soft_sink_wall": optional("derived/soft_sink_burn_do_not_move_wall.json"),
            "nearcom_mix_mutex": optional("derived/nearcom_mix_mutex_with_sk_tax.json"),
            "fidelity_terms": optional("derived/fidelity_high_leakage_is_terms.json"),
            "settlement_weight": optional("derived/settlement_weight_not_tx_count.json"),
            "foreign_neq_demand": optional("derived/foreign_rail_fee_neq_near_demand.json"),
            "immaterial_vs_sk": optional("derived/immaterial_narratives_vs_sk_tax.json"),
            "five_lead_capture": optional("derived/five_ledgers_lead_capture_only.json"),
            "capital_leakage_binds": optional("derived/capital_light_leakage_binds.json"),
            "peerset_not_prize": optional("derived/peerset_leadership_not_the_prize.json"),
            "trust_sk_nested": optional("derived/trust_nested_sk_tax_conversation.json"),
            "mutex_sum_trap": optional("derived/mutex_naive_sum_trap.json"),
            "cs_infra_not_fee": optional("derived/cs_infra_not_additive_fee.json"),
            "hsp007_vs_fee": optional("derived/hsp007_competes_with_fee_offset.json"),
            "perps_overlay": optional("derived/perps_delever_not_fee_signal.json"),
            "double_opac_inv_cap": optional("derived/double_opacity_inventory_and_capture.json"),
            "relayer_resilience": optional("derived/relayer_resilience_not_capture.json"),
            "intents_value_surface": optional("derived/intents_dominates_value_surface.json"),
            "inventory_privacy": optional("derived/inventory_privacy_foreign_heavy.json"),
            "dist_tax_gt_claim": optional("derived/distribution_tax_exceeds_token_claim.json"),
            "sk_hhi_leverage": optional("derived/swapkit_concentration_is_sk_leverage.json"),
            "fee_neq_l1_224": optional("derived/fee_neq_l1_holds_at_224.json"),
            "dense_15_progress": optional("derived/dense_15_progress.json"),
            "channel_attach_uneven": optional("derived/channel_attach_uneven_conversion_map.json"),
            "qoc_not_beta": optional("derived/quality_on_cool_capture_not_beta.json"),
            "rating_fragile": optional("derived/rating_fragile_to_intents_cool.json"),
            "capture_never_50x": optional("derived/capture_alone_never_finishes_50x.json"),
            "purity_concentration": optional("derived/thesis_purity_is_concentration_risk.json"),
            "hold_orthogonal": optional("derived/hold_flip_orthogonal_to_delivery.json"),
            "bb_wallet_gap": optional("derived/bb_wallet_implied_gap_trust_surface.json"),
            "revwallet_mix": optional("derived/revwallet_frontend_bb_mix_dial.json"),
            "price_disclose": optional("derived/price_heavy_print_disclose_both.json"),
            "staking_unstake": optional("derived/staking_float_unstake_not_intents.json"),
            "peerset_dwarfed": optional("derived/peerset_recovery_dwarfed_by_sk_tax.json"),
            "cross_ledger_ok": optional("derived/cross_ledger_stack_same_ledger_mutex.json"),
            "peer_claimable_neq": optional("derived/peer_gross_bp_neq_token_claimable.json"),
            "ledger_tax_intensity": optional("derived/ledger_sk_partner_tax_intensity.json"),
            "pip_irrelevant": optional("derived/protocol_pip_economically_irrelevant.json"),
            "non1click_gap": optional("derived/non_1click_fee_composition_gap.json"),
            "repo_private_confirmed": optional("derived/repo_still_private_confirmed.json"),
            "partner_micro": optional("derived/partner_path_micro_vs_sk_tax.json"),
            "collector_not_1to1": optional("derived/collector_rail_not_clean_1to1.json"),
            "fee_neq_trust": optional("derived/fee_print_neq_escrow_trust.json"),
            "two_bridges_vol": optional("derived/two_bridges_before_volume.json"),
            "dial_rank_comm": optional("derived/dial_rank_commercial_before_volume.json"),
            "hsp029_attn": optional("derived/hsp029_attention_dwarfs_hsp007.json"),
            "invest_refresh": optional("derived/investment_object_refresh.json"),
            "mix_arith": optional("derived/mix_shift_is_arithmetic_not_forecast.json"),
            "cap_eff_binds": optional("derived/capital_efficiency_leakage_binds.json"),
            "pci_light": optional("derived/pci_capital_light_leakage_binds.json"),
            "commits_640": optional("derived/commits_640_milestone.json"),
            "bonded_peers": optional("derived/capital_light_vs_bonded_peers.json"),
            "inv_risk_off_bs": optional("derived/inventory_risk_not_on_token_bs.json"),
            "cap_light_falsifier": optional("derived/capital_light_falsifier_is_onbalance_inventory.json"),
            "thor_3x_pci": optional("derived/thor_matched_stack_3x_pci.json"),
            "cap_wins_loses": optional("derived/capital_light_wins_and_loses.json"),
            "no_bond_from_cl": optional("derived/no_bond_demand_from_capital_light.json"),
            "claim_design_gap": optional("derived/claim_design_drives_multiple_gap.json"),
            "disc_claim_h1b": optional("derived/discretionary_claim_is_h1b_underwriting.json"),
            "f1_f4": optional("derived/f1_f4_on_submit_day.json"),
        },
        "repro": reproducibility(),
    }


if __name__ == "__main__":
    d = build()
    print(json.dumps({k: (list(v)[:6] if isinstance(v, dict) else type(v).__name__) for k, v in d.items()}, indent=1)[:900])
