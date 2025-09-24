from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent

def load_regions_countries():
    p = BASE / "data" / "regions_countries.json"
    return json.loads(p.read_text(encoding="utf-8"))

def load_spots_df() -> pd.DataFrame:
    p = BASE / "data" / "spots.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    return pd.DataFrame(data)

def load_costs_df() -> pd.DataFrame:
    p = BASE / "data" / "cost_baselines.csv"
    return pd.read_csv(p)

def load_airfare_df() -> pd.DataFrame:
    p = BASE / "data" / "airfare_cache_mock.csv"
    return pd.read_csv(p)
