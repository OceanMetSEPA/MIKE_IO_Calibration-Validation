# plot_dfs0_item_select.py
from pathlib import Path
import numpy as np
import pandas as pd

from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, HoverTool, Div, Select, CustomJS
from bokeh.layouts import column

def _ensure_time_items(ds):
    """Return (DatetimeIndex, values with shape (time, items))."""
    t = pd.DatetimeIndex(ds.time)
    arr = ds.to_numpy()
    if arr.ndim != 2:
        raise ValueError("Unexpected data shape from mikeio dataset")
    if arr.shape[0] != len(t) and arr.shape[1] == len(t):
        arr = arr.T
    return t, arr

def _unit_text(u):
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
        return str(u)

def plot_dfs0_item_with_selector(ds, dfs0_files, title_prefix=None):
    """
    Interactive Bokeh plot: choose any item from a dfs0 dataset via dropdown.

    Parameters
    ----------
    ds : mikeio.Dataset
        Already-loaded dfs0 dataset.
    dfs0_files : list[pathlib.Path] or list[str]
        Original file paths; used to display the full file location.
    title_prefix : str | None
        Optional text to prefix the plot title.

    Returns
    -------
    layout : bokeh.layouts.Column
    """
    # Match dataset to original full path if possible
    file_path = None
    try:
        src_name = Path(getattr(ds, "source", ""))  # ds.source may be Path-like or str
        src_base = src_name.name
    except Exception:
        src_base = None

    for p in map(Path, dfs0_files):
        if src_base and p.name == src_base:
            file_path = p
            break
    if file_path is None:
        # fallback: try ds.source or just unknown
        file_path = Path(str(getattr(ds, "source", "unknown")))

    # Extract time and all items
    t, arr = _ensure_time_items(ds)
    t_ms = t.astype("datetime64[ms]").astype(np.int64).tolist()  # Bokeh expects ms since epoch

    names = [it.name for it in ds.items]
    units = {it.name: _unit_text(getattr(it, "unit", None)) for it in ds.items}
    all_y = {names[i]: arr[:, i].astype(float).tolist() for i in range(len(names))}

    # Initial selection = first item
    item0 = names[0]
    unit0 = units[item0]

    # Data source for the line
    source = ColumnDataSource(data=dict(t=t_ms, y=all_y[item0]))

    # Figure (full browser window)
    title_text = f"{title_prefix + ' - ' if title_prefix else ''}{item0} ({unit0})"
    p = figure(
        title=title_text,
        x_axis_type="datetime",
        sizing_mode="stretch_both",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll="wheel_zoom",
    )
    r = p.line("t", "y", source=source, line_width=1.5, color="#1f77b4", legend_label=item0)
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    p.xaxis.axis_label = "Time"
    p.yaxis.axis_label = unit0

    p.add_tools(HoverTool(
        renderers=[r],
        tooltips=[("Time", "@t{%F %T}"), ("Value", "@y")],
        formatters={"@t": "datetime"}
    ))

    # Dropdown to pick item
    select = Select(title="Select dfs0 item:", value=item0, options=names)

    # JS callback to swap series, legend, axes, and title
    cb = CustomJS(
        args=dict(
            source=source,
            all_y=all_y,
            units=units,
            p=p,
            r=r,
            t=t_ms,
            title_prefix=title_prefix or "",
        ),
        code="""
        const name = cb_obj.value;
        const y = all_y[name];
        if (!y) { return; }

        // Update data
        source.data = {t: t, y: y};
        source.change.emit();

        // Update legend, axis label, title
        r.glyph.line_color = "#1f77b4";  // keep style stable
        r.legend_label = name;
        const unit = units[name] || "";
        p.yaxis[0].axis_label = unit;

        const prefix = title_prefix ? (title_prefix + " - ") : "";
        p.title.text = `${prefix}${name} (${unit})`;
        """
    )
    select.js_on_change("value", cb)

    # Show file location under the plot
    div = Div(text=f"<b>File location:</b> {file_path}", styles={"font-size": "90%"})

    layout = column(select, p, div, sizing_mode="stretch_both")
    show(layout)
    return layout
