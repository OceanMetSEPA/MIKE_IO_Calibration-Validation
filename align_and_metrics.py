# align_and_metrics.py
from pathlib import Path
import numpy as np
import pandas as pd

# ---------- helpers to get series ----------
def _ensure_time_items(ds):
    """Return (DatetimeIndex, 2D numpy array) with shape (time, items)."""
    t = pd.DatetimeIndex(ds.time)
    arr = ds.to_numpy()
    if arr.ndim != 2:
        raise ValueError("Unexpected data shape from mikeio dataset")
    if arr.shape[0] != len(t) and arr.shape[1] == len(t):
        arr = arr.T
    return t, arr

def _find_item_index(ds, item_query: str):
    """Find item by exact name first, else substring (case-insensitive)."""
    q = item_query.lower()
    names = [it.name for it in ds.items]
    for i, nm in enumerate(names):
        if nm.lower() == q:
            return i
    for i, nm in enumerate(names):
        if q in nm.lower():
            return i
    raise ValueError(f"Item '{item_query}' not found. Available: {names}")

def get_dfs0_speed_series(datasets: dict, dfs0_key: str, item_query: str) -> pd.Series:
    """Return model speed (pd.Series) indexed by datetime."""
    if dfs0_key not in datasets:
        raise KeyError(f"'{dfs0_key}' not in datasets: {list(datasets.keys())}")
    ds = datasets[dfs0_key]
    t, arr = _ensure_time_items(ds)
    i = _find_item_index(ds, item_query)
    y = arr[:, i].astype(float)
    return pd.Series(y, index=t, name="model")

def get_hg_speed_series(mat_data: dict, mat_key: str, bin_index: int) -> pd.Series:
    """Return observed speed (pd.Series) for given bin, indexed by datetime."""
    if mat_key not in mat_data:
        raise KeyError(f"'{mat_key}' not in mat_data: {list(mat_data.keys())}")
    md = mat_data[mat_key]
    if "profileStruct" not in md:
        raise KeyError(f"'profileStruct' not found in '{mat_key}'. Keys: {list(md.keys())}")
    ps = md["profileStruct"]
    try:
        b = ps.Bins[bin_index]
    except Exception as e:
        raise IndexError(f"Bin {bin_index} invalid; available bins: {len(ps.Bins)}") from e
    # Expect Time already converted to Python datetimes by your load_mat_list.py
    t = pd.DatetimeIndex(pd.to_datetime(b.Time))
    y = np.asarray(b.Speed, dtype=float)
    return pd.Series(y, index=t, name="obs")

# ---------- alignment strategies ----------
def align_series(
    s_model: pd.Series,
    s_obs: pd.Series,
    method: str = "asof",
    tolerance: str = "10min",
    resample: str | None = None,
    how_resample: str = "mean",
) -> pd.DataFrame:
    """
    Align two time series into a single DataFrame with columns ['model','obs'].

    method:
      - 'inner'   : exact timestamp intersection
      - 'asof'    : nearest match (left join on model time) within 'tolerance'
      - 'outer'   : union of timestamps
    resample:
      - None      : keep native time stamps
      - e.g. 'H'  : resample both to hourly ('mean' by default)
    """
    sm = s_model.sort_index()
    so = s_obs.sort_index()

    if resample:
        agg = {"mean": "mean", "median": "median", "sum": "sum"}[how_resample]
        sm = getattr(sm.resample(resample), agg)()
        so = getattr(so.resample(resample), agg)()

    if method == "inner":
        df = pd.concat([sm, so], axis=1, join="inner")
    elif method == "outer":
        df = pd.concat([sm, so], axis=1, join="outer")
    elif method == "asof":
        # nearest obs to each model time within tolerance
        df = pd.DataFrame({"model": sm})
        df["obs"] = so.reindex(sm.index, method="nearest", tolerance=pd.Timedelta(tolerance))
    else:
        raise ValueError("method must be one of: 'inner', 'asof', 'outer'")

    # drop rows with any NaN after alignment
    return df.dropna()

# ---------- metrics ----------
def calc_stats(obs: np.ndarray, mod: np.ndarray) -> dict:
    """Common calibration/validation stats."""
    obs = np.asarray(obs, dtype=float)
    mod = np.asarray(mod, dtype=float)
    mask = np.isfinite(obs) & np.isfinite(mod)
    obs = obs[mask]; mod = mod[mask]
    n = len(obs)
    if n == 0:
        return {"N": 0}
    bias = np.mean(mod - obs)
    mae = np.mean(np.abs(mod - obs))
    rmse = np.sqrt(np.mean((mod - obs) ** 2))
    corr = np.corrcoef(obs, mod)[0, 1] if n > 1 else np.nan
    # Nash–Sutcliffe Efficiency
    denom = np.sum((obs - np.mean(obs)) ** 2)
    nse = 1 - np.sum((obs - mod) ** 2) / denom if denom > 0 else np.nan
    return {
        "N": n,
        "Bias": bias,
        "MAE": mae,
        "RMSE": rmse,
        "Correlation": corr,
        "R2": (corr ** 2) if np.isfinite(corr) else np.nan,
        "NSE": nse,
    }

# ---------- one-call convenience ----------
def compare_speed_stats(
    datasets: dict,
    mat_data: dict,
    dfs0_key: str,
    dfs0_item: str,
    mat_key: str,
    bin_index: int,
    *,
    align_method: str = "asof",
    tolerance: str = "10min",
    resample: str | None = None,  # e.g. 'H' to align by hour like your MATLAB script
    how_resample: str = "mean",
) -> tuple[pd.DataFrame, dict]:
    """
    Extract, align, and compute metrics.
    Returns (aligned_df, stats_dict).
    """
    s_model = get_dfs0_speed_series(datasets, dfs0_key, dfs0_item)
    s_obs   = get_hg_speed_series(mat_data, mat_key, bin_index)
    aligned = align_series(s_model, s_obs, method=align_method, tolerance=tolerance,
                           resample=resample, how_resample=how_resample)
    stats = calc_stats(aligned["obs"].values, aligned["model"].values)
    return aligned, stats
