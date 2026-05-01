"""
Scrape food shelf names + coordinates from hungersolutions.org page source,
then reverse geocode each point to a county via the Census API.

No address parsing. No batch geocoder format issues.

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

BASE_URL = "https://www.hungersolutions.org/find-help/"
HEADERS  = {"User-Agent": "Mozilla/5.0"}

OUTPUT_PKL = "data/food_shelves_enriched.pkl"

# ── Step 1: Scrape all pages for name + lat/lon ───────────────────────────────

def fetch_page_source(page_num: int) -> str:
    params = {
        "fwp_categories": "food-shelves",
        "fwp_paged": page_num,
    }
    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text

def extract_markers(html: str) -> list[dict]:
    """
    Pull location data from the page source.
    The map plugin embeds markers as JSON objects in <script> tags or
    data attributes. We look for the pattern the sniffer found:
        {"lat": 44.764..., "lng": -93.185...}
    and try to grab the associated name from nearby context.
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # Strategy A: find all <script> blocks and parse JSON marker arrays
    for script in soup.find_all("script"):
        text = script.string or ""
        # Look for arrays of marker objects with lat/lng
        arrays = re.findall(r'\[\s*(\{[^[\]]*"lat"[^[\]]*\}[\s,]*)+\]', text)
        for arr_str in arrays:
            try:
                markers = json.loads(arr_str if arr_str.startswith("[") else f"[{arr_str}]")
                for m in markers:
                    if "lat" in m and "lng" in m:
                        results.append({
                            "name":    m.get("title", m.get("name", m.get("label", ""))),
                            "address": m.get("address", m.get("street_address", "")),
                            "lat":     float(m["lat"]),
                            "lng":     float(m["lng"]),
                        })
            except Exception:
                pass

    # Strategy B: regex-extract every individual {lat, lng} blob in the full HTML
    # and pair it with the nearest title/name string in a window around it
    if not results:
        # Find every occurrence of a lat/lng pair
        for m in re.finditer(
            r'\{[^{}]*"lat"\s*:\s*(-?\d+\.\d+)[^{}]*"lng"\s*:\s*(-?\d+\.\d+)[^{}]*\}',
            html,
        ):
            lat = float(m.group(1))
            lng = float(m.group(2))
            # Search for a "title" or "name" key nearby (within 300 chars before)
            window = html[max(0, m.start() - 300): m.start()]
            name_match = re.search(r'"(?:title|name|label)"\s*:\s*"([^"]+)"', window)
            addr_match = re.search(r'"(?:address|street_address|location)"\s*:\s*"([^"]+)"', window)
            results.append({
                "name":    name_match.group(1) if name_match else "",
                "address": addr_match.group(1) if addr_match else "",
                "lat":     lat,
                "lng":     lng,
            })

    # Strategy C: look for elements with data-lat / data-lng attributes
    for el in soup.find_all(attrs={"data-lat": True, "data-lng": True}):
        try:
            name_el = el.find(class_=re.compile(r"title|name|heading", re.I))
            results.append({
                "name":    name_el.get_text(strip=True) if name_el else el.get("data-title", ""),
                "address": el.get("data-address", ""),
                "lat":     float(el["data-lat"]),
                "lng":     float(el["data-lng"]),
            })
        except (ValueError, KeyError):
            pass

    return results


def scrape_all_pages() -> pd.DataFrame:
    all_markers = []
    page = 1

    print("Scraping page 1 to detect total pages...")
    html = fetch_page_source(1)
    markers = extract_markers(html)
    print(f"  Page 1: {len(markers)} markers found")
    all_markers.extend(markers)

    # Try to detect total page count from pagination
    soup = BeautifulSoup(html, "html.parser")

    # Look for FacetWP pager or standard WP pagination
    total_pages = 1
    pager = soup.select_one(".fwp-pager, .facetwp-pager")
    if pager:
        page_links = pager.find_all("a")
        nums = [int(a.get_text()) for a in page_links if a.get_text().isdigit()]
        if nums:
            total_pages = max(nums)

    # Fallback: look for last page number anywhere in pager text
    if total_pages == 1:
        pager_text = soup.get_text()
        m = re.search(r'of\s+(\d+)\s+pages?', pager_text, re.IGNORECASE)
        if m:
            total_pages = int(m.group(1))

    print(f"  Detected {total_pages} total page(s).")

    for page in range(2, total_pages + 1):
        print(f"  Scraping page {page}/{total_pages}...")
        try:
            html = fetch_page_source(page)
            markers = extract_markers(html)
            print(f"    {len(markers)} markers")
            all_markers.extend(markers)
        except Exception as e:
            print(f"    ERROR: {e}")
        time.sleep(0.5)

    df = pd.DataFrame(all_markers).drop_duplicates(subset=["lat", "lng"])
    print(f"\nTotal unique markers scraped: {len(df)}")
    return df


# ── Step 2: Reverse geocode each lat/lng → county ─────────────────────────────

REVERSE_URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"

def reverse_geocode(lat: float, lng: float) -> str | None:
    """Single Census reverse geocode call. Returns county name or None."""
    params = {
        "x":         lng,   # Census uses x=longitude, y=latitude
        "y":         lat,
        "benchmark": "Public_AR_Current",
        "vintage":   "Current_Current",
        "layers":    "Counties",
        "format":    "json",
    }
    try:
        resp = requests.get(REVERSE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        geographies = data.get("result", {}).get("geographies", {})
        counties = geographies.get("Counties", [])
        if counties:
            return counties[0].get("NAME")   # e.g. "Hennepin County"
    except Exception as e:
        print(f"    reverse geocode error ({lat},{lng}): {e}")
    return None


def geocode_all(df: pd.DataFrame) -> pd.DataFrame:
    counties = []
    total = len(df)
    for i, (_, row) in enumerate(df.iterrows(), 1):
        if i % 25 == 0 or i == 1:
            print(f"  Reverse geocoding {i}/{total}...")
        county = reverse_geocode(row["lat"], row["lng"])
        counties.append(county)
        time.sleep(0.1)   # ~10 req/sec — well within Census limits
    df["county"] = counties
    return df


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    # 1. Scrape
    print("=" * 55)
    print("STEP 1: Scraping map markers from page source")
    print("=" * 55)
    df = scrape_all_pages()

    if df.empty:
        print("\nNo markers found. The map plugin may load markers via a")
        print("separate XHR after page load. Try opening the site in")
        print("Chrome DevTools > Network > Fetch/XHR and look for a")
        print("request returning JSON with lat/lng arrays.")
        return

    print(f"\nSample data:\n{df.head(5).to_string(index=False)}")

    # 2. Reverse geocode
    print("\n" + "=" * 55)
    print("STEP 2: Reverse geocoding to county")
    print("=" * 55)
    df = geocode_all(df)

    matched = df["county"].notna().sum()
    print(f"\nCounty assigned: {matched}/{len(df)}")
    if df["county"].isna().any():
        print("Unresolved:")
        print(df[df["county"].isna()][["name", "lat", "lng"]].to_string(index=False))

    # 3. Save
    keep = ["name", "address", "lat", "lng", "county"]
    df = df[[c for c in keep if c in df.columns]]
    df.to_pickle(OUTPUT_PKL)
    print(f"\nSaved to {OUTPUT_PKL}")
    print(df[["name", "county"]].head(15).to_string(index=False))


if __name__ == "__main__":
    main()