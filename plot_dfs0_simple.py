def plot_dfs0_item_exact(ds, item_name):
    import pandas as pd
    from bokeh.plotting import figure, show
    from bokeh.models import HoverTool, DatetimeTickFormatter

    # Find item index
    idx = None
    for i, it in enumerate(ds.items):
        if it.name == item_name:
            idx = i
            break
    if idx is None:
        raise ValueError(f"Item '{item_name}' not found. Available: {[it.name for it in ds.items]}")

    # Extract time series
    t = pd.DatetimeIndex(ds.time)
    arr = ds.to_numpy()
    if arr.shape[0] != len(t):   # handle (items, time) orientation
        arr = arr.T
    y = arr[:, idx]

    unit = getattr(ds.items[idx], "unit", "")
    unit_str = str(unit)

    # Bokeh figure
    p = figure(
        title=f"{item_name} ({unit_str})",
        x_axis_type="datetime",
        sizing_mode="stretch_both",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll="wheel_zoom",
    )
    r = p.line(t, y, line_width=1.0, color="navy", legend_label=item_name)

    # Format axes
    p.legend.location = "top_left"
    p.xaxis.axis_label = "Time"
    p.yaxis.axis_label = unit_str

    # Corrected datetime formatter for Bokeh 3.x
    p.xaxis.formatter = DatetimeTickFormatter(
        hours="%d/%m/%Y %H:%M:%S",
        days="%d/%m/%Y %H:%M:%S",
        months="%d/%m/%Y %H:%M:%S",
        years="%d/%m/%Y %H:%M:%S",
    )

    # Hover tool with same format
    p.add_tools(HoverTool(
        renderers=[r],
        tooltips=[("Time", "@x{%d/%m/%Y %H:%M:%S}"), (item_name, "@y")],
        formatters={"@x": "datetime"}
    ))

    show(p)
    return p
