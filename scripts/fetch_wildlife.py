"""
fetch_wildlife.py
-----------------
Fetches occurrence counts from the Atlas of Living Australia (ALA) API
for wallaby and huntsman spider sightings near each Brisbane suburb,
then updates data/wildlife.json with recalculated chance ratings.

ALA API docs: https://api.ala.org.au/apps/biocache
No API key required.

Run locally:  python scripts/fetch_wildlife.py
Run in CI:    triggered by .github/workflows/update_wildlife.yml
"""

import json
import time
import datetime
import pathlib
import requests

# ── Config ────────────────────────────────────────────────────────────────────

ALA_URL  = "https://biocache-ws.ala.org.au/ws/occurrences/search"
HEADERS  = {"User-Agent": "BrisbaneSuburbScorer/1.0 (github.com/lucieranglova/brisbane-suburb-scorer)"}
RADIUS_KM = 3        # search radius around suburb centre
YEARS_BACK = 5       # only count recent observations
DELAY_S   = 1.5      # be polite to ALA servers between requests

# Species to track — latin name : display config
SPECIES = {
    "Wallabia bicolor": {
        "name": "Wallaby",
        "emoji": "🦘",
        "danger": False,
        # thresholds: (high, med) — observations in last N years within radius
        "thresholds": (5, 1),
    },
    "Atrax robustus": {
        "name": "Funnel-web spider",
        "emoji": "🕷",
        "danger": True,
        "thresholds": (3, 1),
    },
    "Isopeda": {
        "name": "Huntsman spider",
        "emoji": "🕷",
        "danger": True,
        # huntsman is very common — higher thresholds needed
        "thresholds": (10, 3),
    },
    "Cacatua": {
        "name": "Cockatoo",
        "emoji": "🦜",
        "danger": False,
        # cockatoos are everywhere in Brisbane — always 'high'
        "thresholds": (1, 0),
    },
}

# Suburbs: name → (lat, lng)
SUBURBS = {
    "West End":         (-27.4820, 153.0045),
    "Chermside":        (-27.3876, 153.0324),
    "New Farm":         (-27.4700, 153.0467),
    "Manly":            (-27.4578, 153.1764),
    "Toowong":          (-27.4852, 152.9824),
    "Paddington":       (-27.4621, 152.9892),
    "Woolloongabba":    (-27.4928, 153.0340),
    "Redcliffe":        (-27.2298, 153.1020),
    "Ascot":            (-27.4288, 153.0600),
    "Fortitude Valley": (-27.4572, 153.0364),
    "Carindale":        (-27.5030, 153.0960),
    "South Brisbane":   (-27.4758, 153.0187),
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def year_filter():
    """ALA fq date filter for the last N years."""
    since = datetime.date.today().year - YEARS_BACK
    return f"year:[{since} TO *]"


def fetch_count(taxon: str, lat: float, lng: float) -> int:
    """Return observation count for taxon within RADIUS_KM of (lat, lng)."""
    params = {
        "q":        f"taxon_name:{taxon}",
        "fq":       year_filter(),
        "lat":      lat,
        "lon":      lng,
        "radius":   RADIUS_KM,
        "pageSize": 0,         # we only need totalRecords
    }
    try:
        r = requests.get(ALA_URL, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json().get("totalRecords", 0)
    except Exception as e:
        print(f"    WARNING: ALA request failed for {taxon} @ {lat},{lng}: {e}")
        return -1   # -1 = unknown, keep existing chance


def count_to_chance(count: int, thresholds: tuple) -> str:
    """Convert raw observation count to 'high' / 'med' / 'low'."""
    if count < 0:
        return None   # unknown — keep existing
    high, med = thresholds
    if count >= high:
        return "high"
    if count >= med:
        return "med"
    return "low"


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    root      = pathlib.Path(__file__).parent.parent
    wl_path   = root / "data" / "wildlife.json"
    sub_path  = root / "data" / "suburbs.json"

    # Load existing wildlife.json to keep structure, only update chance values
    with open(wl_path) as f:
        wildlife = json.load(f)

    # Load suburbs.json to update wildlife scores
    with open(sub_path) as f:
        suburbs = json.load(f)

    print(f"Fetching ALA data (radius={RADIUS_KM}km, last {YEARS_BACK} years)...\n")

    suburb_scores = {}   # suburb → wildlife score (1-10)

    for suburb_name, (lat, lng) in SUBURBS.items():
        print(f"  {suburb_name}")
        suburb_wildlife = []
        score_components = []

        for taxon, cfg in SPECIES.items():
            count = fetch_count(taxon, lat, lng)
            chance = count_to_chance(count, cfg["thresholds"])
            print(f"    {cfg['name']:22} → {count:4} obs  → {chance or 'unchanged'}")

            # Find existing entry for this animal in wildlife.json
            existing = next(
                (a for a in wildlife.get(suburb_name, []) if a["name"] == cfg["name"]),
                None
            )

            if chance is None:
                # API failed — keep existing entry unchanged
                if existing:
                    suburb_wildlife.append(existing)
                continue

            suburb_wildlife.append({
                "name":   cfg["name"],
                "emoji":  cfg["emoji"],
                "chance": chance,
                "danger": cfg["danger"],
            })

            # Contribute to wildlife score
            # Kangaroo/wallaby sightings weighted 3x, spiders 1x, cockatoo 0 (everywhere)
            if cfg["name"] == "Wallaby":
                score_components.append({"high": 9, "med": 5, "low": 1}[chance])
            elif cfg["name"] == "Funnel-web spider":
                score_components.append({"high": 4, "med": 2, "low": 1}[chance])
            elif cfg["name"] == "Huntsman spider":
                score_components.append({"high": 3, "med": 2, "low": 1}[chance])
            # Cockatoo: always present, don't affect score

            time.sleep(DELAY_S)

        wildlife[suburb_name] = suburb_wildlife

        # Calculate composite wildlife score (1-10)
        if score_components:
            raw = sum(score_components) / len(score_components)
            # Normalise: max possible ~= 8 (wallaby high=9 + funnel-web high=4 + huntsman high=3) / 3
            score = max(1, min(10, round(raw)))
        else:
            score = 1
        suburb_scores[suburb_name] = score
        print(f"    → wildlife score: {score}\n")

    # Update suburbs.json wildlife scores
    for s in suburbs:
        if s["name"] in suburb_scores:
            s["scores"]["wildlife"] = suburb_scores[s["name"]]

    # Write updated files
    with open(wl_path, "w") as f:
        json.dump(wildlife, f, indent=2, ensure_ascii=False)
    print(f"✓ Updated {wl_path}")

    with open(sub_path, "w") as f:
        json.dump(suburbs, f, indent=2, ensure_ascii=False)
    print(f"✓ Updated {sub_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
