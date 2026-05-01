"""
Enrich food_shelves.csv with county data via the US Census Geocoder batch API.

Steps:
  1. Load food_shelves.csv into a DataFrame
  2. Strip "( miles away)" variants from the 'name' column
  3. Parse street / city / state / zip from messy addresses (see parse_address)
  4. Submit to Census batch geocoder in chunks of 1000
  5. Resolve county FIPS -> county name via Census reference file
  6. Save result as food_shelves_enriched.pkl

Requirements:
    pip install pandas requests

Usage:
    python enrich_food_shelves.py
"""

import io
import re
import csv
import time
import requests
import pandas as pd

INPUT_CSV = "data/mn_food_shelf_list.csv"
OUTPUT_PKL = "data/clean_food_shelf_list.pkl"

CENSUS_BATCH_URL = "https://geocoding.geo.census.gov/geocoder/geographies/addressbatch"
CENSUS_PARAMS = {
    "benchmark": "Public_AR_Current",
    "vintage": "Current_Current",
}

# ── Name cleaning ─────────────────────────────────────────────────────────────

MILES_RE = re.compile(r"\(\s*[\d.,]*\s*miles?\s*away\s*\)", re.IGNORECASE)


def clean_names(series: pd.Series) -> pd.Series:
    return series.str.replace(MILES_RE, "", regex=True).str.strip()


# ── Address parsing ───────────────────────────────────────────────────────────

# Expanded to include full state names
US_STATES = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "DC",
    "PR",
    "GU",
    "VI",
    "AS",
    "MP",
}

STATE_NAME_MAP = {
    "ALABAMA": "AL",
    "ALASKA": "AK",
    "ARIZONA": "AZ",
    "ARKANSAS": "AR",
    "CALIFORNIA": "CA",
    "COLORADO": "CO",
    "CONNECTICUT": "CT",
    "DELAWARE": "DE",
    "FLORIDA": "FL",
    "GEORGIA": "GA",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "ILLINOIS": "IL",
    "INDIANA": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KENTUCKY": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI",
    "MINNESOTA": "MN",
    "MISSISSIPPI": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "NEBRASKA": "NE",
    "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OREGON": "OR",
    "PENNSYLVANIA": "PA",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN",
    "TEXAS": "TX",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI",
    "WYOMING": "WY",
}

ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")
STATE_ZIP_RE = re.compile(r"^([A-Z]{2})(?:\s+(\d{5}(?:-\d{4})?))?$")


def parse_address(raw: str) -> dict:
    if not isinstance(raw, str) or raw.strip().lower() == "nan":
        return {"street": "", "city": "", "state": "", "zipcode": ""}

    addr = raw.strip().strip('"').strip("'")
    addr = re.sub(
        r",?\s*(USA|United States)\s*$", "", addr, flags=re.IGNORECASE
    ).strip()

    parts = [p.strip() for p in addr.split(",")]

    # Normalize any full state name to its abbreviation
    normalized = []
    for p in parts:
        upper = p.strip().upper()
        if upper in STATE_NAME_MAP:
            normalized.append(STATE_NAME_MAP[upper])
        else:
            normalized.append(p)
    parts = normalized

    # Scan right-to-left for the state anchor
    state_idx = None
    state = ""
    zipcode = ""

    for i in range(len(parts) - 1, -1, -1):
        p = parts[i].strip()

        # Case 1: "MN 55401" — state and zip together
        m = STATE_ZIP_RE.match(p)
        if m and m.group(1) in US_STATES:
            state_idx = i
            state = m.group(1)
            zipcode = m.group(2) or ""
            # Case 2: "MN, 56339" — zip landed in the NEXT part to the right
            if not zipcode and i + 1 < len(parts):
                next_p = parts[i + 1].strip()
                if ZIP_RE.match(next_p):
                    zipcode = next_p
            break

        # Case 3: bare zip landed before state in scan — skip it, keep looking
        if ZIP_RE.match(p):
            continue

    if state_idx is None:
        return {"street": addr, "city": "", "state": "", "zipcode": ""}

    city_idx = state_idx - 1

    # Skip over any stray ZIP-only part just left of state (the "MN, 56339" case)
    if city_idx >= 0 and ZIP_RE.match(parts[city_idx].strip()):
        city_idx -= 1

    city = parts[city_idx] if city_idx >= 0 else ""
    street = ", ".join(parts[:city_idx]) if city_idx > 0 else ""

    # If street is empty (missing comma between street and city), the
    # city field holds "123 Main St Townname" — send it all as street
    # and leave city blank. Census handles this better than an empty street.
    if not street and city:
        street = city
        city = ""

    return {"street": street, "city": city, "state": state, "zipcode": zipcode}


# ── Census batch geocoder ─────────────────────────────────────────────────────

GEOCODE_COLUMNS = [
    "id",
    "input_address",
    "match",
    "match_type",
    "matched_address",
    "coords",
    "tiger_line_id",
    "tiger_side",
    "state_fips",
    "county_fips",
    "tract",
    "block",
]


def geocode_batch(df_chunk: pd.DataFrame) -> pd.DataFrame:
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\n")

    for idx, row in df_chunk.iterrows():
        writer.writerow(
            [
                idx,
                str(row["street"] if pd.notna(row["street"]) else "").replace(",", " "),
                str(row["city"] if pd.notna(row["city"]) else "").replace(",", " "),
                str(row["state"] if pd.notna(row["state"]) else ""),
                str(row["zipcode"] if pd.notna(row["zipcode"]) else ""),
            ]
        )

    # Debug: print first 3 lines so you can see exactly what's being sent
    sample_lines = buf.getvalue().splitlines()[:3]
    print(f"    Sample CSV rows being sent:")
    for line in sample_lines:
        print(f"      {line}")

    payload = buf.getvalue().encode("utf-8")

    print(f"    Sending {len(df_chunk)} addresses to Census geocoder...")
    resp = requests.post(
        CENSUS_BATCH_URL,
        params=CENSUS_PARAMS,
        files={"addressFile": ("addresses.csv", payload, "text/plain")},
        timeout=180,
    )

    if not resp.ok:
        print(f"    HTTP {resp.status_code}: {resp.text[:500]}")
        resp.raise_for_status()

    result = pd.read_csv(
        io.StringIO(resp.text),
        header=None,
        names=GEOCODE_COLUMNS,
        dtype=str,
        on_bad_lines="skip",
    )
    result["id"] = pd.to_numeric(result["id"], errors="coerce").astype("Int64")
    return result


# ── County name lookup ────────────────────────────────────────────────────────


def fetch_county_names() -> dict:
    """
    Download the Census national county reference file and return a dict:
        (state_fips_2digit, county_fips_3digit) -> county_name
    """
    url = "https://www2.census.gov/geo/docs/reference/codes2020/national_county2020.txt"
    print("  Fetching county name reference file from Census...")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    ref = pd.read_csv(
        io.StringIO(resp.text),
        sep="|",
        dtype=str,
        encoding="latin-1",
    )
    ref.columns = [c.strip() for c in ref.columns]

    sf_col = next(c for c in ref.columns if "STATEFP" in c.upper())
    cf_col = next(c for c in ref.columns if "COUNTYFP" in c.upper())
    nm_col = next(c for c in ref.columns if "NAME" in c.upper())

    mapping = {
        (str(row[sf_col]).zfill(2), str(row[cf_col]).zfill(3)): row[nm_col]
        for _, row in ref.iterrows()
    }
    print(f"  Loaded {len(mapping)} county entries.")
    return mapping


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    # 1. Load CSV
    print(f"Loading {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV, dtype=str)
    print(f"  {len(df)} rows. Columns: {list(df.columns)}")

    # 2. Clean names
    print("Cleaning 'name' column...")
    df["name"] = clean_names(df["name"])

    # 3. Parse address components
    print("Parsing address components...")
    parsed = df["address"].apply(parse_address).apply(pd.Series)
    df = pd.concat([df, parsed], axis=1)

    print("  Sample parsed addresses:")
    print(
        df[["address", "street", "city", "state", "zipcode"]]
        .head(10)
        .to_string(index=False)
    )

    missing_state = (df["state"] == "").sum()
    missing_zip = (df["zipcode"] == "").sum()
    print(f"  Rows with no state parsed: {missing_state}")
    print(
        f"  Rows with no ZIP parsed:   {missing_zip} (OK — Census can match without ZIP)"
    )

    # 4. Geocode in chunks of 1000
    CHUNK_SIZE = 1000
    chunks = [df.iloc[i : i + CHUNK_SIZE] for i in range(0, len(df), CHUNK_SIZE)]
    print(f"\nGeocoding {len(df)} addresses in {len(chunks)} batch(es)...")

    all_geo = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  Batch {i}/{len(chunks)} ({len(chunk)} rows)...")
        try:
            geo = geocode_batch(chunk)
            all_geo.append(geo)
            print(f"    Got {len(geo)} result rows back.")
        except Exception as e:
            print(f"    ERROR: {e}")
        if i < len(chunks):
            time.sleep(2)

    if not all_geo:
        raise RuntimeError(
            "All geocoding batches failed — check your internet connection and Census API status."
        )

    geo_df = pd.concat(all_geo, ignore_index=True)

    # 5. Merge results back
    df.index.name = "id"
    df = df.reset_index()
    df["id"] = df["id"].astype("Int64")

    df = df.merge(
        geo_df[
            ["id", "matched_address", "coords", "state_fips", "county_fips", "match"]
        ],
        on="id",
        how="left",
    )

    # 6. Resolve FIPS -> county name
    county_map = fetch_county_names()

    def resolve_county(row):
        sf = row.get("state_fips")
        cf = row.get("county_fips")
        if pd.isna(sf) or pd.isna(cf):
            return None
        sf = str(sf).zfill(2)
        cf = str(cf).zfill(3)
        return county_map.get((sf, cf), f"FIPS:{sf}{cf}")

    df["county"] = df.apply(resolve_county, axis=1)

    # 7. Summary
    match_upper = df["match"].str.upper()
    matched = (match_upper == "MATCH").sum()
    tie = (match_upper == "TIE").sum()
    no_match = df["match"].isna().sum() + (match_upper == "NO MATCH").sum()
    print(f"\nGeocoding summary ({len(df)} total):")
    print(f"  Match:    {matched}")
    print(f"  Tie:      {tie}  (first candidate used)")
    print(f"  No match: {no_match}  (county = NaN)")
    print(f"  County assigned: {df['county'].notna().sum()}")

    # Flag any no-match rows so they're easy to inspect / fix manually
    no_match_df = df[df["match"].str.upper().isin(["NO MATCH"]) | df["match"].isna()]
    if len(no_match_df):
        print(f"\n  Unmatched addresses:")
        print(
            no_match_df[
                ["name", "address", "street", "city", "state", "zipcode"]
            ].to_string(index=False)
        )

    # 8. Final column order
    keep = [
        "name",
        "address",
        "street",
        "city",
        "state",
        "zipcode",
        "county",
        "matched_address",
        "coords",
        "state_fips",
        "county_fips",
        "match",
    ]
    df = df[[c for c in keep if c in df.columns]]

    # 9. Save
    print(f"\nSaving to {OUTPUT_PKL}...")
    df.to_pickle(OUTPUT_PKL)
    print("Done.\n")
    print(df[["name", "address", "county"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
