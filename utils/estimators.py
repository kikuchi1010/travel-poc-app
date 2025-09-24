from __future__ import annotations
import pandas as pd
from typing import Optional, Tuple

def estimate_airfare_jpy(airfare_df: pd.DataFrame, origin: str, country_iso2: str, month: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    df = airfare_df[(airfare_df['origin']==origin) & (airfare_df['country_iso2']==country_iso2)]
    if month:
        df_m = df[df['month']==month]
        if not df_m.empty:
            df = df_m
    if df.empty:
        return None, None
    row = df.iloc[0]
    return int(row['median_price']), int(row['min_price'])

def estimate_daily_cost(cost_df: pd.DataFrame, country_iso2: str, level: str='med') -> Optional[int]:
    df = cost_df[cost_df['country_iso2']==country_iso2]
    if df.empty:
        return None
    row = df.iloc[0]
    return int(row['daily_cost_low' if level=='low' else 'daily_cost_high' if level=='high' else 'daily_cost_med'])

def total_budget_range(airfare_median: Optional[int], daily_cost: Optional[int], days: int) -> Tuple[Optional[int], Optional[int]]:
    if airfare_median is None or daily_cost is None:
        return None, None
    low = int(airfare_median*0.85 + daily_cost*days*0.85)
    high = int(airfare_median*1.15 + daily_cost*days*1.15)
    return low, high
