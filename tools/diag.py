#!/usr/bin/env python3
"""Per-profile component breakdown, optionally side by side with a reference.

Copy this file into the root of the unzipped Short Order kit, then:

    python3 diag.py my-scheduler/scheduler.py --vs gordon_ramsay --seeds 3000..3010
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "student-sdk"))
from kitchen.runner import play  # noqa: E402

PROFILES = ["default", "rush", "one-cook", "brigade", "banquet-night",
            "bake-off", "blind", "service-line", "function"]
COMPS = ["completion", "response", "turnaround", "slowdown", "switching", "fairness"]


def cfg(p):
    return None if p == "default" else os.path.join(HERE, "configs", f"{p}.toml")


def collect(spec, profiles, seeds):
    out = {}
    for prof in profiles:
        rs = [play(spec, s, config_path=cfg(prof), record_debug=False).result for s in seeds]
        agg = {c: statistics.fmean(r["score"][c] for r in rs) for c in COMPS}
        agg["total"] = statistics.fmean(r["score"]["total"] for r in rs)
        m = lambda k: statistics.fmean(r["metrics"][k] for r in rs)  # noqa: E731
        agg["_raw"] = {
            "served%": 100 * m("completion"),
            "resp": statistics.fmean(r["metrics"]["response"]["mean"] for r in rs),
            "turn": statistics.fmean(r["metrics"]["turnaround"]["mean"] for r in rs),
            "bslow": statistics.fmean(r["metrics"]["bounded_slowdown"]["mean"] for r in rs),
            "sw": m("context_switches"),
            "extra": m("extra_switches"),
            "preempt": m("preemptions"),
            "bumps": m("station_bumps"),
            "nostart": m("never_started"),
            "invalid": statistics.fmean(r.get("invalid_assignments", 0) for r in rs),
            "slowms": statistics.fmean(r["decision_time_ms"]["max_ms"] for r in rs),
        }
        out[prof] = agg
    return out


def show(name, data, other=None):
    print(f"\n=== {name} ===")
    print(f"{'profile':<14}{'total':>7}" + "".join(f"{c[:5]:>7}" for c in COMPS))
    for prof, a in data.items():
        line = f"{prof:<14}{a['total']:7.2f}" + "".join(f"{a[c]:7.3f}" for c in COMPS)
        if other:
            line += f"   Δ{a['total'] - other[prof]['total']:+6.2f}"
        print(line)
    print(f"{'MEAN':<14}{statistics.fmean(a['total'] for a in data.values()):7.2f}")
    print("  raw:")
    for prof, a in data.items():
        r = a["_raw"]
        print(f"   {prof:<14} served {r['served%']:5.1f}%  resp {r['resp']:6.1f}  "
              f"turn {r['turn']:6.1f}  bslow {r['bslow']:5.2f}  sw {r['sw']:6.1f}"
              f"(+{r['extra']:5.1f})  pre {r['preempt']:5.1f} bump {r['bumps']:5.1f} "
              f"nostart {r['nostart']:4.1f} inv {r['invalid']:.1f} ms {r['slowms']:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--vs", default=None)
    ap.add_argument("--seeds", default="2000..2005")
    ap.add_argument("--profiles", default=",".join(PROFILES))
    args = ap.parse_args()
    a, _, b = args.seeds.partition("..")
    seeds = list(range(int(a), int(b))) if b else [int(a)]
    profiles = [p for p in args.profiles.split(",") if p]

    other = collect(args.vs, profiles, seeds) if args.vs else None
    mine = collect(args.spec, profiles, seeds)
    if other:
        show(args.vs, other)
    show(args.spec, mine, other)


if __name__ == "__main__":
    main()
