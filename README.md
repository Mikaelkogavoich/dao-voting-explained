# How DAO voting works now

A short member guide to voting on the Redbelly DAO governance platform: how to vote, when eligibility is checked, why a wallet verified after a proposal opens cannot vote on it, how many votes each verified account gets, and the known limits of the current setup.

## Deliverables

| Brief item | File |
|---|---|
| 1. The guide | `index.html` (web page) and `guide.pdf` (6 pages, printed from the same page). The PDF also opens inside the page with **Read PDF**, or directly at `/#read-pdf` |
| 2. Diagrams as images, placed in the guide | `diagrams/*.png` (2x) and `diagrams/*.svg`, inlined in sections 01, 03 and 05 |
| 3. Editable source of the diagrams | `diagrams/*.svg`, hand-written SVG. See `diagrams/README.md` |
| Evidence for every rule | `SOURCES.md` |
| Re-runnable checks | `verify/check.py` |

The three diagrams:

1. `01-path-to-vote`: from verification to a counted vote (the path the brief asks for).
2. `02-snapshot-timeline`: when eligibility is checked, and why a late wallet misses that proposal.
3. `03-wallets-and-votes`: how several wallets under one verification are counted.

## Verification

```bash
python3 verify/check.py          # offline: files, brand voice, no outdated rules, no advice, no credit
python3 verify/check.py --live   # plus every rule, re-checked against the live platform
```

The live run checks the platform's interface text, its public API, its published code, Redbelly Network mainnet and the Redbelly Access portal. It also finds a wallet that was enabled just after a proposal's snapshot and confirms the platform gives it 0 power on that proposal. Results are written to `verify/report.json`.

## Deploy

Static files, no build step. On Vercel: Add New, Project, import the repository, Framework Preset **Other**, leave Build Command and Output Directory empty, Deploy. `index.html` is at the root.

## Edit and rebuild

- Guide text: `tools/index.template.html`. Troubleshooting rows and the evidence table: `tools/build.py`. Measured numbers and the last verified date: `tools/data.json`.
- `python3 tools/build.py` writes `index.html` with the diagrams inlined, so they follow the page's light or dark theme.
- `node tools/render.js` exports the diagram PNGs and prints `guide.pdf` (needs Node and Playwright with Chromium).

## Brand

The favicon is `assets/dao-mark.svg`: the DAO mark traced to vector from the kit's icon, with its background removed. It switches to light ink when the browser is in dark mode, the same way the kit pairs dark-ink and light-ink logos. `assets/icon.png` is a transparent PNG fallback.


Built to the Task Board brand kit: Be Vietnam Pro and JetBrains Mono, the single brand red, slate surfaces, 4 and 8 px radii, tonal depth, dark by default with a light theme, no em dashes and no emoji. Logo files are the kit's own `dao-logo-on-dark.png` and `dao-logo-on-light.png`, scaled by height.
