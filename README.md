# brisbane-suburb-scorer
# Brisbane Suburb Scorer 🏡

An interactive dashboard for ranking Brisbane suburbs based on your personal priorities — built as a portfolio project while planning a move from Prague to Brisbane.

**Live demo:** [lucieranglova.github.io/brisbane-suburb-scorer](https://lucieranglova.github.io/brisbane-suburb-scorer)

---

## Features

- **Weighted scoring** — adjust sliders for rent, CBD proximity, transit, beach, lifestyle, safety and wildlife
- **Commute calculator** — enter any Brisbane address (workplace or school/uni); straight-line distance is calculated live via [Nominatim](https://nominatim.openstreetmap.org/) (free, no API key needed)
- **Interactive maps** — each suburb detail opens a Leaflet.js map showing the suburb and your commute destinations with distance lines
- **Wildlife guide** — shows which animals from a custom list you're likely to spot in each suburb, with danger indicators for spiders, jellyfish and sharks
- **Filters** — quickly narrow to beach suburbs, affordable areas, great transit or wildlife hotspots
- **Share link** — your priority weights are encoded in the URL so you can share your personal ranking

---

## Tech stack

| Layer | Tech |
|---|---|
| UI | Vanilla HTML + CSS + JS (no framework) |
| Maps | [Leaflet.js](https://leafletjs.com/) + OpenStreetMap tiles |
| Geocoding | [Nominatim](https://nominatim.openstreetmap.org/) (free, no key) |
| Data | Static JSON files (`data/`) |
| Hosting | GitHub Pages |

---

## Project structure

```
brisbane-suburb-scorer/
├── index.html          # Main app — UI, CSS, JS
├── data/
│   ├── suburbs.json    # 12 suburbs with scores and info
│   ├── wildlife.json   # Wildlife sightings per suburb
│   └── criteria.json   # Scoring criteria and default weights
├── assets/
│   ├── og-image.png    # Open Graph preview image
│   └── favicon.svg     # Browser tab icon
└── README.md
```

---

## Running locally

Because the app fetches JSON files, you need a local server (browsers block `fetch()` on `file://`):

```bash
# Python 3
python -m http.server 8000

# Node.js
npx serve .
```

Then open `http://localhost:8000`.

---

## Adding a suburb

Edit `data/suburbs.json` — add a new object following the existing structure:

```json
{
  "name": "Suburb Name",
  "lat": -27.0000,
  "lng": 153.0000,
  "tags": [["Tag", "tg"]],
  "scores": {
    "rent": 7, "cbd": 5, "transit": 6,
    "beach": 3, "cafe": 7, "safe": 8, "wildlife": 5
  },
  "info": {
    "avgRent": "$500/wk",
    "cbdMin": "25 min",
    "beachKm": "20 km"
  },
  "url": "https://www.domain.com.au/rent/suburb-name-qld-XXXX/"
}
```

Tag colour classes: `tg` (green), `ta` (amber), `tb` (blue), `tc` (coral), `tn` (neutral).

All scores are on a 1–10 scale where 10 = best for that criterion (so `rent: 10` = very affordable).

---

## Adding wildlife to a suburb

Edit `data/wildlife.json`. Each entry:

```json
{ "name": "Animal name", "emoji": "🦘", "chance": "high", "danger": false }
```

- `chance`: `"high"` | `"med"` | `"low"`
- `danger`: `true` for spiders, jellyfish, sharks etc. — gets a red border in the UI

---

## About

Built by [Lucie Ranglová](https://github.com/lucieranglova) as a practical side project combining QA skills, JavaScript, and genuine research for a planned move to Brisbane, Australia.

Part of a broader collection of Brisbane/Australia-themed automation projects.
