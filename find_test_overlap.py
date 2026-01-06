#!/usr/bin/env -S uv run
# /// script
# dependencies = ["coverage", "pytest", "pytest-cov"]
# ///
import os
import subprocess
import sys
from collections import defaultdict

import coverage


def run_coverage(target_dir="tests/application"):
    print(f"Running overlap analysis for {target_dir}...")
    env = os.environ.copy()
    env["COVERAGE_FILE"] = ".coverage.overlap"

    # Minimal pytest plugin to switch contexts
    # We write it to a file so we can load it with -p
    with open("context_plugin.py", "w") as f:
        f.write("""
import coverage
def pytest_runtest_setup(item):
    cov = coverage.Coverage.current()
    if cov:
        cov.switch_context(item.nodeid)
""")

    cmd = [
        "uv",
        "run",
        "coverage",
        "run",
        "--source=simple_agent",
        "-m",
        "pytest",
        target_dir,
        "-p",
        "context_plugin",
        "-p",
        "no:cov",
        "-n",
        "0",
        "-q",
        "--no-summary",
    ]
    try:
        subprocess.run(cmd, env=env, check=True)
    finally:
        if os.path.exists("context_plugin.py"):
            os.remove("context_plugin.py")


def analyze(threshold=3):
    if not os.path.exists(".coverage.overlap"):
        print("No coverage data found.")
        return

    data = coverage.CoverageData(".coverage.overlap")
    data.read()

    overlap_map = defaultdict(lambda: defaultdict(int))
    for file in data.measured_files():
        contexts = data.contexts_by_lineno(file)
        for line, ctxs in contexts.items():
            # Filter for pytest nodeids (contain ::)
            active = [c for c in ctxs if "::" in c]
            if len(active) >= threshold:
                overlap_map[file][line] = len(active)

    if not overlap_map:
        print(f"No overlap found >= {threshold}")
        return

    print(f"Overlap Analysis (Threshold {threshold}):")
    for file in sorted(overlap_map.keys()):
        rel = os.path.relpath(file)
        lines = overlap_map[file]
        print(f"\n{rel}")
        counts = defaultdict(list)
        for ln, c in lines.items():
            counts[c].append(ln)
        for c in sorted(counts.keys(), reverse=True):
            print(f"  [{c} tests]: lines {format_ranges(counts[c])}")


def format_ranges(nums):
    nums = sorted(nums)
    if not nums:
        return ""
    ranges = []
    s = e = nums[0]
    for i in range(1, len(nums)):
        if nums[i] == e + 1:
            e = nums[i]
        else:
            ranges.append(f"{s}-{e}" if s != e else f"{s}")
            s = e = nums[i]
    ranges.append(f"{s}-{e}" if s != e else f"{s}")
    return ", ".join(ranges)


if __name__ == "__main__":
    # Usage: python analyze_test_overlap.py [threshold] [target_path]
    threshold = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    target = sys.argv[2] if len(sys.argv) > 2 else "tests/"

    if not os.path.exists(".coverage.overlap"):
        run_coverage(target)
    analyze(threshold)
