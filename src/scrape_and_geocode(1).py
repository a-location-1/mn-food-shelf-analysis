"""
Scrape all food shelf locations from hungersolutions.org, then reverse
geocode each point to a county via the Census API.

Strategy:
  - Page 1: parse window.FWP_JSON from the HTML (gives us nonce + first batch)
  - Remaining pages: POST to the FacetWP refresh endpoint using the nonce,
    requesting all rows in one shot (per_page = total_rows)
  - Parse name + address from the HTML content field of each map marker
  - Reverse geocode lat/lng → county via Census coordinates endpoint

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


# ── Step 1: Scrape all markers ────────────────────────────────────────────────

def parse_locations(locations: list) -> list[dict]:
    """Extract name, address, lat, lng from a FacetWP map locations list."""
    rows = []
    for loc in locations:
        lat = loc["position"]["lat"]
        lng = loc["position"]["lng"]

        content_soup = BeautifulSoup(loc["content"], "html.parser")

        name_el = content_soup.find("strong")
        name = name_el.get_text(strip=True) if name_el else ""
        name = MILES_RE.sub("", name).strip()

        lines = [
            t.strip() for t in content_soup.get_text("\n").splitlines()
            if t.strip() and t.strip() != name and "Get Directions" not in t
        ]
        address = lines[0] if lines else ""

        rows.append({"name": name, "address": address, "lat": lat, "lng": lng})
    return rows


def scrape_markers() -> pd.DataFrame:
    def fetch_fwp_json(page: int) -> dict:
        params = {"fwp_categories": "food-shelves", "fwp_paged": page}
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for script in soup.find_all("script"):
            text = script.string or ""
            if "window.FWP_JSON" in text:
                m = re.search(r"window\.FWP_JSON\s*=\s*(\{.*?\});\s*$",
                              text, re.DOTALL | re.MULTILINE)
                if m:
                    return json.loads(m.group(1))
        return {}

    print("Fetching page 1...")
    fwp = fetch_fwp_json(1)
    if not fwp:
        raise RuntimeError("Could not find window.FWP_JSON on page 1.")

    pager       = fwp["preload_data"]["settings"]["pager"]
    total_pages = pager["total_pages"]
    total_rows  = pager["total_rows"]
    print(f"  Total rows: {total_rows}, pages: {total_pages}")

    all_rows = parse_locations(fwp["preload_data"]["settings"]["map"]["locations"])
    print(f"  Page 1: {len(all_rows)} markers")

    for page in range(2, total_pages + 1):
        print(f"  Fetching page {page}/{total_pages}...")
        try:
            fwp = fetch_fwp_json(page)
            locations = fwp["preload_data"]["settings"]["map"]["locations"]
            rows = parse_locations(locations)
            print(f"    {len(rows)} markers")
            all_rows.extend(rows)
        except Exception as e:
            print(f"    ERROR: {e}")
        time.sleep(0.5)

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["lat", "lng"])
    print(f"\nTotal unique markers: {len(df)}")
    return df


# ── Step 2: Reverse geocode lat/lng → county ──────────────────────────────────

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
            return counties[0]["NAME"]
    except Exception as e:
        print(f"    reverse geocode error ({lat:.4f},{lng:.4f}): {e}")
    return None


def geocode_all(df: pd.DataFrame) -> pd.DataFrame:
    print(f"\nReverse geocoding {len(df)} locations...")
    counties = []
    for i, (_, row) in enumerate(df.iterrows(), 1):
        if i % 50 == 0 or i == 1:
            print(f"  {i}/{len(df)}...")
        counties.append(reverse_geocode(row["lat"], row["lng"]))
        time.sleep(0.1)
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
        print(null_rows[["name", "address", "lat", "lng", "county"]].to_string(index=False))

    df.to_pickle(OUTPUT_PKL)
    print(f"\nSaved to {OUTPUT_PKL}")
    print(df[["name", "address", "county"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
