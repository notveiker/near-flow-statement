"""Offline tests for sample metrics, estimators and the U1-U5 verdicts, on synthetic data with known answers."""
import random
import unittest

from pipeline import sample_metrics as sm


def tx(signer, receiver, fail=False, burnt=10**21):
    st = {"Failure": {}} if fail else {"SuccessReceiptId": "x"}
    return {"transaction": {"signer_id": signer, "receiver_id": receiver},
            "outcome": {"execution_outcome": {"outcome": {"status": st, "tokens_burnt": str(burnt)}}}}


def rcpt(receiver, fail=False, burnt=10**21):
    st = {"Failure": {}} if fail else {"SuccessValue": ""}
    return {"execution_outcome": {"outcome": {"status": st, "tokens_burnt": str(burnt)}}, "receipt": {"receiver_id": receiver}}


def block(txs, rcs):
    return {"block": {"header": {}}, "shards": [{"chunk": {"transactions": txs}, "receipt_execution_outcomes": rcs}, {"chunk": None, "receipt_execution_outcomes": []}]}


class TestBlockCounts(unittest.TestCase):
    def test_counts_signers_receivers_failures_burn_and_intents(self):
        b = block([tx("a", "x.near"), tx("b", "x.near", fail=True), tx("a", "y.near")],
                  [rcpt("intents.near"), rcpt("z.near", fail=True), rcpt("intents.near")])
        recv, sg = sm.Counter(), set()
        c = sm.block_counts(b, recv, sg)
        self.assertEqual((c["tx"], c["ok_tx"], c["receipts"], c["ok_receipts"], c["intents"]), (3, 2, 3, 2, 2))
        self.assertEqual(c["burnt_yocto"], 6 * 10**21)
        self.assertEqual(dict(recv), {"x.near": 2, "y.near": 1})
        self.assertEqual(sg, {"a", "b"})

    def test_cluster_row_handles_null_heights_and_truncates_receivers(self):
        cl = {"id": "Q_01", "stratum": "Q", "start": 10, "end": 12}
        rows = [{"h": 10, "b": block([tx("a", f"r{i}.near") for i in range(sm.TOP_KEEP + 5)], [])}, {"h": 11, "b": None},
                {"h": 12, "b": block([tx("b", "r0.near")], [rcpt("intents.near")])}]
        r = sm.cluster_row(cl, rows)
        self.assertEqual((r["heights"], r["null_heights"], r["tx"], r["signers"], r["intents"]), (3, 1, sm.TOP_KEEP + 6, 2, 1))
        self.assertEqual(len(r["receivers"]), sm.TOP_KEEP)
        self.assertEqual(sum(r["receivers"].values()) + r["receivers_other"], r["tx"])
        self.assertEqual(r["receivers"]["r0.near"], 2)


def synth(plan_strata, level, n=30, seed=1, top_share=None, signers=None):
    """Rows whose per-100-block tx count is Poisson-ish around level[stratum]."""
    rnd = random.Random(seed)
    rows = []
    for s in plan_strata:
        lam = level[s["id"]]
        for i in range(n):
            t = max(0, int(rnd.gauss(lam, lam * 0.2)))
            ts = (top_share or {}).get(s["id"], 0.2)
            rows.append({"id": f"{s['id']}_{i}", "stratum": s["id"], "start": i * 1000, "heights": 100, "null_heights": 0,
                         "tx": t, "ok_tx": int(t * 0.9), "receipts": 3 * t, "ok_receipts": int(2.7 * t), "intents": int(level.get("I_" + s["id"], 0) * rnd.uniform(0.8, 1.2)),
                         "burnt_near": t * 0.001, "signers": int(t * (signers or {}).get(s["id"], 0.5)),
                         "receivers": {"top.near": int(t * ts), **{f"o{j}.near": (t - int(t * ts)) // 10 for j in range(10)}}, "receivers_other": 0})
    return rows


DAY = 86_400 * 10**9


def mkstrata(ids, hpd=100_000):
    return [{"id": i, "h0": k * 9_000_000, "h1": k * 9_000_000 + hpd * 90 - 1, "t0_ns": k * 90 * DAY, "t1_ns": (k + 1) * 90 * DAY, "n": 30} for k, i in enumerate(ids)]


class TestEstimators(unittest.TestCase):
    ids = ["2025Q1", "2025Q3", "2026Q3"]

    def plan(self):
        return {"seed": "s", "strata": mkstrata(self.ids)}

    def test_per_day_scaling_uses_the_strata_block_rate(self):
        p = self.plan()
        rows = synth(p["strata"], {"2025Q1": 100, "2025Q3": 100, "2026Q3": 100}, n=5)
        boot = sm.bootstrap(p, rows, B=50)
        # 100 txs per 100 blocks = 1 tx per block; 100,000 blocks a day
        self.assertAlmostEqual(boot["2026Q3"]["point"]["tx_per_day"] / 100_000, 1.0, delta=0.2)

    def test_true_growth_passes_and_flat_fails(self):
        p = self.plan()
        grow = {"2025Q1": 50, "2025Q3": 100, "2026Q3": 220, "I_2025Q1": 10, "I_2025Q3": 30, "I_2026Q3": 60}
        v = sm.verdicts(sm.bootstrap(p, synth(p["strata"], grow, top_share={"2025Q3": 0.3, "2026Q3": 0.2}, signers={"2025Q3": 0.3, "2026Q3": 0.4}), B=300))
        self.assertEqual([v[k]["verdict"] for k in ("U1", "U2", "U3", "U4", "U5")], ["pass"] * 5)
        self.assertEqual(v["overall"], "supported by sampled history")
        flat = {"2025Q1": 100, "2025Q3": 100, "2026Q3": 105, "I_2025Q1": 10, "I_2025Q3": 10, "I_2026Q3": 10}
        v = sm.verdicts(sm.bootstrap(p, synth(p["strata"], flat), B=300))
        self.assertEqual(v["U1"]["verdict"], "fail")
        self.assertEqual(v["overall"], "not supported")

    def test_growth_carried_by_one_contract_fails_l2(self):
        p = self.plan()
        lvl = {"2025Q1": 50, "2025Q3": 100, "2026Q3": 300, "I_2025Q1": 10, "I_2025Q3": 20, "I_2026Q3": 50}
        rows = synth(p["strata"], lvl, top_share={"2025Q3": 0.2, "2026Q3": 0.8})
        v = sm.verdicts(sm.bootstrap(p, rows, B=300))
        self.assertEqual(v["U1"]["verdict"], "pass")
        self.assertEqual(v["U2"]["verdict"], "fail")
        self.assertEqual(v["overall"], "not supported")

    def test_missing_quarter_is_not_scorable_not_estimated(self):
        p = {"seed": "s", "strata": mkstrata(["2025Q1", "2025Q3"])}
        v = sm.verdicts(sm.bootstrap(p, synth(p["strata"], {"2025Q1": 50, "2025Q3": 100}), B=50))
        self.assertEqual(v["U1"]["verdict"], "not scorable")
        self.assertEqual(v["overall"], "not scorable")

    def test_bootstrap_is_deterministic(self):
        p = self.plan()
        rows = synth(p["strata"], {"2025Q1": 50, "2025Q3": 100, "2026Q3": 150})
        a = sm.ratio(sm.bootstrap(p, rows, B=200), "tx_per_day", "2026Q3", "2025Q3")
        b = sm.ratio(sm.bootstrap(p, rows, B=200), "tx_per_day", "2026Q3", "2025Q3")
        self.assertEqual(a, b)
        self.assertLess(a["lo90"], a["point"])
        self.assertGreater(a["hi90"], a["point"])

    def test_interval_covers_known_ratio_most_of_the_time(self):
        p = {"seed": "s", "strata": mkstrata(["2025Q3", "2026Q3"])}
        hits = 0
        for seed in range(40):
            rows = synth(p["strata"], {"2025Q3": 100, "2026Q3": 200}, n=25, seed=seed)
            r = sm.ratio(sm.bootstrap(p, rows, B=200), "tx_per_day", "2026Q3", "2025Q3")
            hits += r["lo90"] <= 2.0 <= r["hi90"]
        self.assertGreaterEqual(hits, 32)  # nominal 90%

    def test_counter_evidence_reports_falls_and_burn_share(self):
        p = self.plan()
        boot = sm.bootstrap(p, synth(p["strata"], {"2025Q1": 100, "2025Q3": 80, "2026Q3": 90}, n=10), B=50)
        t = sm.counter_evidence(boot, 88_295)
        self.assertIn("2025Q3", t["quarters_where_tx_per_day_fell"])
        self.assertIn("burn_share_of_issuance_2026Q3", t)


if __name__ == "__main__":
    unittest.main()
