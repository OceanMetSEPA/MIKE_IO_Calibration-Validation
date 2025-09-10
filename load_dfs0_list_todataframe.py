# load_dfs0_list_todataframe.py

from pathlib import Path
import re
import mikeio
import pandas as pd


class Dfs0File:
    """
    Wrapper for a single dfs0 file where each column (and datetime) is dot-accessible.

    Access patterns:
        - Dot access (sanitized):  bundle.maob1.sur_current_speed
        - Index by original name:  bundle.maob1["sur: Current speed"]
        - Datetime index:          bundle.maob1.datetime
        - Mapping:                 bundle.maob1.parameters  # {original: sanitized}
        - Full DataFrame:          bundle.maob1.dataframe
        - Table of params:         bundle.maob1.show_parameters()
    """

    def __init__(self, name: str, df: pd.DataFrame):
        self._name = name
        self._df = df
        self.parameters: dict[str, str] = {}  # original -> sanitized attribute name

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
            self.parameters[str(col)] = safe  # store mapping from original -> sanitized

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

    # Dict-like access by original name (or sanitized name)
    def __getitem__(self, key: str):
        """
        Get a pandas Series by:
          - original dfs0 item name (exact match), e.g. "sur: Current direction (Horizontal)"
          - OR the sanitized name used for dot access, e.g. "sur_current_direction_horizontal"
        """
        if key in self.parameters:
            return getattr(self, self.parameters[key])
        if hasattr(self, key):
            return getattr(self, key)
        available = list(self.parameters.keys())
        raise KeyError(
            f"Parameter '{key}' not found. "
            f"Try one of the original names: {available[:10]}{' ...' if len(available)>10 else ''}"
        )

    def __contains__(self, key: str) -> bool:
        return key in self.parameters or hasattr(self, key)

    def get(self, key: str, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def show_parameters(self) -> pd.DataFrame:
        """
        Print a neat table mapping original dfs0 names to dot-access names.
        Returns the DataFrame for further use.
        """
        table = pd.DataFrame(
            [(orig, dot) for orig, dot in self.parameters.items()],
            columns=["Original name", "Dot-access name"],
        ).sort_values("Original name", kind="stable", ignore_index=True)
        # Pretty print without the pandas index
        print(table.to_string(index=False))
        return table

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
    Returns a Dfs0Bundle where each file exposes its parameters via dot-access and original-name indexing.

    Parameters
    ----------
    file_list : list[str|Path]
        Paths to .dfs0 files (strings or Path objects).

    Returns
    -------
    Dfs0Bundle
        Access like:
          - bundle.<filename_stem>.datetime
          - bundle.<filename_stem>.<sanitized_parameter>
          - bundle.<filename_stem>["<original parameter name>"]
        See mapping via bundle.<filename_stem>.parameters (original -> sanitized).
        Print a readable table via bundle.<filename_stem>.show_parameters()
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
            print(f"✅ Loaded: {p.name} → access with bundle.{key}.<parameter> or bundle.{key}[\"<original>\"]")
        except Exception as e:
            print(f"❌ Error loading {p}: {e}")
    return bundle
