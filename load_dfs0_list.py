# E:\CodeLibraryOps\MIKE_IO_CalibrationValidation\load_dfs0_list.py
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

# Optional: allow running this file directly from Spyder
if __name__ == "__main__":
    # Example: hard-code or read from a text file
    dfs0_files = [
        r"E:\ASB-HPC-VM01\EastSkye\...\MAOB1.dfs0",
        r"E:\ASB-HPC-VM01\EastSkye\...\MAOB1_WL.dfs0",
    ]
    datasets = load_dfs0s(dfs0_files)
