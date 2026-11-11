import json
import unittest

from pipeline.census_usage import merge, report, shard_usage, target_of


def tx(recv, actions, status=None, outs=()):
    return {"transaction": {"receiver_id": recv, "signer_id": "s", "actions": actions}, "status": status or {"SuccessValue": ""},
            "receipts_outcome": list(outs)}


def oc(ex, gas=10, logs=(), status=None):
    return {"outcome": {"executor_id": ex, "gas_burnt": gas, "tokens_burnt": str(gas * 10**12), "logs": list(logs), "status": status or {"SuccessValue": ""}}}


class T(unittest.TestCase):
    def test_target_delegate(self):
        a = [{"Delegate": {"delegate_action": {"receiver_id": "game.near", "actions": [{"FunctionCall": {"method_name": "go"}}]}}}]
        self.assertEqual(target_of({"receiver_id": "user.near", "actions": a}), ("game.near", True, "go"))
        self.assertEqual(target_of({"receiver_id": "x", "actions": [{"Transfer": {}}]}), ("x", False, None))

    def test_usage(self):
        ev = "EVENT_JSON:" + json.dumps({"standard": "nep141", "event": "ft_transfer", "data": [{"amount": "2500000"}, {"amount": "500000"}]})
        blk = {"b": {"txs": {
            "1": tx("intents.near", [{"FunctionCall": {"method_name": "execute_intents"}}], outs=[oc("intents.near", 30)]),
            "2": tx("usdt.tether-token.near", [{"FunctionCall": {"method_name": "ft_transfer"}}], outs=[oc("usdt.tether-token.near", 10, [ev])]),
            "3": tx("v1.signer", [{"FunctionCall": {"method_name": "sign"}}], status={"Failure": {}}, outs=[oc("v1.signer", 10)]),
        }}}
        diff = "EVENT_JSON:" + json.dumps({"event": "token_diff", "data": [{"diff": {"nep141:a": "-100", "nep141:b": "90"}, "fees_collected": {"nep141:a": "1"}, "referral": "ref.tg"}]})
        mint = "EVENT_JSON:" + json.dumps({"event": "mt_mint", "data": [{"token_ids": ["nep141:a"], "amounts": ["7"], "memo": "deposit"}]})
        burn = "EVENT_JSON:" + json.dumps({"event": "mt_burn", "data": [{"token_ids": ["nep141:a"], "amounts": ["3"], "memo": "withdraw"}]})
        blk["b"]["txs"]["4"] = tx("intents.near", [{"FunctionCall": {"method_name": "execute_intents"}}], outs=[oc("intents.near", 5, [diff, mint, burn])])
        r = report(merge([shard_usage([blk])]), 1, 2)
        self.assertEqual(r["flows"]["nep141:a"], {"swap_out": "100", "fees": "1", "deposit": "7", "withdraw": "3"})
        self.assertEqual(r["flows"]["nep141:b"], {"swap_in": "90"})
        self.assertEqual(r["referrals"], {"ref.tg": 1})
        self.assertEqual(r["txs"], 4)
        self.assertAlmostEqual(r["ok_share"], 3 / 4)
        self.assertEqual(r["stablecoins"]["USDT"], {"transfers": 2, "usd": 3.0})
        self.assertEqual(r["methods"]["v1.signer"], {"sign": 1})
        self.assertAlmostEqual(r["gas_burners"][0]["gas_share"], 35 / 55)


if __name__ == "__main__":
    unittest.main()
