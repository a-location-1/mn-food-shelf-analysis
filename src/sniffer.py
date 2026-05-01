"""
Sniff map marker data from hungersolutions.org.
Run this first to find where the lat/lon data lives.
"""

import re
import json
import requests

BASE    = "https://www.hungersolutions.org"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ── 1. Check the page source for embedded JS marker data ──────────────────
print("=== Fetching page source ===")
resp = requests.get(f"{BASE}/find-help/", params={"fwp_categories": "food-shelves"},
                    headers=HEADERS, timeout=30)

# Look for JSON blobs that contain lat/lon
hits = re.findall(r'(\{[^{}]{0,500}"lat"[^{}]{0,500}\})', resp.text)
print(f"Found {len(hits)} lat/lon-looking blobs in page source")
for h in hits[:3]:
    print(" ", h[:200])

# Look for JS variable assignments that might hold marker arrays
vars_hit = re.findall(r'var\s+\w+\s*=\s*(\[.*?\]);', resp.text, re.DOTALL)
print(f"\nFound {len(vars_hit)} JS array assignments")

# ── 2. Try the WP REST API ────────────────────────────────────────────────
print("\n=== Trying WP REST API ===")
r = requests.get(f"{BASE}/wp-json/wp/v2/types", headers=HEADERS, timeout=15)
print(f"  /wp-json/wp/v2/types -> {r.status_code}")
if r.ok:
    print(" ", list(r.json().keys()))

# ── 3. Try FacetWP map-specific endpoints ────────────────────────────────
print("\n=== Trying FacetWP map endpoints ===")
candidates = [
    "/wp-admin/admin-ajax.php",  # standard WP ajax
    "/wp-json/facetwp/v1/map",
    "/wp-json/facetwp/v1/locations",
]
for path in candidates:
    r = requests.post(f"{BASE}{path}",
                      data={"action": "facetwp_map_marker_load",
                            "data[facets][categories][]": "food-shelves"},
                      headers=HEADERS, timeout=15)
    print(f"  POST {path} -> {r.status_code} | {r.text[:120]}")

# ── 4. Try the FacetWP refresh and look for coords in the response ────────
print("\n=== FacetWP refresh response (looking for coords) ===")
r = requests.post(f"{BASE}/find-help/",
                  data={"action": "facetwp_refresh",
                        "data[facets][categories][]": "food-shelves",
                        "data[pager][per_page]": 1},
                  headers=HEADERS, timeout=30)
if r.ok:
    blob = r.json()
    print("Top-level keys:", list(blob.keys()))
    # Print anything that looks like it has coordinates
    for k, v in blob.items():
        s = json.dumps(v)
        if "lat" in s.lower() or "lng" in s.lower() or "coord" in s.lower():
            print(f"  Key '{k}' contains coordinate-looking data:")
            print(" ", s[:400])