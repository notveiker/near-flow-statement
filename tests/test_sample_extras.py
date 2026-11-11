import json
import unittest

from pipeline.sample_extras import block_extras


def ev(name, data):
    return "EVENT_JSON:" + json.dumps({"standard": "dip4", "event": name, "data": data})


def outcome(executor, logs=(), recv=None, method=None):
    rc = {"receiver_id": recv or executor}
    if method:
        rc["receipt"] = {"Action": {"actions": [{"FunctionCall": {"method_name": method}}]}}
    return {"receipt": rc, "execution_outcome": {"outcome": {"executor_id": executor, "logs": list(logs)}}}


class TestExtras(unittest.TestCase):
    def test_counts(self):
        blk = {"shards": [{"receipt_execution_outcomes": [
            outcome("intents.near", [ev("intents_executed", [{"account_id": "a"}, {"account_id": "b"}]), ev("token_diff", [{}]), ev("mt_mint", []), "plain log"]),
            outcome("intents.near", [ev("mt_burn", []), ev("mt_burn", [])]),
            outcome("v1.signer", recv="v1.signer", method="sign"),
            outcome("v1.signer", recv="v1.signer", method="other"),
            outcome("other.near", [ev("intents_executed", [{}])]),
        ]}]}
        c = block_extras(blk)
        self.assertEqual((c["executed"], c["intents"], c["token_diff"], c["deposits"], c["withdrawals"], c["signs"]), (1, 2, 1, 1, 2, 1))


if __name__ == "__main__":
    unittest.main()
