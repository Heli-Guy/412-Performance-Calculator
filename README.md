# Bell 412EPI Performance Calculator (CCG)

Web-based performance calculator for the CCG Bell 412EPI fleet, built from the CCG 412EPI library on the Bell website (BHT-412-FM-5 and supplements FMS-1.5, 9.5, 35.5, 62.5, 74.5, 80.5).

**Test build for evaluation only — not approved for operational use.** Always verify against the current flight manual and supplements.

Open `index.html` in a browser (or via GitHub Pages). Single self-contained file, works offline.

## Current version: v0.05

- **Splash screen** — 2-second launch image (as on the planned iPad app); tap to skip.
- **Hover** — IGE/OGE hover ceiling at takeoff power, MCP and EHP-kit MCP; 100% Nr (FM-5) and 103% Nr (FMS-74.5); standard / 9-seat / external load; heater off / standard / winterization; OGE Area A.
- **WAT** — FM-5 / FMS-35.5 / FMS-74.5 weight-altitude-temperature limits.
- **CAT-A** — FMS-62.5 Parts A–D (side step, backup, runway, offset backup) and FMS-74.5 Part D runway above 11,900 lb: max GW with headwind credit, drop down / height loss, TDP, rejected TO, takeoff path to 1000 ft.
- **Rate of climb** — FM-5 Fig 4-7/4-8/4-9, FMS-1.5 (winterization heater), FMS-74.5 (12,200 lb).

Chart curves are read directly from the vector drawings in the Bell PDFs (no hand digitizing); each result is shown with its calculation path drawn on the original chart.

## tools/

Python scripts that extract the chart data from the PDFs and assemble `index.html` (`build.py`, `build_catA.py`, `build_roc.py`, then `assemble.py`). The PDFs themselves are not included.
