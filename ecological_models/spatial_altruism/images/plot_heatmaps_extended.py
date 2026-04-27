# Heatmap Visualization for Altruism Grid Search
from pathlib import Path
import sys

import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from ecological_models.spatial_altruism.utils.plotting import plot_heatmap_embedded
else:
    from ..utils.plotting import plot_heatmap_embedded

# Load results
df = pd.read_csv('ecological_models/spatial_altruism/data/grid_search_results_extended.csv')


# Get all unique harshness values from the data
harshness_options = sorted(df['harshness'].unique())


def on_harshness_change():
    selected_harshness = float(harshness_var.get())
    fixed = {
        'disease': 0.26,
        'harshness': selected_harshness,
    }
    plot_heatmap_embedded(
        df,
        'benefit_from_altruism',
        'cost_of_altruism',
        fixed, value='coexist_prob',
        cmap='viridis',
        canvas=canvas,
        fig=fig
    )


root = tk.Tk()
root.title("Altruism Grid Search Heatmap")

frame = ttk.Frame(root, padding=10)
frame.pack(side=tk.LEFT, fill=tk.Y)

ttk.Label(
    frame, text="Select harshness:",
    font=("Helvetica", 18, "bold")
).pack(anchor=tk.W, pady=5)
harshness_var = tk.StringVar(value=str(harshness_options[0]))


radio_style = ttk.Style()
radio_style.configure(
    'Big.TRadiobutton',
    font=('Helvetica', 16),
    indicatorsize=20,
    padding=0  # <-- Minimal padding for tightest spacing
)

for h in harshness_options:
    ttk.Radiobutton(
        frame,
        text=f"{h}",
        variable=harshness_var,
        value=str(h),
        command=on_harshness_change,
        style='Big.TRadiobutton'
    ).pack(anchor=tk.W, pady=0)  # <-- No extra vertical space between buttons

# Matplotlib figure and canvas
fig = plt.Figure(figsize=(8, 6))
canvas_frame = ttk.Frame(root)
canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Initial plot
on_harshness_change()

root.mainloop()
