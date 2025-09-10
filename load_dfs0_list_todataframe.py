# load_dfs0_list_todataframe.py

from pathlib import Path
import mikeio
import pandas as pd


class Dfs0File:
    """
    Wrapper for a single dfs0 file where each column (and datetime) is dot-accessible.
    Example: bundle.myfile.datetime, bundle.myfile.currentspeed
    """

    def __init__(self, name: str, df: pd.DataFrame):
        self._name = name
        self._df = df

        # expose datetime index
        setattr(self, "datetime", df.index)

        # expose each column automatically
        for col in df.columns:
            safe_name = self._sanitize(col)
            setattr(self, safe_name, df[col])

    @staticmethod
    def _sanitize(name: str) -> str:
        """Make column name safe for dot access: lowercase + underscores only."""
        return (
            str(name)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace(".", "_")
        )

    @property
    def dataframe(self) -> pd.DataFrame:
        """Access the full DataFrame if needed."""
        return self._df

    def __repr__(self):
        return f"<Dfs0File {self._name} with {len(self._df.columns)} parameters>"


class Dfs0Bundle:
    """Bundle of dfs0 files, each accessible by filename (stem)."""

    def __init__(self):
        self._files = {}

    def add(self, name: str, df: pd.DataFrame):
        dfs0file = Dfs0File(name, df)
        setattr(self, name, dfs0file)
        self._files[name] = dfs0file

    def __iter__(self):
        return iter(self._files.values())

    def __len__(self):
        return len(self._files)

    def keys(self):
        return self._files.keys()

    def items(self):
        return self._files.items()

    def __repr__(self):
        return f"<Dfs0Bundle with {len(self)} files: {list(self._files.keys())}>"


def load_dfs0s_to_dataframe(file_list):
    """
    Load multiple dfs0 files into pandas DataFrames.

    Parameters
    ----------
    file_list : list of str or Path
        Paths to dfs0 files.

    Returns
    -------
    Dfs0Bundle
        Each dfs0 file is accessible as bundle.<filename_stem>.<parameter>

    Example
    -------
    >>> from load_dfs0_list_todataframe import load_dfs0s_to_dataframe
    >>> files = ["flow_stationB.dfs0", "stage_stationA.dfs0"]
    >>> bundle = load_dfs0s_to_dataframe(files)
    >>> bundle.flow_stationb.datetime
    >>> bundle.flow_stationb.current_speed
    """
    bundle = Dfs0Bundle()
    for f in file_list:
        p = Path(f)
        if not p.exists():
            print(f"⚠️ File not found: {p}")
            continue
        try:
            ds = mikeio.read(p)
            df = ds.to_dataframe()
            key = p.stem.lower()  # filename (stem) becomes attribute name
            bundle.add(key, df)
            print(f"✅ Loaded: {p.name} → access with bundle.{key}.<parameter>")
        except Exception as e:
            print(f"❌ Error loading {p}: {e}")
    return bundle
