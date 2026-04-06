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
):
    dff = df.copy()
    for key, selected_value in fixed.items():
        dff = dff[dff[key] == selected_value]

    dff = dff.sort_values([y, x])
    pivot = dff.pivot_table(index=y, columns=x, values=value, aggfunc=aggfunc)
    if fig is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    else:
        fig.clf()
        ax = fig.add_subplot(111)

    sns.heatmap(
        pivot,
        annot=False,
        fmt=".2f",
        cmap=cmap,
        cbar_kws={"label": "Coexistence probability"},
        vmin=0,
        vmax=1,
        ax=ax,
    )
    ax.set_title(f"Coexistence probability\nFixed: {fixed}")
    ax.set_xlabel(x.replace("_", " "))
    ax.set_ylabel(y.replace("_", " "))
    fig.tight_layout()
    if canvas is not None:
        canvas.draw()
    return fig
