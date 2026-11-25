# Bell 412EPI Performance Calculator (CCG)

Web-based performance calculator for the CCG Bell 412EPI fleet, built from the CCG 412EPI library on the Bell website (BHT-412-FM-5 and supplements FMS-1.5, 9.5, 35.5, 62.5, 74.5, 80.5).

**Test build for evaluation only — not approved for operational use.** Always verify against the current flight manual and supplements.

Open `index.html` in a browser (or via GitHub Pages). Single self-contained file, works offline.

## Current version: v0.11

### v0.11
- Fix: tapping a chart to enlarge it showed only the calculation lines — the chart image was being corrupted when the arrow markers were renamed for the zoom view.
- CAT-A Helipad Part B / D inputs laid out like the 429 (backup obstacle height and distance, flyaway obstacle height above the TDP card).

### v0.10
- Limitations: H-V diagram removed.
- CAT-A Helipad: profile selector on its own row, profile inputs on the next row (no clipped text); Performance Class 2 cards moved up under the CAT-A cards, PC2 charts at the bottom.
- Charts no longer stretch to the height of their neighbour (no blank chart panels).
- Power Check in the 429 layout: Engine 1 / Engine 2 input boxes, PASS / BELOW MIN SPEC boxes with MGT and NG margin cards, check-limit messages.

### v0.09
- Limitations: WAT cards moved up under the limitation tiles; fuel and H-V status below; reference charts (WAT, H-V diagram) at the bottom.

### v0.08 — brought in line with the 429 app (v0.86), plus 412-only additions
- 429 layout: Chrome-style tabs (Limitations, CAT-A Helipad, CAT-A Runway, Stay Up Weight, Hover, ROC, Power Check), dark mode, sticky Conditions / Aircraft configuration frames, **Current METAR** button, relative-wind pictogram with the FM-5 Fig 4-3 OGE critical azimuths, ON/OFF switches (heater FMS-1.5, air conditioner, ≤ 9 pax FMS-35.5, hook load FMS-9.5), input limits with notes, weights in Lbs, settings and tab remembered.
- **CAT-A Helipad** (Parts A / B / D) and **CAT-A Runway** (Part C, FMS-74.5 Part D above 11,900 lb): 429-style cards in fixed rows (max T/O weight, GW margin, TDP/LDP, obstacle clearance / backup obstacle, height loss, OEI takeoff, stage 1, level acceleration, stage 2, total), 2-min OEI ROC at V_TOSS (FMS-62.5 Fig 4A-8) and OEI MCP ROC at V_Y (FM-5 Fig 4-9) cards, the Bell emergency profile figure (3A-1 / 3B-1 / 3C-1 / 3D-1) with this takeoff's values and a distance strip. Backup obstacle check from MD-5 Fig 4-11; flyaway obstacle raises the TDP (height loss + 15 ft + obstacle). Results dashed when GW is over the CAT-A weight, wind is outside limits, the backup obstacle is not clear, or heater / A/C is ON (FMS-62.5: cabin heat and A/C OFF).
- **Stay Up Weight**: zero-ROC weight and OEI ROC at cruise altitude / OAT (continuous OEI FM-5 Fig 4-9; 2-min OEI FMS-62.5 Fig 4A-8). The PT6T-9 has no 30-min OEI rating.
- **Hover**: cards like the aircraft HOVER PERFORMANCE page (IGE min spec, OGE MCP with EHP, OGE T/O power; 100% N_R, 103% value below) — match the training-deck screenshots within 0.3 %. EHP max continuous mast torque below 60 KIAS (FMS-80.5 Fig 1A-8 / 1B-8, 90.3 % at 8,000 ft / 12 °C). OEI hover weight, 2-min and 30-sec (MD-5 Fig 4-3A / 4-3B, Bell example within 0.2 %).
- **Performance Class 2 helideck** (MD-5 Fig 4-4 WAT, Fig 4-5 drop-down takeoff / balked landing) on the Helipad tab — Bell examples 11,650 lb (exact) and 89 ft drop-down (app 91 ft).
- Air conditioner (Air Comm 412AC-104): −111 ft/min AEO ROC, −150 lb hover; CAT-A not valid with A/C ON.
- Limitations: H-V diagram applicability (limitation only with more than 9 passenger seats when not flown CAT-A — FMS-35.5).
- Fix: FMS-80.5 Fig 4A-5 (100 %, heater off, ≥ 0 °C) 30 °C line was picked up from the Area B shading edge.


- **Limitations** (v0.07, first tab) — 429-style: OAT limits and margin (FM-5 1-11), fuel temperature limits for the fuel selected in Conditions (Jet A / A-1 above −30 °C; Jet B all temperatures, FM-5 1-17-A), valid-fuels list, and the WAT charts (Fig 1-2, FMS-74.5 Fig 1A-2).
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
