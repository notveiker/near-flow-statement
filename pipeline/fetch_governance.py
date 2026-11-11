"""NEAR governance activity from the public forum (Discourse JSON, no key): topics created per month, views, replies,
and the list of HSP proposals. Pages through /latest.json politely.

Run: python3 -m pipeline.fetch_governance
"""
from __future__ import annotations

import time

from .common import http_json, write_raw

FORUM = "https://gov.near.org"


def main() -> None:
    topics, page = [], 0
    while page < 60:
        d = http_json(f"{FORUM}/latest.json", {"page": page, "order": "created"})
        ts = d["topic_list"]["topics"]
        if not ts:
            break
        topics += [{k: t.get(k) for k in ("id", "title", "created_at", "posts_count", "reply_count", "views", "like_count", "category_id", "tags")} for t in ts]
        page += 1
        time.sleep(1.5)
    seen = {t["id"]: t for t in topics}
    topics = sorted(seen.values(), key=lambda t: t["created_at"])
    cats = http_json(f"{FORUM}/categories.json")["category_list"]["categories"]
    write_raw("governance/topics.json", topics, "gov.near.org latest.json, paged")
    write_raw("governance/categories.json", [{k: c.get(k) for k in ("id", "name", "topic_count", "post_count")} for c in cats], "gov.near.org categories.json")
    top = http_json(f"{FORUM}/top.json", {"period": "yearly"})["topic_list"]["topics"]
    write_raw("governance/top_yearly.json", [{k: t.get(k) for k in ("id", "title", "created_at", "posts_count", "views", "like_count")} for t in top], "gov.near.org top.json yearly")
    print(f"governance: {len(topics)} topics, {len(cats)} categories")


if __name__ == "__main__":
    main()
