#!/usr/bin/env python3
"""Sweep a scheduler's class attributes and report the mark for each setting.

Copy this file into the root of the unzipped Short Order kit, then:

    python3 sweep.py my-scheduler/scheduler.py --set GAMMA=0.5,0.75,1.0 --set BETA=1.0 --detail

Each --set NAME=v1,v2,... is swept; NAME=v pins it. Every combination is run.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "student-sdk"))
from kitchen import Scheduler  # noqa: E402
from kitchen.runner import play  # noqa: E402

PROFILES = ["default", "rush", "one-cook", "brigade", "banquet-night",
            "bake-off", "blind", "service-line", "function"]


def cfg(p):
    return None if p == "default" else os.path.join(HERE, "configs", f"{p}.toml")


def load(path):
    spec = importlib.util.spec_from_file_location("cand", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for v in vars(mod).values():
        if isinstance(v, type) and issubclass(v, Scheduler) and v is not Scheduler:
            return v
    raise SystemExit("no scheduler class found")


def mark(cls, seeds, profiles):
    inst = cls()
    per = {}
    for prof in profiles:
        per[prof] = statistics.fmean(
            play(inst, s, config_path=cfg(prof), record_debug=False).result["score"]["total"]
            for s in seeds)
    return statistics.fmean(per.values()), per


def parse(v):
    for conv in (int, float):
        try:
            return conv(v)
        except ValueError:
            pass
    return {"True": True, "False": False}.get(v, v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--seeds", default="2000..2004")
    ap.add_argument("--profiles", default=",".join(PROFILES))
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--detail", action="store_true")
    args = ap.parse_args()

    a, _, b = args.seeds.partition("..")
    seeds = list(range(int(a), int(b))) if b else [int(a)]
    profiles = [p for p in args.profiles.split(",") if p]
    cls = load(args.path)

    names, grids = [], []
    for spec in args.set:
        name, _, vals = spec.partition("=")
        names.append(name)
        grids.append([parse(v) for v in vals.split(",")])

    base = {n: getattr(cls, n) for n in names}
    best = None
    for combo in itertools.product(*grids) if grids else [()]:
        for n, v in zip(names, combo):
            setattr(cls, n, v)
        m, per = mark(cls, seeds, profiles)
        label = " ".join(f"{n}={v}" for n, v in zip(names, combo)) or "base"
        line = f"{m:6.2f}  {label}"
        if args.detail:
            line += "   " + " ".join(f"{p[:4]}:{per[p]:.1f}" for p in profiles)
        print(line, flush=True)
        if best is None or m > best[0]:
            best = (m, label)
    for n, v in base.items():
        setattr(cls, n, v)
    if best:
        print(f"\nbest {best[0]:.2f}  {best[1]}")


if __name__ == "__main__":
    main()
