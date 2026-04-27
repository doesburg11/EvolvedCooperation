"""Interactive heatmaps for culling-variant sweep results."""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from ecological_models.spatial_altruism.utils.plotting import plot_heatmap_embedded
else:
    from ..utils.plotting import plot_heatmap_embedded


df = pd.read_csv("ecological_models/spatial_altruism/data/culling_grid_search_results.csv")

METRICS = {
    "coexist_prob": {"label": "Coexistence probability", "cmap": "viridis", "vmin": 0, "vmax": 1},
    "altruist_avg": {"label": "Average altruist count", "cmap": "RdPu", "vmin": None, "vmax": None},
    "selfish_avg": {"label": "Average selfish count", "cmap": "Blues", "vmin": None, "vmax": None},
    "black_avg": {"label": "Average empty count", "cmap": "Greys", "vmin": None, "vmax": None},
    "occupied_avg": {"label": "Average occupied fraction", "cmap": "YlGnBu", "vmin": 0, "vmax": 1},
}


def sorted_values(column):
    return sorted(df[column].unique())


variant_options = sorted_values("model_variant")
harshness_options = sorted_values("harshness")
interval_options = sorted_values("disturbance_interval")
fraction_options = sorted_values("disturbance_fraction")


def render():
    metric = metric_var.get()
    metric_cfg = METRICS[metric]
    fixed = {
        "model_variant": variant_var.get(),
        "harshness": float(harshness_var.get()),
        "disturbance_interval": int(interval_var.get()),
        "disturbance_fraction": float(fraction_var.get()),
    }
    title = (
        f"{metric_cfg['label']}\n"
        f"variant={fixed['model_variant']}, harshness={fixed['harshness']}, "
        f"interval={fixed['disturbance_interval']}, fraction={fixed['disturbance_fraction']}"
    )
    plot_heatmap_embedded(
        df,
        "benefit_from_altruism",
        "cost_of_altruism",
        fixed,
        value=metric,
        cmap=metric_cfg["cmap"],
        canvas=canvas,
        fig=fig,
        title=title,
        cbar_label=metric_cfg["label"],
        vmin=metric_cfg["vmin"],
        vmax=metric_cfg["vmax"],
    )


root = tk.Tk()
root.title("Spatial Altruism Culling Heatmaps")

controls = ttk.Frame(root, padding=10)
controls.pack(side=tk.LEFT, fill=tk.Y)

ttk.Label(controls, text="Variant", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=(0, 4))
variant_var = tk.StringVar(value=str(variant_options[0]))
variant_box = ttk.Combobox(controls, textvariable=variant_var, values=variant_options, state="readonly")
variant_box.pack(anchor=tk.W, fill=tk.X, pady=(0, 10))

ttk.Label(controls, text="Metric", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=(0, 4))
metric_var = tk.StringVar(value="coexist_prob")
metric_box = ttk.Combobox(controls, textvariable=metric_var, values=list(METRICS.keys()), state="readonly")
metric_box.pack(anchor=tk.W, fill=tk.X, pady=(0, 10))

ttk.Label(controls, text="Harshness", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=(0, 4))
harshness_var = tk.StringVar(value=str(harshness_options[0]))
harshness_box = ttk.Combobox(controls, textvariable=harshness_var, values=harshness_options, state="readonly")
harshness_box.pack(anchor=tk.W, fill=tk.X, pady=(0, 10))

ttk.Label(controls, text="Disturbance Interval", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=(0, 4))
interval_var = tk.StringVar(value=str(interval_options[0]))
interval_box = ttk.Combobox(controls, textvariable=interval_var, values=interval_options, state="readonly")
interval_box.pack(anchor=tk.W, fill=tk.X, pady=(0, 10))

ttk.Label(controls, text="Disturbance Fraction", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=(0, 4))
fraction_var = tk.StringVar(value=str(fraction_options[0]))
fraction_box = ttk.Combobox(controls, textvariable=fraction_var, values=fraction_options, state="readonly")
fraction_box.pack(anchor=tk.W, fill=tk.X, pady=(0, 10))

for widget in (variant_box, metric_box, harshness_box, interval_box, fraction_box):
    widget.bind("<<ComboboxSelected>>", lambda _event: render())

fig = plt.Figure(figsize=(8, 6))
canvas_frame = ttk.Frame(root)
canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

render()

root.mainloop()
