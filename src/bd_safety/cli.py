import argparse
import json
from pathlib import Path
import sys
import unittest

from .config import REPORTS, ROOT


def check():
    from .acquisition import write_json
    from .validation import validate

    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    tests = unittest.TextTestRunner(verbosity=2).run(suite)
    unit = {
        "tests_run": tests.testsRun,
        "failures": len(tests.failures),
        "errors": len(tests.errors),
        "passed": tests.wasSuccessful(),
    }
    write_json(REPORTS / "test_results.json", unit)
    if not unit["passed"]:
        raise RuntimeError("Software unit checks failed")
    return {"unit": unit, "real_data_validation": validate()}


def main():
    parser = argparse.ArgumentParser(
        description="Source-audited Bangladesh road accident record analysis"
    )
    parser.add_argument(
        "stage",
        choices=[
            "acquire",
            "clean",
            "build",
            "analyze",
            "report",
            "notebooks",
            "check",
            "all",
        ],
    )
    parser.add_argument(
        "--archive", type=Path, help="Optional original Mendeley version-2 ZIP"
    )
    args = parser.parse_args()
    if args.archive and args.stage not in ["acquire", "all"]:
        parser.error("--archive applies only to acquire/all")
    from .acquisition import acquire
    from .analysis import analyze
    from .cleaning import prepare
    from .model import build_model
    from .notebooks import execute
    from .reporting import render
    from .visualization import charts

    def clean():
        _, quality = prepare()
        return quality

    def report():
        return {"charts": charts(), **render()}

    stages = {
        "acquire": lambda: acquire(args.archive),
        "clean": clean,
        "build": build_model,
        "analyze": analyze,
        "report": report,
        "notebooks": execute,
        "check": check,
    }
    for name, function in (
        stages if args.stage == "all" else {args.stage: stages[args.stage]}
    ).items():
        print(f"Running {name}...", flush=True)
        try:
            result = function()
        except (ValueError, FileNotFoundError, RuntimeError) as exc:
            print(f"{name} failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        print(json.dumps({"stage": name, "result": result}, indent=2), flush=True)


if __name__ == "__main__":
    main()
