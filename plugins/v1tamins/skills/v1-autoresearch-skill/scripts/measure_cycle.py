#!/usr/bin/env python3
"""Measure one AutoResearch cycle: run the metric N times, take the median,
compare it to the best-known score, and append one row to the results log.

Prints one JSON object on stdout. Exit codes: 0 measured (any verdict),
2 usage or measurement error (nothing logged).
"""

import argparse
import datetime
import json
import os
import re
import statistics
import subprocess
import sys

LOG_HEADER = ["timestamp", "cycle", "change", "metric_before", "metric_after", "verdict"]
NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


def fail(message):
    print(json.dumps({"ok": False, "error": message}))
    sys.exit(2)


def run_metric(command):
    proc = subprocess.run(command, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:
        fail(f"metric command exited {proc.returncode}: {proc.stderr.strip()[-500:]}")
    numbers = NUMBER.findall(proc.stdout)
    if not numbers:
        fail("metric command printed no number on stdout")
    return float(numbers[-1])


def append_log(path, row):
    new_file = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", encoding="utf-8") as handle:
        if new_file:
            handle.write("\t".join(LOG_HEADER) + "\n")
        clean = [str(value).replace("\t", " ").replace("\n", " ") for value in row]
        handle.write("\t".join(clean) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run one AutoResearch measurement. Without --best, records the baseline. "
            "With --best, runs the optional constraint, measures, compares, and logs "
            "KEPT or DISCARDED. The caller reverts the commit when verdict is DISCARDED."
        )
    )
    parser.add_argument("--metric", required=True, help="shell command whose last stdout number is the score")
    parser.add_argument("--direction", required=True, choices=["lower", "higher"], help="which way is better")
    parser.add_argument("--runs", type=int, default=3, help="metric runs per measurement; median is used (default 3)")
    parser.add_argument("--best", type=float, help="best-known score; omit to record the baseline")
    parser.add_argument("--constraint", help="shell command that must exit 0 before measuring")
    parser.add_argument("--cycle", type=int, default=0, help="cycle number for the log row (default 0)")
    parser.add_argument("--change", default="baseline", help="one-line description of the change")
    parser.add_argument("--log", default="autoresearch-results.tsv", help="results log path (default autoresearch-results.tsv)")
    args = parser.parse_args()

    if args.runs < 1:
        fail("--runs must be at least 1")

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    result = {"ok": True, "cycle": args.cycle, "change": args.change, "best_before": args.best}

    if args.best is not None and args.constraint:
        constraint = subprocess.run(args.constraint, shell=True, capture_output=True, text=True)
        if constraint.returncode != 0:
            append_log(args.log, [timestamp, args.cycle, args.change, args.best, "CONSTRAINT_FAIL", "DISCARDED"])
            result.update(verdict="DISCARDED", reason="constraint_failed", constraint_exit=constraint.returncode,
                          best_after=args.best, log=args.log)
            print(json.dumps(result))
            return

    samples = [run_metric(args.metric) for _ in range(args.runs)]
    score = statistics.median(samples)
    result.update(samples=samples, median=score)

    if args.best is None:
        append_log(args.log, [timestamp, args.cycle, args.change, "", score, "BASELINE"])
        result.update(verdict="BASELINE", best_after=score, log=args.log)
        print(json.dumps(result))
        return

    improved = score < args.best if args.direction == "lower" else score > args.best
    verdict = "KEPT" if improved else "DISCARDED"
    change_pct = None if args.best == 0 else round((score - args.best) / abs(args.best) * 100, 2)
    append_log(args.log, [timestamp, args.cycle, args.change, args.best, score, verdict])
    result.update(verdict=verdict, best_after=score if improved else args.best, change_pct=change_pct, log=args.log)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
