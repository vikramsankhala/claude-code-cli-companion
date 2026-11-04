"""Country packs: compliance is configuration, validated on load, never hard-coded in modules."""
from pathlib import Path

import yaml

REQUIRED = {"country", "currency", "fiscal_year_start", "tax", "privacy", "retention_years", "approvals"}


def load_packs(folder="packs") -> dict:
    packs = {}
    for p in sorted(Path(folder).glob("*.yaml")):
        pack = yaml.safe_load(p.read_text())
        missing = REQUIRED - pack.keys()
        if missing:
            raise ValueError(f"{p.name}: missing {sorted(missing)}")
        if not 0 <= pack["tax"]["rates"]["standard"] < 1:
            raise ValueError(f"{p.name}: standard tax rate must be a fraction")
        packs[pack["country"]] = pack
    return packs


def tax(pack, net: float, rate="standard") -> float:
    return round(net * pack["tax"]["rates"][rate], 2)
