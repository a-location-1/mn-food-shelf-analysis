"""
Scrape all food shelf locations from window.FWP_JSON embedded in the
hungersolutions.org page source, then reverse geocode each point to a
county via the Census API.

All 552 locations are in the initial page load — no pagination needed.

Requirements:
    pip install requests beautifulsoup4 pandas

Usage:
    python scrape_and_geocode.py

Output:
    food_shelves_enriched.pkl
"""

import re
import json
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL   = "https://www.hungersolutions.org/find-help/"
HEADERS    = {"User-Agent": "Mozilla/5.0"}
OUTPUT_PKL = "data/food_shelves_enriched.pkl"

MILES_RE = re.compile(r"\(\s*[\d.,]*\s*miles?\s*away\s*\)", re.IGNORECASE)

# ── Step 1: Extract markers from window.FWP_JSON ──────────────────────────────

def scrape_markers() -> pd.DataFrame:
    print("Fetching page...")
    resp = requests.get(BASE_URL, params={"fwp_categories": "food-shelves"},
                        headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the script tag containing FWP_JSON
    fwp_json = None
    for script in soup.find_all("script"):
        text = script.string or ""
        if "window.FWP_JSON" in text:
            m = re.search(r"window\.FWP_JSON\s*=\s*(\{.*\});", text, re.DOTALL)
            if m:
                fwp_json = json.loads(m.group(1))
                break

    if not fwp_json:
        raise RuntimeError("Could not find window.FWP_JSON in page source.")

    locations = fwp_json["preload_data"]["settings"]["map"]["locations"]
    print(f"Found {len(locations)} locations in FWP_JSON.")

    rows = []
    for loc in locations:
        lat = loc["position"]["lat"]
        lng = loc["position"]["lng"]

        # content is an HTML snippet:
        # <strong>Name</strong><br>\nAddress<br>\n<a ...>Get Directions</a>
        content_soup = BeautifulSoup(loc["content"], "html.parser")

        name = content_soup.find("strong")
        name = name.get_text(strip=True) if name else ""
        name = MILES_RE.sub("", name).strip()

        # Address: all text lines that aren't the name and aren't the directions link
        lines = [t.strip() for t in content_soup.get_text("\n").splitlines()
                 if t.strip() and t.strip() != name and "Get Directions" not in t]
        address = lines[0] if lines else ""

        rows.append({"name": name, "address": address, "lat": lat, "lng": lng})

    return pd.DataFrame(rows)


# ── Step 2: Reverse geocode each lat/lng → county ─────────────────────────────

REVERSE_URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"

def reverse_geocode(lat: float, lng: float) -> str | None:
    params = {
        "x":         lng,
        "y":         lat,
        "benchmark": "Public_AR_Current",
        "vintage":   "Current_Current",
        "layers":    "Counties",
        "format":    "json",
    }
    try:
        resp = requests.get(REVERSE_URL, params=params, timeout=15)
        resp.raise_for_status()
        counties = resp.json()["result"]["geographies"].get("Counties", [])
        if counties:
            return counties[0]["NAME"]   # e.g. "Hennepin County"
    except Exception as e:
        print(f"    reverse geocode error ({lat:.4f},{lng:.4f}): {e}")
    return None


def geocode_all(df: pd.DataFrame) -> pd.DataFrame:
    print(f"\nReverse geocoding {len(df)} locations...")
    counties = []
    for i, (_, row) in enumerate(df.iterrows(), 1):
        if i % 50 == 0 or i == 1:
            print(f"  {i}/{len(df)}...")
        county = reverse_geocode(row["lat"], row["lng"])
        counties.append(county)
        time.sleep(0.1)   # ~10 req/sec — well within Census limits
    df = df.copy()
    df["county"] = counties
    return df


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    df = scrape_markers()
    print(f"\nSample:\n{df.head(5).to_string(index=False)}\n")

    df = geocode_all(df)

    matched = df["county"].notna().sum()
    print(f"\nCounty assigned: {matched}/{len(df)}")

    null_rows = df[df.isna().any(axis=1)]
    if not null_rows.empty:
        print(f"\nRows with any null ({len(null_rows)}):")
        print(null_rows.to_string(index=False))

    df.to_pickle(OUTPUT_PKL)
    print(f"\nSaved to {OUTPUT_PKL}")
    print(df[["name", "address", "county"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
