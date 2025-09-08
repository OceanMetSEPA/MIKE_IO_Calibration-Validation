# E:\CodeLibraryOps\MIKE_IO_CalibrationValidation\print_dfs0_list.py
from pathlib import Path
import pandas as pd
import numpy as np

def unit_text(u):
    """Return a friendly unit string from a mikeio unit value."""
    try:
        if hasattr(u, "abbreviation") and u.abbreviation:
            return u.abbreviation
        if hasattr(u, "name") and u.name:
            return u.name.replace("_", " ")
    except Exception:
        pass
    try:
        from mikeio import eum
        return eum.EUMUnit(u).name.replace("_", " ")
    except Exception:
        pass
    return str(u)

def print_dfs0s(datasets, dfs0_files=None):
    """
    Print details of already loaded dfs0 datasets
    and return a summary DataFrame.

    Parameters
    ----------
    datasets : dict
        {filename: mikeio.Dataset}
    dfs0_files : list of str/Path, optional
        Original file paths (to fill in Folder column)

    Returns
    -------
    summary_df : pandas.DataFrame
    """
    name_to_folder = {}
    if dfs0_files:
        for fp in dfs0_files:
            p = Path(fp)
            name_to_folder[p.name] = str(p.parent)

    summary_rows = []
    for fname, ds in datasets.items():
        time = pd.DatetimeIndex(ds.time)
        nrec = len(time)
        start = time[0] if nrec > 0 else None
        end   = time[-1] if nrec > 0 else None

        mean_dt = min_dt = max_dt = None
        if nrec > 1:
            dt = np.diff(time.values).astype("timedelta64[s]").astype(float)
            mean_dt = float(np.mean(dt))
            min_dt  = float(np.min(dt))
            max_dt  = float(np.max(dt))

        print("="*60)
        print(f"📄 File:   {fname}")
        print(f"📂 Folder: {name_to_folder.get(fname, '')}")
        print(f"🕒 Start:  {start}")
        print(f"🕒 End:    {end}")
        if start and end:
            print(f"⏳ Duration: {end - start}")
        print(f"📊 Records: {nrec}")
        print(f"Δt (s): mean={mean_dt}, min={min_dt}, max={max_dt}")
        print(f"Items ({len(ds.items)}):")
        for it in ds.items:
            print(f"  - {it.name} [{unit_text(getattr(it, 'unit', None))}]")

        items_preview = ", ".join(
            [f"{it.name} [{unit_text(getattr(it, 'unit', None))}]" for it in ds.items[:3]]
        ) + ("…" if len(ds.items) > 3 else "")

        summary_rows.append({
            "File": fname,
            "Folder": name_to_folder.get(fname, ""),
            "Start": start,
            "End": end,
            "Records": nrec,
            "MeanDt_s": mean_dt,
            "MinDt_s": min_dt,
            "MaxDt_s": max_dt,
            "Items": len(ds.items),
            "ItemsPreview": items_preview
        })

    summary_df = pd.DataFrame(summary_rows)
    print("\n=== Summary DataFrame ===")
    print(summary_df)

    return summary_df
