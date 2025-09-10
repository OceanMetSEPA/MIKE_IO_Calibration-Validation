# load_dfs0_list_todataframe.py

from pathlib import Path
import re
import mikeio
import pandas as pd


class Dfs0File:
    """
    Wrapper for a single dfs0 file where each column (and datetime) is dot-accessible.

    Example:
        bundle.myfile.datetime
        bundle.myfile.sur_current_speed
        bundle.myfile.parameters
            -> {'sur: Current speed': 'sur_current_speed', ...}
    """

    def __init__(self, name: str, df: pd.DataFrame):
        self._name = name
        self._df = df
        self.parameters = {}  # mapping original -> sanitized attribute name

        # expose datetime index
        setattr(self, "datetime", df.index)

        # expose each column automatically with sanitized, lowercase attr names
        used = set()
        for col in df.columns:
            safe = self._sanitize(col)
            # ensure uniqueness if sanitization collides
            base = safe
            i = 2
            while safe in used or hasattr(self, safe):
                safe = f"{base}_{i}"
                i += 1
            setattr(self, safe, df[col])
            used.add(safe)
            self.parameters[col] = safe  # store mapping

    @staticmethod
    def _sanitize(name: str) -> str:
        """
        Make column name safe for dot access:
        - lowercase
        - any run of non-alphanumeric chars -> "_"
        - trim leading/trailing underscores
        """
        s = str(name).strip().lower()
        s = re.sub(r"[^0-9a-z]+", "_", s)
        return s.strip("_")

    @property
    def dataframe(self) -> pd.DataFrame:
        """Access the full DataFrame if needed."""
        return self._df

    def __repr__(self):
        return f"<Dfs0File {self._name} with {len(self._df.columns)} parameters>"


class Dfs0Bundle:
    """Bundle of dfs0 files, each accessible by filename stem (lowercase)."""

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
    Returns a Dfs0Bundle where each file exposes its parameters via dot-access.

    Parameters
    ----------
    file_list : list[str|Path]
        Paths to .dfs0 files (strings or Path objects).

    Returns
    -------
    Dfs0Bundle
        Access like: bundle.<filename_stem>.datetime, bundle.<filename_stem>.<parameter>
        Also check bundle.<filename_stem>.parameters for mapping.

    Example
    -------
    >>> bundle = load_dfs0s_to_dataframe([Path("MAOB1.dfs0")])
    >>> bundle.maob1.datetime
    >>> bundle.maob1.sur_current_speed
    >>> bundle.maob1.parameters
        {'sur: Current speed': 'sur_current_speed',
         'sur: Current direction (Horizontal)': 'sur_current_direction_horizontal'}
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
            key = p.stem.lower()  # filename stem as attribute name
            bundle.add(key, df)
            print(f"✅ Loaded: {p.name} → access with bundle.{key}.<parameter>")
        except Exception as e:
            print(f"❌ Error loading {p}: {e}")
    return bundle
