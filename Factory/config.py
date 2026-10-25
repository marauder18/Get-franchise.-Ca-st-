"""Configuration for the offline factory. Deliberately contains no provider support."""
from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Load simple KEY=VALUE overrides without exposing or requiring credentials."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()
REPORTS_DIR = (ROOT / os.getenv("FACTORY_REPORTS_DIR", "../output/franchises")).resolve()
WEBSITE_DATA = (ROOT / os.getenv("FACTORY_WEBSITE_DATA", "../output/franchises/GETFRANCHISE_BRAND_DATA_2026-07-18.json")).resolve()
WORKSPACE = ROOT / "workspace"
RAW_DIR = WORKSPACE / "raw"
CLEAN_DIR = WORKSPACE / "clean"
PUBLISHED_DIR = WORKSPACE / "published"
LOG_DIR = WORKSPACE / "logs"
PROMPTS_DIR = ROOT / "prompts"
SCHEMA_DIR = ROOT / "schemas"


def ensure_workspace() -> None:
    for directory in (RAW_DIR, CLEAN_DIR, PUBLISHED_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)
