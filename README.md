# Bell 412EPI Performance Calculator (CCG)

Web-based performance calculator for the CCG Bell 412EPI fleet, built from the CCG 412EPI library on the Bell website (BHT-412-FM-5 and supplements FMS-1.5, 9.5, 35.5, 62.5, 74.5, 80.5).

**Test build for evaluation only — not approved for operational use.** Always verify against the current flight manual and supplements.

Open `index.html` in a browser (or via GitHub Pages). Single self-contained file, works offline.

## Current version: v0.07

- **Limitations** (v0.07, first tab) — FM-5 Section 1 checks against Conditions: PA 20,000 ft, OAT envelope (−40 °C to 51.7 °C −2 °C/1,000 ft), DA 14,000 ft for TO/LDG/IGE (16,000 ft with FMS-35.5), fuel type (Jet A family above −30 °C), heater ≤21 °C, 53 Ah cold-soaked battery start ≥−25 °C, gross weight, hover crosswind/tailwind (Fig 1-3) and OGE critical azimuths; envelope chart; placard VNE (Fig 1-6) with torque, autorotation, single-autopilot and FMS-9.5 external-load values; WAT (Fig 1-2) moved here.
- **Atmosphere & wind** card in the 429 layout (PA, DA with rule of thumb, ISA deviation, headwind, crosswind, factored headwind). Tabs in 429 order: Limitations, CAT-A, Hover, ROC, Power Check.
- **Splash screen** — 2-second launch image (as on the planned iPad app); tap to skip.
- **Hover** — IGE/OGE hover ceiling at takeoff power, MCP and EHP-kit MCP; 100% Nr (FM-5) and 103% Nr (FMS-74.5); standard / 9-seat / external load; heater off / standard / winterization; OGE Area A.
- **WAT** — FM-5 / FMS-35.5 / FMS-74.5 weight-altitude-temperature limits.
- **CAT-A** — FMS-62.5 Parts A–D (side step, backup, runway, offset backup) and FMS-74.5 Part D runway above 11,900 lb: max GW with headwind credit, drop down / height loss, TDP, rejected TO, takeoff path to 1000 ft.
- **Rate of climb** — FM-5 Fig 4-7/4-8/4-9, FMS-1.5 (winterization heater), FMS-74.5 (12,200 lb).
- **Power check** (v0.06, density altitude on the same tab) — FM-5 Fig 4-1 sheets 1–2: max allowable MGT and Ng from test torque, PA and OAT; MGT/Ng margin and pass/fail for both engines; check-limit warnings (825 °C, 102.0% Ng, 66.2% Q). Lines digitized from the scanned figure (raster).
  - **Density altitude** — FM-5 Fig 4-2: DA, σ, 1/√σ and KTAS from KCAS, drawn on the chart (ISA, matches the Bell chart within ~10 ft).

Chart curves are read directly from the vector drawings in the Bell PDFs (no hand digitizing); the power assurance figure is a scan, so its straight lines are fitted from a 430 dpi render; each result is shown with its calculation path drawn on the original chart.

## tools/

Python scripts that extract the chart data from the PDFs and assemble `index.html` (`build.py`, `build_catA.py`, `build_roc.py`, `build_pwr.py`, then `assemble.py`). The PDFs themselves are not included.
