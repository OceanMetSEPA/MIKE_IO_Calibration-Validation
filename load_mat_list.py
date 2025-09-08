# load_mat_list.py
from pathlib import Path
import scipy.io as sio
import numpy as np
import datetime

def matlab_datenum_to_datetime(md):
    """
    Convert Matlab datenum array -> list of Python datetimes.
    """
    md = np.asarray(md)
    day = np.floor(md).astype(int)
    frac = md - day
    return [
        datetime.datetime.fromordinal(int(d)) + datetime.timedelta(days=float(f)) - datetime.timedelta(days=366)
        for d, f in zip(day, frac)
    ]

def convert_time_fields(obj):
    """
    Recursively look for 'Time' fields in MATLAB structs and convert them.
    """
    # scipy.io.loadmat returns nested mat_struct objects
    if hasattr(obj, "__dict__"):  # likely a mat_struct
        for field, val in obj.__dict__.items():
            if field.lower() == "time":
                try:
                    setattr(obj, field, matlab_datenum_to_datetime(val))
                except Exception:
                    pass
            else:
                convert_time_fields(val)
    elif isinstance(obj, (list, tuple, np.ndarray)):
        for item in obj:
            convert_time_fields(item)

def load_mat_files(file_list):
    """
    Load one or more .mat files into a dictionary.
    - MATLAB 'datenum' fields called 'Time' are converted to Python datetimes.
    - Returns {filename: dict_of_variables}.
    """
    results = {}
    for f in file_list:
        p = Path(f)
        if not p.exists():
            print(f"⚠️ File not found: {p}")
            continue
        try:
            mat = sio.loadmat(p, squeeze_me=True, struct_as_record=False)
            mat = {k: v for k, v in mat.items() if not k.startswith("__")}

            # Convert Time fields inside any structs
            for v in mat.values():
                convert_time_fields(v)

            results[p.name] = mat
            print(f"✅ Loaded {p.name} with variables: {list(mat.keys())}")
        except Exception as e:
            print(f"❌ Error loading {p}: {e}")
    return results
