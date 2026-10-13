#!/usr/bin/env python3
"""Funnel + segment analysis for the product-designer-005 onboarding fixture.

Usage:
    python3 my-submissions/product-designer-005/analyze_sessions.py \
        challenges/product-designer-005/fixtures/onboarding_sessions.csv

It answers three questions:
1. Where do in-ICP, self-serve users stall, and why (from their verbatims)?
2. Does "completed onboarding" actually predict day-14 activity?
3. Which rows should NOT drive the redesign at face value?

Stdlib only. Every number it prints is [Observed] from the CSV. With n=16,
read them as direction, not effect size.
"""
from __future__ import annotations

import csv
import hashlib
import sys
from collections import Counter
from pathlib import Path

ICP = range(10, 101)  # brief: creative agencies with 10-100 employees


def yes(v: str) -> bool:
    return v.strip().lower() == "yes"


def rate(rows, pred) -> str:
    n = len(rows)
    k = sum(1 for r in rows if pred(r))
    return f"{k}/{n}" + (f" ({100 * k / n:.0f}%)" if n else "")


def main(path: str) -> None:
    p = Path(path)
    rows = list(csv.DictReader(p.open()))
    for r in rows:
        for k in ("company_size", "step_reached", "time_spent_min", "teammates_invited",
                  "integrations_connected"):
            r[k] = int(r[k])
    print(f"fixture sha256: {hashlib.sha256(p.read_bytes()).hexdigest()}")
    print(f"sessions: {len(rows)}\n")

    # --- Segments ------------------------------------------------------------
    invited = [r for r in rows if r["signup_source"] == "teammate invite"]
    off_icp = [r for r in rows if r["company_size"] not in ICP]
    # S-05 says it's a second attempt after abandoning last week; S-01 matches
    # its persona, company size, and source. Treat as the same person.
    repeat = [r for r in rows if "second try" in r["verbatim"].lower()]
    core = [r for r in rows if r not in invited and r not in off_icp]

    print("segments")
    print(f"  joined via teammate invite (different flow): {[r['session_id'] for r in invited]}")
    print(f"  outside 10-100 ICP: {[(r['session_id'], r['company_size']) for r in off_icp]}")
    print(f"  probable repeat user: {[r['session_id'] for r in repeat]} (likely same person as S-01)")
    print(f"  core self-serve ICP sessions: {len(core)}\n")

    # --- Where core users stop ----------------------------------------------
    print("core: last step reached by non-completers")
    stops = Counter(r["step_reached"] for r in core if not yes(r["completed_onboarding"]))
    for step in sorted(stops):
        ids = [r["session_id"] for r in core
               if r["step_reached"] == step and not yes(r["completed_onboarding"])]
        print(f"  step {step}: {stops[step]}  {ids}")
    print()

    # --- Completion vs value -------------------------------------------------
    comp = [r for r in rows if yes(r["completed_onboarding"])]
    noncomp = [r for r in rows if not yes(r["completed_onboarding"])]
    print("completion vs day-14 activity (all sessions)")
    print(f"  completed, active d14:     {rate(comp, lambda r: yes(r['active_day_14']))}")
    print(f"  not completed, active d14: {rate(noncomp, lambda r: yes(r['active_day_14']))}")
    print(f"  completed but inactive d14: "
          f"{[r['session_id'] for r in comp if not yes(r['active_day_14'])]}")
    print(f"  never completed but active d14: "
          f"{[r['session_id'] for r in noncomp if yes(r['active_day_14'])]}")
    reached4 = [r for r in rows if r["step_reached"] >= 4]
    print(f"  reached step 4 (first project), active d14: "
          f"{rate(reached4, lambda r: yes(r['active_day_14']))}")
    below4 = [r for r in rows if r["step_reached"] < 4]
    print(f"  stopped before step 4, active d14: {rate(below4, lambda r: yes(r['active_day_14']))}\n")

    # --- The brief's integration claim, checked -----------------------------
    hi = [r for r in rows if r["integrations_connected"] >= 2]
    lo = [r for r in rows if r["integrations_connected"] < 2]
    print("integrations >= 2 vs < 2, active d14 (brief claims 3x retention)")
    print(f"  >=2: {rate(hi, lambda r: yes(r['active_day_14']))}")
    print(f"  <2:  {rate(lo, lambda r: yes(r['active_day_14']))}")
    lo_reached = [r for r in lo if r["step_reached"] >= 4]
    print(f"  <2 but reached a project: {rate(lo_reached, lambda r: yes(r['active_day_14']))}\n")

    # --- Single-voice and blocker rows ---------------------------------------
    print("rows needing special handling")
    flags = {
        "accessibility blocker (defect, fix regardless of n)": "keyboard",
        "SSO / admin-first requirement (sales-led path)": "sso",
        "minority-of-one: wants MORE hand-holding": "more hand-holding",
        "contradiction: invite step skippable via tiny link": "tiny link",
        "contradiction: invite step reported as hard-blocking": "wouldn't let me",
        "completion != value: existing tool habit": "spreadsheets",
    }
    for label, needle in flags.items():
        ids = [r["session_id"] for r in rows if needle in r["verbatim"].lower()]
        print(f"  {label}: {ids}")
    slow = sorted(rows, key=lambda r: -r["time_spent_min"])[:3]
    print(f"  slowest sessions: {[(r['session_id'], r['time_spent_min']) for r in slow]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1
         else "challenges/product-designer-005/fixtures/onboarding_sessions.csv")
