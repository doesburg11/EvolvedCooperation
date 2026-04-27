from __future__ import annotations

from pathlib import Path
import webbrowser


def show_plotly_figure(fig, script_file: str | Path) -> Path:
    """Write a Plotly figure to HTML and try to open it in the default browser."""
    script_path = Path(script_file).resolve()
    html_path = script_path.with_suffix(".html")
    fig.write_html(str(html_path), include_plotlyjs="cdn", auto_open=False)
    print(f"Wrote interactive Plotly figure to {html_path}")

    try:
        opened = webbrowser.open_new_tab(html_path.as_uri())
    except Exception as exc:
        print(f"Could not open browser automatically: {exc}")
    else:
        if not opened:
            print("Browser did not open automatically. Open the HTML file manually.")

    return html_path
