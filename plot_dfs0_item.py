# plot_dfs0_item.py
import pandas as pd
from bokeh.plotting import figure, show
from bokeh.models import HoverTool

def _ensure_time_items(ds):
    """Return (DatetimeIndex, values time x items)."""
    t = pd.DatetimeIndex(ds.time)
    arr = ds.to_numpy()
    if arr.ndim != 2:
        raise ValueError("Unexpected data shape from mikeio dataset")
    if arr.shape[0] != len(t) and arr.shape[1] == len(t):
        arr = arr.T
    return t, arr

def _find_item_index(ds, item_query: str):
    """Find item index by exact name or substring (case-insensitive)."""
    q = item_query.lower()
    names = [it.name for it in ds.items]
    for i, nm in enumerate(names):
        if nm.lower() == q:
            return i
    for i, nm in enumerate(names):
        if q in nm.lower():
            return i
    raise ValueError(f"Item '{item_query}' not found. Available: {names}")

def plot_dfs0_item(ds, item_query, title=None, sizing_mode="stretch_both"):
    """
    Plot one dfs0 item (interactive Bokeh).
    
    Parameters
    ----------
    ds : mikeio.Dataset
        Already-loaded dfs0 dataset.
    item_query : str
        Item name (exact or substring match).
    title : str
        Optional plot title.
    sizing_mode : str
        Bokeh sizing mode ('stretch_both' fills the window).
    """
    t, arr = _ensure_time_items(ds)
    i = _find_item_index(ds, item_query)
    y = arr[:, i].astype(float)

    name = ds.items[i].name
    unit = getattr(ds.items[i], "unit", "")
    unit_str = str(unit)

    p = figure(
        title=title or f"{name} ({unit_str})",
        x_axis_type="datetime",
        sizing_mode=sizing_mode,
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll="wheel_zoom",
    )
    r = p.line(t, y, line_width=1.5, color="navy", legend_label=name)
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    p.xaxis.axis_label = "Time"
    p.yaxis.axis_label = unit_str

    p.add_tools(HoverTool(renderers=[r],
                          tooltips=[("Time", "@x{%F %T}"), (name, "@y")],
                          formatters={"@x": "datetime"}))
    show(p)
    return p
