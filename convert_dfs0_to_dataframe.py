"""
convert_dfs0_to_dataframe.py

Convert a dict of loaded MIKE dfs0 Datasets (from mikeio.read)
into pandas DataFrames.

Usage
-----
from convert_dfs0_to_dataframe import dfs0_to_dataframes

# datasets is a dict like {"file1": mikeio.read("file1.dfs0")}
frames = dfs0_to_dataframes(datasets)

for name, df in frames.items():
    print("\n—", name, "—")
    print(df.head())
"""
from __future__ import annotations
from typing import Dict, Mapping
import pandas as pd

# ---- internal ----

def _dataset_to_dataframe(ds) -> pd.DataFrame:
    """Convert a single mikeio.Dataset to a pandas DataFrame (time index, item columns)."""
    t = pd.DatetimeIndex(ds.time)
    arr = ds.to_numpy()

    # Normalize to shape (n_time, n_items)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    if arr.shape[0] != len(t) and arr.shape[1] == len(t):
        arr = arr.T
    if arr.shape[0] != len(t):
        raise ValueError(f"Unexpected dfs0 data shape: {arr.shape} vs {len(t)} timestamps")

    columns = [it.name for it in ds.items]
    return pd.DataFrame(arr, index=t, columns=columns)

# ---- public ----

def dfs0_to_dataframes(datasets: Mapping[str, object]) -> Dict[str, pd.DataFrame]:
    """
    Convert a dict of {name: mikeio.Dataset} into {name: DataFrame}.
    """
    frames: Dict[str, pd.DataFrame] = {}
    for name, ds in datasets.items():
        try:
            frames[name] = _dataset_to_dataframe(ds)
        except Exception as e:
            print(f"❌ Error converting {name}: {e}")
    return frames

if __name__ == "__main__":
    print("This module provides dfs0_to_dataframes(datasets). Import and call it with your dict of mikeio Datasets.")
