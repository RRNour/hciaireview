"""
00_setup_project.py
===================
Create the full repository directory structure and validate the
environment before any data collection begins.

Inputs  : config/config.yaml
Outputs : directory tree, data/raw/.gitkeep, outputs/.../.gitkeep
"""

import os, sys, yaml, subprocess, importlib
from pathlib import Path


REQUIRED_DIRS = [
    "data/raw",
    "data/normalized",
    "data/deduplicated",
    "data/filtered",
    "data/classified",
    "data/fulltext",
    "data/sections",
    "data/final",
    "outputs/tables",
    "outputs/figures",
    "outputs/prisma",
    "outputs/reports",
    "outputs/open_data",
    "outputs/sensitivity",
    "reports",
    "logs",
]

REQUIRED_PACKAGES = [
    "requests", "yaml", "numpy", "pandas",
    "scipy", "matplotlib", "seaborn",
    "networkx", "tqdm",
]


def load_config(path: str = "config/config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def create_dirs(base: Path, dirs: list[str]) -> None:
    for d in dirs:
        target = base / d
        target.mkdir(parents=True, exist_ok=True)
        gitkeep = target / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
    print(f"  Created {len(dirs)} directories")


def check_packages(packages: list[str]) -> list[str]:
    missing = []
    for pkg in packages:
        try:
            importlib.import_module(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    return missing


def check_python_version(min_major: int = 3, min_minor: int = 9) -> bool:
    v = sys.version_info
    return (v.major, v.minor) >= (min_major, min_minor)


def main():
    print("=== 00_setup_project.py ===")
    cfg = load_config()
    base = Path(cfg.get("project_root", "."))

    print(f"  Project root : {base.resolve()}")
    print(f"  Python       : {sys.version.split()[0]}")

    if not check_python_version():
        print("  WARNING: Python 3.9+ recommended")

    print("\n  Creating directory structure ...")
    create_dirs(base, REQUIRED_DIRS)

    print("\n  Checking required packages ...")
    missing = check_packages(REQUIRED_PACKAGES)
    if missing:
        print(f"  MISSING: {missing}")
        print(f"  Run: pip install -r requirements.txt")
    else:
        print(f"  All {len(REQUIRED_PACKAGES)} packages found")

    print("\n  Validating config keys ...")
    required_keys = [
        "project_root", "study_period", "venues",
        "thresholds", "evidence_tiers",
    ]
    for k in required_keys:
        status = "✓" if k in cfg else "✗ MISSING"
        print(f"    {status}  {k}")

    print("\n  Setup complete. Proceed with 01_collect_metadata.py")


if __name__ == "__main__":
    main()
