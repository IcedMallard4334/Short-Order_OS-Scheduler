#!/usr/bin/env python3
"""Bench: run a scheduler over every marking profile and report the mark.

The marking formula from the student guide:
    "Your mark is the mean over profiles of your mean score per profile."

Copy this file into the root of the unzipped Short Order kit, then:

    python3 bench.py <spec> [--seeds 2000..2012] [--profiles default,rush,...]

<spec> is a scheduler file (my-scheduler/scheduler.py) or a reference name
(gordon_ramsay, julia_child, ...).
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "student-sdk"))

from kitchen.runner import play  # noqa: E402

PROFILES = [
    "default", "rush", "one-cook", "brigade", "banquet-night",
    "bake-off", "blind", "service-line", "function",
]


def cfg(profile):
    return None if profile == "default" else os.path.join(HERE, "configs", f"{profile}.toml")


def run_set(spec, profiles, seeds, verbose=True):
    per_profile = {}
    for prof in profiles:
        scores = [float(play(spec, seed, config_path=cfg(prof), record_debug=False)
                        .result["score"]["total"]) for seed in seeds]
        per_profile[prof] = statistics.fmean(scores)
        if verbose:
            sd = statistics.pstdev(scores) if len(scores) > 1 else 0.0
            print(f"  {prof:<14} {per_profile[prof]:6.2f}  (sd {sd:4.2f})", flush=True)
    mark = statistics.fmean(per_profile.values())
    if verbose:
        print(f"  {'MARK':<14} {mark:6.2f}", flush=True)
    return mark, per_profile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--seeds", default="2000..2006")
    ap.add_argument("--profiles", default=",".join(PROFILES))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    start, _, end = args.seeds.partition("..")
    seeds = list(range(int(start), int(end))) if end else [int(start)]
    profiles = [p for p in args.profiles.split(",") if p]

    print(f"{args.spec}  seeds {seeds[0]}..{seeds[-1]} ({len(seeds)})", flush=True)
    mark, per = run_set(args.spec, profiles, seeds)
    if args.json:
        print(json.dumps({"mark": mark, "profiles": per}))


if __name__ == "__main__":
    main()
