# plot_speed_compare.py
from pathlib import Path
import numpy as np
import pandas as pd
from bokeh.plotting import figure, show
from bokeh.io import output_file
from bokeh.models import HoverTool

def _ensure_time_items(ds):
    t = pd.DatetimeIndex(ds.time)
    arr = ds.to_numpy()
    if arr.ndim != 2:
        raise ValueError("Unexpected data shape from mikeio dataset")
    if arr.shape[0] != len(t) and arr.shape[1] == len(t):
        arr = arr.T
    return t, arr

def _find_item_index(ds, item_query: str):
    q = item_query.lower()
    names = [it.name for it in ds.items]
    for i, nm in enumerate(names):
        if nm.lower() == q:
            return i
    for i, nm in enumerate(names):
        if q in nm.lower():
            return i
    raise ValueError(f"Item '{item_query}' not found. Available: {names}")

def _unit_text(unit_obj):
    try:
        if hasattr(unit_obj, "abbreviation") and unit_obj.abbreviation:
            return unit_obj.abbreviation
        if hasattr(unit_obj, "name") and unit_obj.name:
            return unit_obj.name.replace("_", " ")
    except Exception:
        pass
    try:
        from mikeio import eum
        return eum.EUMUnit(unit_obj).name.replace("_", " ")
    except Exception:
        return str(unit_obj)

def plot_speed_compare(
    datasets: dict,
    mat_data: dict,
    dfs0_key: str,
    dfs0_item: str,          # dfs0 item name or substring
    mat_key: str,
    bin_index: int,          # 0=bed, 1=mid, 2=surface
    *,
    label_dfs0: str | None = None,
    label_mat: str | None = None,
    title: str | None = None,
    output_html: str | Path | None = None,
):
    """
    Plot MIKE dfs0 item vs HG .mat Speed for a chosen bin.
    The Bokeh plot will fill the whole browser window.
    """
    # --- MIKE dfs0 ---
    ds = datasets[dfs0_key]
    t_dfs0, arr = _ensure_time_items(ds)
    i_item = _find_item_index(ds, dfs0_item)
    y_dfs0 = arr[:, i_item].astype(float)
    unit = _unit_text(getattr(ds.items[i_item], "unit", None))
    label_dfs0 = label_dfs0 or f"MIKE: {ds.items[i_item].name}"

    # --- HG .mat ---
    md = mat_data[mat_key]
    ps = md["profileStruct"]
    b = ps.Bins[bin_index]
    t_mat = pd.DatetimeIndex(pd.to_datetime(b.Time))
    y_mat = np.asarray(b.Speed, dtype=float)
    label_mat = label_mat or f"Observed bin {bin_index}"

    # --- Bokeh figure ---
    fig_title = title or f"{dfs0_key} vs {mat_key} (bin {bin_index})"
    p = figure(
        title=fig_title,
        x_axis_type="datetime",
        sizing_mode="stretch_both",  # fill browser window
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll="wheel_zoom",
    )

    # thinner, solid lines
    r1 = p.line(t_dfs0, y_dfs0, line_width=1.5, color="#1f77b4", legend_label=label_dfs0)
    r2 = p.line(t_mat,  y_mat,  line_width=1.5, color="#d62728", legend_label=label_mat)

    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    p.xaxis.axis_label = "Time"
    p.yaxis.axis_label = unit or "Speed"

    # Hover tools
    p.add_tools(HoverTool(renderers=[r1], tooltips=[("Time", "@x{%F %T}"), (label_dfs0, "@y")],
                          formatters={"@x": "datetime"}))
    p.add_tools(HoverTool(renderers=[r2], tooltips=[("Time", "@x{%F %T}"), (label_mat, "@y")],
                          formatters={"@x": "datetime"}))

    if output_html:
        output_file(str(Path(output_html)))
    show(p)
    return p
