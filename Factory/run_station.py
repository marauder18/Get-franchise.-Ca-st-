"""Run exactly one offline station in this process."""
from __future__ import annotations

import argparse
from pathlib import Path

from stations.station1_extract import extract
from stations.station2_clean import clean
from stations.station3_publish import publish


def run(station: str, input_value: str) -> Path:
    if station == "extract":
        return extract(input_value)
    if station == "clean":
        return clean(Path(input_value))
    if station == "publish":
        return publish(Path(input_value))
    raise ValueError("station must be extract, clean, or publish")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one offline GetFranchise station.")
    parser.add_argument("station", choices=("extract", "clean", "publish"))
    parser.add_argument("input")
    args = parser.parse_args()
    print(run(args.station, args.input))


if __name__ == "__main__":
    main()
