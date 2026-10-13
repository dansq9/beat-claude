#!/usr/bin/env python3
"""Risk-tier + triage engine for the ops-coo-009 review queue fixture.

Usage:
    python3 my-submissions/ops-coo-009/tier_queue.py \
        challenges/ops-coo-009/fixtures/review_queue_snapshot.csv

How it works
- Every queue item gets six yes/no risk fields. In production the automation
  layer would emit these fields itself; the fixture doesn't have them, so I
  tagged them by hand from each item's summary (FEATURES below). Those tags
  are my judgment and are what a reviewer should argue with.
- A fixed decision tree (tier()) turns the fields into GREEN / YELLOW / RED.
  The tree never reads the automation's own `current_tier_guess`; it only
  compares against it, to measure how often the automation mis-tiers.
- Hygiene detectors (duplicates, false-done, unowned + aged, alert floods,
  dead-account targets) run before tiering. They decide whether an item is
  worked, merged, or closed.

Stdlib only. Output is deterministic for a given CSV.
"""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

# --- Risk fields, hand-tagged per item (judgment, labeled [Estimated]) -------
# legal:        changes a contract, liability, or compliance position
# confidential: moves client data/numbers outside the client relationship
# top_account:  a top-tier account relationship is at stake
# external:     sends something to a person outside the company
# revenue:      a live revenue opportunity or renewal is at stake
# irreversible: can't be cleanly undone once sent or executed
FEATURES = {
    "Q-01": dict(top_account=1, revenue=1),                  # enterprise renewal in 45d
    "Q-02": dict(external=1, irreversible=1),                # outreach drafts
    "Q-03": dict(external=1),                                # social drafts
    "Q-04": dict(external=1, revenue=1),                     # warm revival signal
    "Q-05": dict(),                                          # competitor price alert
    "Q-06": dict(external=1),                                # lost finalist
    "Q-07": dict(),                                          # SEO recs, already in review
    "Q-08": dict(external=1, irreversible=1),                # wrong-name auto-send
    "Q-09": dict(top_account=1, revenue=1),                  # duplicate of Q-01
    "Q-10": dict(),                                          # editorial calendar
    "Q-11": dict(legal=1, top_account=0, revenue=1, irreversible=1),  # auto-renew liability
    "Q-12": dict(),                                          # competitor AI feature alert
    "Q-13": dict(external=1, revenue=1),                     # false-done revival
    "Q-14": dict(),                                          # churned-client recs
    "Q-15": dict(top_account=1, revenue=1, external=1),      # top-3 CMO disengaged
    "Q-16": dict(confidential=1, external=1, irreversible=1),  # client numbers in newsletter
    "Q-17": dict(external=1, irreversible=1),                # duplicate prospect batch
    "Q-18": dict(external=1, confidential=0, legal=0, top_account=1),  # candidates at clients
}

# SLA by tier, in days, for an item to have a named owner AND a decision.
SLA_DAYS = {"RED": 1, "YELLOW": 2, "GREEN": 5}
ALERT_FLOOD_THRESHOLD = 10  # similar alerts/week above which a stream goes to digest


def tier(f: dict) -> tuple[str, str]:
    """Decision tree. Returns (tier, reason). First matching rule wins."""
    if f.get("legal"):
        return "RED", "legal/contract term change"
    if f.get("confidential") and f.get("external"):
        return "RED", "client-confidential data would leave the relationship"
    if f.get("top_account") and f.get("revenue"):
        return "RED", "top-account revenue at risk"
    if f.get("external") and f.get("irreversible"):
        return "YELLOW", "irreversible external send"
    if f.get("external") or f.get("revenue") or f.get("top_account"):
        return "YELLOW", "external-facing or revenue-touching"
    return "GREEN", "internal, reversible"


def needs_exec(f: dict) -> bool:
    """RED goes to a named senior owner. The exec is pulled in only for a
    legal position change or an exec-to-exec relationship move on a top account."""
    return bool(f.get("legal") or (f.get("top_account") and f.get("external") and f.get("revenue")))


def route(t: str) -> str:
    return {
        "RED": "named senior owner acts <24h; exec sponsor decides only the one irreversible call",
        "YELLOW": "department operator reviews + sends <48h; no exec",
        "GREEN": "auto-execute or batch into weekly digest; sampled 10%/week",
    }[t]


def hygiene(rows: list[dict]) -> dict[str, list[str]]:
    """Flags that change *whether* an item is worked, independent of tier."""
    flags: dict[str, list[str]] = {r["item_id"]: [] for r in rows}
    for r in rows:
        s, iid = r["summary"].lower(), r["item_id"]
        if s.startswith("duplicate") or "overlapping" in s:
            flags[iid].append("DUPLICATE: merge into parent, don't double-work")
        if r["status"] == "done" and ("no email" in s or "wrong" in s):
            flags[iid].append("FALSE-DONE: status says done, outcome says otherwise")
        if r["owner"] == "unassigned" and int(r["created_days_ago"]) >= 5:
            flags[iid].append(f"UNOWNED {r['created_days_ago']}d: assign today")
        if "alert" in s:
            n = [int(w) for w in s.replace(";", " ").split() if w.isdigit()]
            if n and max(n) >= ALERT_FLOOD_THRESHOLD:
                flags[iid].append(f"ALERT FLOOD ({max(n)}/wk): route stream to weekly digest")
        if "churned" in s:
            flags[iid].append("DEAD TARGET: client churned; close + fix account-status feed")
        if r["owner"] == "exec sponsor":
            flags[iid].append("EXEC AS OWNER: move ownership to account lead, keep exec for one decision")
    return flags


def main(path: str) -> None:
    p = Path(path)
    rows = list(csv.DictReader(p.open()))
    print(f"fixture sha256: {hashlib.sha256(p.read_bytes()).hexdigest()}")
    print(f"items: {len(rows)}\n")
    flags = hygiene(rows)
    out, mistier = [], 0
    for r in rows:
        t, why = tier(FEATURES[r["item_id"]])
        guess = r["current_tier_guess"].upper()
        if guess != t:
            mistier += 1
        breach = int(r["created_days_ago"]) > SLA_DAYS[t] and r["status"] != "in_review"
        out.append((r, t, why, guess, breach))
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2}
    out.sort(key=lambda x: (order[x[1]], -int(x[0]["created_days_ago"])))
    for r, t, why, guess, breach in out:
        mark = "" if guess == t else f"  (automation said {guess})"
        print(f"{r['item_id']}  {t:<6} age={r['created_days_ago']:>2}d  owner={r['owner']:<13}"
              f"{' SLA-BREACH' if breach else ''}{mark}")
        print(f"       why: {why}")
        for fl in flags[r["item_id"]]:
            print(f"       flag: {fl}")
    counts = {k: sum(1 for x in out if x[1] == k) for k in order}
    unowned = sum(1 for r in rows if r["owner"] == "unassigned")
    print("\nsummary")
    print(f"  tiers: RED={counts['RED']} YELLOW={counts['YELLOW']} GREEN={counts['GREEN']}")
    print(f"  automation tier guess disagrees with tree: {mistier}/{len(rows)}")
    print(f"  unassigned: {unowned}/{len(rows)}")
    print(f"  SLA breaches: {sum(1 for x in out if x[4])}/{len(rows)}")
    dupes = {iid for iid, fl in flags.items() if any(f.startswith("DUPLICATE") for f in fl)}
    print(f"  duplicates merged: {len(dupes)} ({', '.join(sorted(dupes))})")
    exec_items = [x[0]["item_id"] for x in out if x[1] == "RED" and needs_exec(FEATURES[x[0]["item_id"]])
                  and x[0]["item_id"] not in dupes]
    print(f"  exec sponsor decisions needed: {len(exec_items)} ({', '.join(exec_items)}) "
          f"vs {len(rows)} if the exec reviews the whole queue")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1
         else "challenges/ops-coo-009/fixtures/review_queue_snapshot.csv")
