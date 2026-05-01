"""
Diagnostic: dump the raw JSON/HTML context around the first few lat/lng
markers in the page source so we can see what fields surround them.

Run this and paste the output so we can write the real scraper.
"""

import re
import json
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.hungersolutions.org/find-help/"
HEADERS  = {"User-Agent": "Mozilla/5.0"}

resp = requests.get(BASE_URL, params={"fwp_categories": "food-shelves"}, headers=HEADERS, timeout=30)
html = resp.text

print(f"Page fetched: {len(html)} chars\n")

# ── 1. Show ALL script tag content that contains lat ─────────────────────────
print("=" * 60)
print("SCRIPT TAGS CONTAINING 'lat'")
print("=" * 60)
soup = BeautifulSoup(html, "html.parser")
for i, script in enumerate(soup.find_all("script")):
    text = script.string or ""
    if '"lat"' in text or "'lat'" in text:
        print(f"\n--- Script tag #{i} (first 2000 chars) ---")
        print(text[:2000])

# ── 2. Show 500 chars before+after the first 3 lat/lng matches in raw HTML ───
print("\n" + "=" * 60)
print("RAW CONTEXT AROUND FIRST 3 lat/lng OCCURRENCES")
print("=" * 60)
for i, m in enumerate(re.finditer(r'"lat"\s*:', html)):
    if i >= 3:
        break
    start = max(0, m.start() - 500)
    end   = min(len(html), m.start() + 500)
    print(f"\n--- Match {i+1} (chars {start}–{end}) ---")
    print(html[start:end])

# ── 3. Try to parse the surrounding object for each lat match ────────────────
print("\n" + "=" * 60)
print("ATTEMPTING TO PARSE FULL JSON OBJECTS AROUND lat MATCHES")
print("=" * 60)
for i, m in enumerate(re.finditer(r'"lat"\s*:', html)):
    if i >= 5:
        break
    # Walk back to find the opening brace of this object
    start = html.rfind("{", 0, m.start())
    if start == -1:
        continue
    # Try expanding the window to find matching close brace
    for end_offset in [200, 500, 1000, 2000]:
        snippet = html[start:start + end_offset]
        try:
            obj = json.loads(snippet[:snippet.rfind("}") + 1])
            print(f"\n--- Object {i+1} keys: {list(obj.keys())} ---")
            print(json.dumps(obj, indent=2)[:600])
            break
        except Exception:
            pass
    else:
        print(f"\n--- Object {i+1}: could not parse, raw snippet ---")
        print(html[start:start + 300])

# ── 4. Look for the listing card HTML structure ───────────────────────────────
print("\n" + "=" * 60)
print("LISTING CARD HTML STRUCTURE (first 2 cards)")
print("=" * 60)
# Common FacetWP result selectors
for selector in [".fwp-result", ".facetwp-template > *", ".location", 
                 ".card", "[class*='result']", "[class*='location']", 
                 "[class*='listing']", "article"]:
    cards = soup.select(selector)
    if cards:
        print(f"\nSelector '{selector}' found {len(cards)} elements")
        print("First card HTML:")
        print(str(cards[0])[:800])
        print("\nSecond card HTML:")
        print(str(cards[1])[:800] if len(cards) > 1 else "(only 1 found)")
        break