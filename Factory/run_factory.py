"""Run independent station subprocesses; files are the only handoff."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from common import log, slugify
from config import LOG_DIR, ROOT, ensure_workspace


def run_command(station: str, input_value: str) -> Path:
    started = time.monotonic()
    process = subprocess.run(
        [sys.executable, "run_station.py", station, input_value],
        cwd=ROOT,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
    )
    duration = round(time.monotonic() - started, 3)
    output = process.stdout.strip().splitlines()
    if process.returncode != 0 or not output:
        detail = process.stderr.strip() or process.stdout.strip() or "no station output"
        raise RuntimeError(f"{station} failed after {duration}s: {detail}")
    path = Path(output[-1]).resolve()
    if not path.exists():
        raise RuntimeError(f"{station} did not produce its claimed output: {path}")
    print(f"{station}: done | {path} | {duration}s")
    return path


def run_factory(franchise: str) -> Path:
    ensure_workspace()
    run_log = LOG_DIR / f"{slugify(franchise)}.run.log"
    try:
        raw = run_command("extract", franchise)
        log(run_log, {"station": "extract", "status": "done", "file": str(raw)})
        clean = run_command("clean", str(raw))
        log(run_log, {"station": "clean", "status": "done", "file": str(clean)})
        published = run_command("publish", str(clean))
        log(run_log, {"station": "publish", "status": "done", "file": str(published)})
        return published
    except Exception as error:
        log(run_log, {"station": "factory", "status": "failed", "error": str(error)})
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the three offline factory stations as isolated subprocesses.")
    parser.add_argument("franchise")
    args = parser.parse_args()
    print(run_factory(args.franchise))


if __name__ == "__main__":
    main()
