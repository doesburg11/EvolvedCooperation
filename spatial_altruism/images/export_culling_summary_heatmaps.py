"""Export static culling summary heatmaps for the website."""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from spatial_altruism.utils.plotting import plot_heatmap_embedded
else:
    from ..utils.plotting import plot_heatmap_embedded


DATA_PATH = Path("spatial_altruism/data/culling_grid_search_results.csv")
OUTPUT_DIR = Path("docs/data/spatial-altruism-demo")
PANELS = (
    {
        "model_variant": "uniform_culling",
        "disturbance_fraction": 0.50,
        "outputs": (
            {
                "metric": "coexist_prob",
                "filename": "culling_uniform_fraction_050_coexist_prob.png",
                "title": "Coexistence probability",
                "cbar_label": "Coexistence probability",
                "cmap": "viridis",
                "vmin": 0,
                "vmax": 1,
            },
            {
                "metric": "occupied_avg",
                "filename": "culling_uniform_fraction_050_occupied_avg.png",
                "title": "Average occupied fraction",
                "cbar_label": "Average occupied fraction",
                "cmap": "YlGnBu",
                "vmin": 0,
                "vmax": 1,
            },
        ),
    },
    {
        "model_variant": "compact_swath",
        "disturbance_fraction": 0.50,
        "outputs": (
            {
                "metric": "coexist_prob",
                "filename": "culling_compact_swath_fraction_050_coexist_prob.png",
                "title": "Coexistence probability",
                "cbar_label": "Coexistence probability",
                "cmap": "viridis",
                "vmin": 0,
                "vmax": 1,
            },
            {
                "metric": "occupied_avg",
                "filename": "culling_compact_swath_fraction_050_occupied_avg.png",
                "title": "Average occupied fraction",
                "cbar_label": "Average occupied fraction",
                "cmap": "YlGnBu",
                "vmin": 0,
                "vmax": 1,
            },
        ),
    },
)


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    harshness = float(sorted(df["harshness"].unique())[0])
    disturbance_interval = int(sorted(df["disturbance_interval"].unique())[0])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for panel in PANELS:
        fixed = {
            "model_variant": panel["model_variant"],
            "harshness": harshness,
            "disturbance_interval": disturbance_interval,
            "disturbance_fraction": panel["disturbance_fraction"],
        }
        for output in panel["outputs"]:
            title = (
                f"{output['title']}\n{panel['model_variant']}, "
                f"fraction={panel['disturbance_fraction']:.2f}, interval={disturbance_interval}"
            )
            fig = plot_heatmap_embedded(
                df,
                "benefit_from_altruism",
                "cost_of_altruism",
                fixed,
                value=output["metric"],
                cmap=output["cmap"],
                title=title,
                cbar_label=output["cbar_label"],
                vmin=output["vmin"],
                vmax=output["vmax"],
            )
            output_path = OUTPUT_DIR / output["filename"]
            fig.savefig(output_path, dpi=180, bbox_inches="tight")
            plt.close(fig)
            print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
