"""Week 7 reproduction: rebuild every software output from the definitions and compare.

One command runs, in order:
    1. every unit test
    2. the Week 5 exhaustive experiment   (configs/week5.json)
    3. the Week 6 optimization            (configs/week6.json, on the rebuilt matrices)
    4. the fault catalog
    5. the mutant audit
The rebuild happens in a clean folder (build/reproduction), starting from copies of the
definitions (configs/ and benchmarks/), so the committed results are never overwritten.
Each rebuilt output is then compared with the committed one. Run dates, commit IDs, and
timing are left out of the comparison because they always change; everything else must
match exactly.

Writes the test report to results/reproduction_report.txt and exits with code 1 if
anything fails.

Run from the repository root:
    python -m src.experiments.reproduce                  (uses configs/week7.json)
    python -m src.experiments.reproduce configs/week7.json
"""

import csv
import io
import json
import os
import platform
import shutil
import sys
import unittest
from datetime import date
from importlib import metadata

from src.experiments.experiment import git_commit

DEFAULT_CONFIG = "configs/week7.json"
PACKAGES = ("numpy", "matplotlib")


def environment():
    """Python version, operating system, and installed package versions."""
    lines = [f"python: {platform.python_version()}", f"platform: {platform.platform()}"]
    for name in PACKAGES:
        try:
            lines.append(f"{name}: {metadata.version(name)}")
        except metadata.PackageNotFoundError:
            lines.append(f"{name}: not installed")
    return lines


def run_unit_tests():
    """Run every test in tests/. Returns (tests run, failures, errors)."""
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(unittest.defaultTestLoader.discover("tests"))
    return result.testsRun, len(result.failures), len(result.errors)


def run_main(module_main, args):
    """Run a script's main() as if it were called from the command line."""
    saved = sys.argv
    sys.argv = ["reproduce"] + args
    try:
        module_main()
    finally:
        sys.argv = saved


def rebuild(config, build, today):
    """Copy the definitions into a clean folder and run every step there."""
    from src.experiments import experiment, optimize
    from src.faults_lib import fault_catalog, mutant_audit

    shutil.rmtree(build, ignore_errors=True)
    os.makedirs(build)
    shutil.copytree("configs", os.path.join(build, "configs"))
    shutil.copytree("benchmarks", os.path.join(build, "benchmarks"))

    # the Week 6 optimization reads the matrices rebuilt today, not the committed ones
    with open(config["week6_config"]) as file:
        week6 = json.load(file)
    week6["matrix_date"] = today
    with open(os.path.join(build, config["week6_config"]), "w") as file:
        json.dump(week6, file, indent=2)

    home = os.getcwd()
    os.chdir(build)
    try:
        run_main(experiment.main, [config["week5_config"]])
        run_main(optimize.main, [config["week6_config"]])
        run_main(fault_catalog.main, [])
        run_main(mutant_audit.main, [])
    finally:
        os.chdir(home)


def read_rows(path, skip_columns=()):
    """Read a CSV file as a list of rows, leaving out the named columns."""
    with open(path, newline="") as file:
        rows = list(csv.DictReader(file))
    return [{k: v for k, v in row.items() if k not in skip_columns} for row in rows]


def compare(config, build, today):
    """Compare every rebuilt output with the committed one. Returns a list of (check, passed, detail)."""
    with open(config["week5_config"]) as file:
        circuits = json.load(file)["circuits"]
    ref = config["week5_reference_date"]
    checks = []

    def file_check(name, pairs, same):
        bad = [old for old, new in pairs if not (os.path.exists(new) and same(old, new))]
        checks.append((name, not bad, f"{len(pairs) - len(bad)}/{len(pairs)} match" + (f"; differ: {bad}" if bad else "")))

    raw = [(f"results/raw/RUN_{c}_{ref}.csv", f"{build}/results/raw/RUN_{c}_{today}.csv") for c in circuits]
    file_check("Week 5 raw results", raw,
               lambda a, b: read_rows(a, ("run_id",)) == read_rows(b, ("run_id",)))

    matrix = [(f"results/matrix/RUN_{c}_{ref}.csv", f"{build}/results/matrix/RUN_{c}_{today}.csv") for c in circuits]
    file_check("Week 5 matrix source data", matrix, lambda a, b: open(a).read() == open(b).read())

    def log_lines(path):
        changing = ("run_id:", "date:", "commit:", "simulation time")
        return [line for line in open(path) if not line.startswith(changing)]
    logs = [(f"results/logs/RUN_{c}_{ref}.txt", f"{build}/results/logs/RUN_{c}_{today}.txt") for c in circuits]
    file_check("Week 5 run logs (counts and checks)", logs, lambda a, b: log_lines(a) == log_lines(b))

    summary = "results/optimization/week6_summary.csv"
    timing = ("run_id", "greedy_ms_min", "greedy_ms_mean", "greedy_ms_max", "exact_ms_min", "exact_ms_mean", "exact_ms_max")
    file_check("Week 6 selected vectors, exact status, re-simulation", [(summary, f"{build}/{summary}")],
               lambda a, b: read_rows(a, timing) == read_rows(b, timing))

    catalog = "results/fault_catalog.csv"
    file_check("Week 4 fault catalog", [(catalog, f"{build}/{catalog}")],
               lambda a, b: read_rows(a, ("run_id",)) == read_rows(b, ("run_id",)))

    audit = "results/mutant_audit.json"
    file_check("Week 4 mutant audit", [(audit, f"{build}/{audit}")],
               lambda a, b: json.load(open(a)) == json.load(open(b)))
    return checks


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG
    with open(path) as file:
        config = json.load(file)
    today = date.today().isoformat()
    build = config["build_folder"]

    print(f"\nReproduction {config['experiment']} ({path})")
    tests_run, failures, errors = run_unit_tests()
    rebuild(config, build, today)
    checks = compare(config, build, today)
    tests_ok = failures == 0 and errors == 0
    passed = tests_ok and all(ok for _, ok, _ in checks)

    lines = [
        "Reproduction report",
        f"experiment: {config['experiment']}",
        f"config: {path}",
        f"date: {today}",
        f"commit: {git_commit()}",
        f"build folder: {build}",
        "",
        "Environment",
    ] + [f"  {line}" for line in environment()] + [
        "",
        "Unit tests",
        f"  {'PASS' if tests_ok else 'FAIL'}  {tests_run} run, {failures} failures, {errors} errors",
        "",
        "Rebuilt outputs compared with committed results (run dates, commit IDs, and timing excluded)",
    ] + [f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}" for name, ok, detail in checks] + [
        "",
        f"RESULT: {'PASS' if passed else 'FAIL'}",
    ]
    os.makedirs(os.path.dirname(config["report"]), exist_ok=True)
    with open(config["report"], "w") as file:
        file.write("\n".join(lines) + "\n")
    print("\n" + "\n".join(lines))
    print(f"\nsaved {config['report']}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()