# load_dfs0_list.py
from pathlib import Path
import mikeio

def load_dfs0s(file_list):
    """
    Load multiple dfs0 files and return a dict of {filename: Dataset}.
    file_list can be a list of strings/Paths.
    """
    datasets = {}
    for f in file_list:
        p = Path(f)
        if not p.exists():
            print(f"⚠️ File not found: {p}")
            continue
        try:
            ds = mikeio.read(p)
            datasets[p.name] = ds
            print(f"✅ Loaded: {p.name} ({len(ds.items)} items, {len(ds.time)} timesteps)")
        except Exception as e:
            print(f"❌ Error loading {p}: {e}")
    return datasets