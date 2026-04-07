"""Reusable plotting helpers for spatial altruism analysis scripts."""

import matplotlib.pyplot as plt
import seaborn as sns


def plot_heatmap_embedded(
    df,
    x,
    y,
    fixed,
    value="coexist_prob",
    aggfunc="mean",
    cmap="viridis",
    canvas=None,
    fig=None,
    title=None,
    cbar_label=None,
    vmin=0,
    vmax=1,
):
    dff = df.copy()
    for key, selected_value in fixed.items():
        dff = dff[dff[key] == selected_value]

    if fig is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    else:
        fig.clf()
        ax = fig.add_subplot(111)

    if dff.empty:
        ax.text(0.5, 0.5, "No data for selected filters.", ha="center", va="center")
        ax.set_axis_off()
        fig.tight_layout()
        if canvas is not None:
            canvas.draw()
        return fig

    dff = dff.sort_values([y, x])
    pivot = dff.pivot_table(index=y, columns=x, values=value, aggfunc=aggfunc)
    heatmap_kwargs = {
        "data": pivot,
        "annot": False,
        "fmt": ".2f",
        "cmap": cmap,
        "cbar_kws": {"label": cbar_label or value.replace("_", " ")},
        "ax": ax,
    }
    if vmin is not None:
        heatmap_kwargs["vmin"] = vmin
    if vmax is not None:
        heatmap_kwargs["vmax"] = vmax

    sns.heatmap(**heatmap_kwargs)
    ax.set_title(title or f"{(cbar_label or value).replace('_', ' ').title()}\nFixed: {fixed}")
    ax.set_xlabel(x.replace("_", " "))
    ax.set_ylabel(y.replace("_", " "))
    fig.tight_layout()
    if canvas is not None:
        canvas.draw()
    return fig

