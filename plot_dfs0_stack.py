import numpy as np
import pandas as pd
from bokeh.plotting import figure, show
from bokeh.layouts import column
from bokeh.models import HoverTool, DatetimeTickFormatter, ColumnDataSource, Range1d
from bokeh.embed import file_html
from bokeh.resources import INLINE
import webbrowser



def show_fullscreen(layout, title="Plot", filename="plot.html", theme=None):
    """Render a Bokeh layout to a standalone HTML that truly fills the viewport.

    This injects a small CSS rule so sizing_mode='stretch_both' uses the full window
    height and avoids unused whitespace at the bottom.
    """
    html = file_html(layout, INLINE, title, theme=theme)
    html = html.replace(
        "</head>",
        "<style>html, body, .bk-root {height: 100%; margin: 0;}</style></head>",
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    try:
        webbrowser.open(filename)
    except Exception:
        pass


def _time_and_matrix(ds):
    """
    Normalize time and data matrix from a mikeio.Dataset-like object.

    - Ensures time is a tz-naive pandas.DatetimeIndex
    - Ensures data has shape (len(time), n_items)
    - Replaces non-finite values with NaN so Bokeh draws gaps
    """
    # Normalize time to DatetimeIndex (tz-naive)
    t = pd.DatetimeIndex(ds.time)
    if getattr(t, "tz", None) is not None:
        # If tz-aware, convert to tz-naive for Bokeh
        try:
            t = t.tz_convert(None)
        except Exception:
            t = t.tz_localize(None)

    arr = ds.to_numpy()
    if arr.ndim != 2:
        raise ValueError(f"Unexpected data shape from mikeio dataset: {arr.shape}")

    # Ensure time runs along axis 0
    if arr.shape[0] != len(t) and arr.shape[1] == len(t):
        arr = arr.T

    if arr.shape[0] != len(t):
        raise ValueError(
            f"Time length ({len(t)}) does not match data rows ({arr.shape[0]}). "
            "The dataset may be irregular or items/time misaligned."
        )

    # Clean non-finite values so Bokeh draws gaps instead of spikes
    arr = np.where(np.isfinite(arr), arr, np.nan)

    return t, arr


def _find_item_index_exact(ds, item_name: str):
    for i, it in enumerate(ds.items):
        if it.name == item_name:
            return i
    available = [getattr(it, "name", str(it)) for it in ds.items]
    raise ValueError(f"Item '{item_name}' not found. Available: {available}")



def _unit_to_display(unit):
    """Return a human-friendly unit string from a MIKE IO EUMUnit-like object.

    Tries, in order:
      1) symbolic/unit fields (unit, symbol, abbr, abbreviation)
      2) descriptive fields (name, description) — converts snake_case to words
      3) if it's an int/code (or enum with .value/.code), attempts to resolve via mikeio.eum
      4) falls back to str(unit)
    """
    if unit in (None, "", "None"):
        return ""

    for attr in ("unit", "symbol", "abbr", "abbreviation"):
        val = getattr(unit, attr, None)
        if isinstance(val, str) and val.strip():
            return val

    name = getattr(unit, "name", None) or getattr(unit, "description", None)
    if isinstance(name, str) and name.strip():
        return name.replace("_", " ")

    code = None
    if isinstance(unit, (int, np.integer)):
        code = int(unit)
    elif isinstance(unit, str) and unit.isdigit():
        code = int(unit)
    else:
        for attr in ("value", "code"):
            v = getattr(unit, attr, None)
            if isinstance(v, (int, np.integer)):
                code = int(v)
                break

    if isinstance(code, int):
        try:
            import mikeio  # optional; only if available
            eum = getattr(mikeio, "eum", None)
            if eum is not None:
                UnitCls = getattr(eum, "EUMUnit", None) or getattr(eum, "Unit", None)
                if UnitCls is not None:
                    resolver = None
                    if hasattr(UnitCls, "from_int"):
                        resolver = getattr(UnitCls, "from_int")
                    elif hasattr(UnitCls, "from_value"):
                        resolver = getattr(UnitCls, "from_value")
                    if resolver is not None:
                        u = resolver(code)
                        for attr in ("unit", "symbol", "abbr", "abbreviation", "name", "description"):
                            val = getattr(u, attr, None)
                            if isinstance(val, str) and val.strip():
                                return val.replace("_", " ")
                        return str(u)
        except Exception:
            pass

    return str(unit)


<<<<<<< HEAD
def _is_radian_unit(unit):
    """Heuristically detect whether a MIKE IO unit represents *radians*.

    Uses the resolved display string from `_unit_to_display` and common attributes.
    """
    disp = str(_unit_to_display(unit)).strip().lower()
    if disp in {"rad", "radian", "radians"} or "radian" in disp:
        return True
    for attr in ("unit", "symbol", "abbr", "abbreviation", "name", "description"):
        v = getattr(unit, attr, None)
        if isinstance(v, str):
            s = v.strip().lower()
            if s in {"rad", "radian", "radians"} or "radian" in s:
                return True
    return False


def _convert_direction_if_radian(y, unit):
    """If `unit` is radians, convert `y` to degrees and return (y_deg, "°").
    Otherwise return (y, human_friendly_unit).
    """
    if _is_radian_unit(unit):
        return np.degrees(y), "°"
    return y, _unit_to_display(unit)


def _normalize_angle_unit_label(label: str) -> str:
    """Normalize any degree-like label to a degree symbol so grouping works.

    Examples: "deg", "degree", "degrees", and "°" -> "°"
    """
    s = (label or "").strip().lower()
    if "deg" in s or "degree" in s or (label and "°" in label):
        return "°"
    return label



def _base_item_name(name: str) -> str:
    """Return a normalized base item name (e.g., drop station prefixes like 'sur:' )."""
    if not isinstance(name, str):
        return str(name)
    core = name.split(":", 1)[1] if ":" in name else name
    return core.strip().lower()


def _canonical_group_key(ds, idx: int, item_name: str, unit_label: str):
    """Build a grouping key so *identical plotting items* share y-axis.

    Preference order: explicit MIKE item type if available, else normalized name.
    Unit is included to avoid grouping items that happen to share the same name
    but have different units.
    """
    it = ds.items[idx]
    for attr in ("type", "eum_item", "eumType", "quantity", "parameter"):
        v = getattr(it, attr, None)
        if v is not None:
            return (str(v).lower(), unit_label)
    return (_base_item_name(item_name), unit_label)


=======
>>>>>>> origin/master
def plot_dfs0_items_stacked(
    ds,
    item_names,                 # list of exact item names
    *,
    line_width=1.0,
    sizing_mode="stretch_both",   # fill the window
    height_per_plot=None,          # None => stretch to fill; else fixed height
    min_height_per_plot=180,       # floor for tiny viewports
    show_legend=True,
    datetime_format="%d/%m/%Y %H:%M:%S",
    palette=("#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"),
):
    """
    Plot multiple dfs0 items (exact names) as stacked subplots with a shared x-range.
    Zooming/panning in one subplot updates all.

    Parameters
    ----------
    ds : mikeio.Dataset (already loaded)
    item_names : list[str]   Exact item names to plot (one per subplot)
    line_width : float       Line thickness
    sizing_mode : str        Use "stretch_both" to fill the browser window
    height_per_plot : int|None  If None (default), plots stretch to fill; set a number to fix heights
    min_height_per_plot : int   Minimum height per subplot when stretching
    show_legend : bool       Show/hide legend on each subplot
    datetime_format : str    Bokeh datetime format string for x-axis and hover
    palette : tuple[str]     Colors to cycle (even if 1 series/plot, future-proof)
    """
    if not item_names:
        raise ValueError("item_names cannot be empty")
    if len(set(item_names)) != len(item_names):
        dupes = sorted({n for n in item_names if item_names.count(n) > 1})
        raise ValueError(f"Duplicate item_names not allowed: {dupes}")

    # Validate all items up front for a faster fail path
    missing = []
    for nm in item_names:
        try:
            _find_item_index_exact(ds, nm)
        except ValueError:
            missing.append(nm)
    if missing:
        available = [getattr(it, "name", str(it)) for it in ds.items]
        raise ValueError(f"Items not found: {missing}. Available: {available}")

    t, arr = _time_and_matrix(ds)

<<<<<<< HEAD
    # Precompute indices and series; detect radians and convert to degrees; compute unit labels
    indices = [_find_item_index_exact(ds, nm) for nm in item_names]
    ys = []
    unit_labels = []
    for i in indices:
        unit_raw = getattr(ds.items[i], "unit", "")
        y_raw = arr[:, i]
        y_conv, unit_str = _convert_direction_if_radian(y_raw, unit_raw)
        ys.append(y_conv)
        unit_labels.append(_normalize_angle_unit_label(unit_str))

    # Build grouping key per series (identical plotting items share y-axis)
    keys = []
    groups = {}
    for k, i in enumerate(indices):
        key = _canonical_group_key(ds, i, item_names[k], unit_labels[k])
        keys.append(key)
        groups.setdefault(key, []).append(k)

    # Compute a shared y-range for each group
    group_ranges = {}
    for key, members in groups.items():
        try:
            gmin = float(np.nanmin([np.nanmin(ys[m]) for m in members]))
            gmax = float(np.nanmax([np.nanmax(ys[m]) for m in members]))
        except ValueError:
            gmin, gmax = 0.0, 1.0
        if not np.isfinite(gmin) or not np.isfinite(gmax):
            gmin, gmax = 0.0, 1.0
        if gmin == gmax:
            gmin -= 0.5
            gmax += 0.5
        pad = (gmax - gmin) * 0.05
        group_ranges[key] = Range1d(start=gmin - pad, end=gmax + pad)
=======
    # Precompute indices and series; compute a global y-range
    indices = [_find_item_index_exact(ds, nm) for nm in item_names]
    ys = [arr[:, i] for i in indices]

    # Global y-range across all selected items (ignore NaNs)
    try:
        y_min = float(np.nanmin([np.nanmin(y) for y in ys]))
        y_max = float(np.nanmax([np.nanmax(y) for y in ys]))
    except ValueError:
        y_min, y_max = 0.0, 1.0  # handle all-NaN case safely
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = 0.0, 1.0
    if y_min == y_max:
        # avoid zero-height range
        y_min -= 0.5
        y_max += 0.5
    padding = (y_max - y_min) * 0.05
    shared_y = None
>>>>>>> origin/master

    figs = []
    shared_x = None

    n_plots = len(item_names)

    for k, name in enumerate(item_names):
        idx = indices[k]
        y = ys[k]

<<<<<<< HEAD
        # Unit already resolved (and converted to degrees if needed)
        unit_str = unit_labels[k]
        title = name if not unit_str else f"{name} ({unit_str})"
        # Decide height: stretch when None
=======
        # Unit handling (MIKE IO may expose a numeric code; resolve to display string)
        unit_raw = getattr(ds.items[idx], "unit", "")
        unit_str = _unit_to_display(unit_raw)
        title = name if not unit_str else f"{name} ({unit_str})"

            # Decide height: stretch when None
>>>>>>> origin/master
        eff_height = height_per_plot if height_per_plot is not None else min_height_per_plot
        p = figure(
            title=title,
            x_axis_type="datetime",
            height=eff_height,
            sizing_mode=sizing_mode,
            tools="pan,xwheel_zoom,box_zoom,reset,save",
            active_scroll="xwheel_zoom",
            toolbar_location="right",
            margin=(4, 8, 4, 8),
        )
        # Encourage max usage of space
        try:
            p.height_policy = "max"
            p.width_policy = "max"
        except Exception:
            pass
        p.min_border_left = 40
        p.min_border_right = 10
        p.min_border_top = 10
        p.min_border_bottom = 10

        if shared_x is None:
            shared_x = p.x_range
        else:
            p.x_range = shared_x  # link x-axes

<<<<<<< HEAD
        # Assign group-shared y-range for identical items
        grp_key = keys[k]
        p.y_range = group_ranges[grp_key]
=======
        # Link y-axes to a common global range
        if shared_y is None:
            shared_y = Range1d(start=y_min - padding, end=y_max + padding)
            p.y_range = shared_y
        else:
            p.y_range = shared_y
>>>>>>> origin/master

        # Explicit ColumnDataSource for robust hover
        source = ColumnDataSource(data={"x": t, "y": y})
        color = palette[k % len(palette)]
        r = p.line(
            "x",
            "y",
            source=source,
            line_width=line_width,
            color=color,
            legend_label=name if show_legend else None,
        )

        # Axes & formatter
        p.xaxis.axis_label = "Time"
        p.yaxis.axis_label = unit_str
        p.xaxis.formatter = DatetimeTickFormatter(
            hours=datetime_format,
            days=datetime_format,
            months=datetime_format,
            years=datetime_format,
        )

        if show_legend:
            p.legend.location = "top_left"
            p.legend.click_policy = "hide"
        # Hide x-axis on all but the bottom subplot to reclaim height
        if k < n_plots - 1:
            p.xaxis.visible = False
            p.xgrid.visible = False

        # Hover
        p.add_tools(
            HoverTool(
                renderers=[r],
                tooltips=[("Time", f"@x{{{datetime_format}}}"), (name, "@y")],
                formatters={"@x": "datetime"},
                mode="vline",
            )
        )

        figs.append(p)

    layout = column(*figs, sizing_mode="stretch_both")
    show(layout)
    return layout
