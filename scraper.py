"""
SCEIN Fellowship - Permits, Incentives & Regulations Scraper
============================================================
Run this script weekly to refresh your dataset.
It reads your Excel file, scrapes each URL, and saves a CSV for QGIS.

Usage:
    python scraper.py

Requirements:
    pip install pandas openpyxl requests beautifulsoup4 geopy lxml
"""


import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import json
import csv
import os
import time
import logging
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# ── Configuration ──────────────────────────────────────────────────────────────
EXCEL_FILE = "SCEIN_Fellowship_Data_Tracker_Google_Sheets.xlsx"   # Path to your Excel file
OUTPUT_CSV = "scraped_data.csv"                                    # Output for QGIS
LOG_FILE   = "scraper.log"                                         # Log file
DELAY_BETWEEN_REQUESTS = 2   # Seconds between requests (be polite to servers)
REQUEST_TIMEOUT        = 15  # Seconds before giving up on a URL
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Step 1: Extract records from Excel ────────────────────────────────────────
def extract_records_from_excel(filepath):
    log.info(f"Reading Excel file: {filepath}")
    xl = pd.read_excel(filepath, sheet_name=None)
    records = []

    for sheet_name in ["Permits", "Incentives", "Regulations"]:
        if sheet_name not in xl:
            continue
        df = xl[sheet_name]

        for i, row in df.iterrows():
            if i == 0:
                continue  # skip header row

            dataset_name  = str(row.iloc[6]).strip()  if pd.notna(row.iloc[6])  else ""
            description   = str(row.iloc[1]).strip()  if pd.notna(row.iloc[1])  else ""
            source_url    = str(row.iloc[9]).strip()  if pd.notna(row.iloc[9])  else ""
            data_age      = str(row.iloc[10]).strip() if pd.notna(row.iloc[10]) else ""
            data_region   = str(row.iloc[11]).strip() if pd.notna(row.iloc[11]) else ""
            data_type     = str(row.iloc[12]).strip() if pd.notna(row.iloc[12]) else ""
            parameter_type= str(row.iloc[18]).strip() if pd.notna(row.iloc[18]) else ""
            priority      = str(row.iloc[5]).strip()  if pd.notna(row.iloc[5])  else ""
            host_name     = str(row.iloc[7]).strip()  if pd.notna(row.iloc[7])  else ""
            access_type   = str(row.iloc[13]).strip() if pd.notna(row.iloc[13]) else ""

            # Find URL
            url = ""
            if source_url and "http" in source_url:
                url = source_url.strip()
            else:
                found = re.findall(r"https?://[^\s\|]+", dataset_name)
                if found:
                    url = found[0].strip()

            if not url or url in ["nan", "NaN"]:
                continue

            # Parse county and state from data_region
            county, state = "", "California"
            if data_region and data_region not in ["nan", "NaN"]:
                m = re.match(r"^(.+?)\s*,\s*", data_region)
                if m:
                    county = m.group(1).strip()
                s = re.search(r",\s*([A-Za-z\s]+),\s*USA", data_region)
                if s:
                    state = s.group(1).strip()

            records.append({
                "type"          : sheet_name.rstrip("s"),
                "parameter_type": parameter_type if parameter_type not in ["nan","NaN",""] else sheet_name.rstrip("s"),
                "dataset_name"  : dataset_name   if dataset_name   not in ["nan","NaN"]    else "",
                "description"   : description[:250] if description not in ["nan","NaN"]    else "",
                "county"        : county,
                "state"         : state,
                "data_region"   : data_region    if data_region    not in ["nan","NaN"]    else "",
                "source_url"    : url,
                "host_name"     : host_name      if host_name      not in ["nan","NaN"]    else "",
                "data_age"      : data_age       if data_age       not in ["nan","NaN","NOT_STATED"] else "",
                "data_type"     : data_type      if data_type      not in ["nan","NaN"]    else "",
                "access_type"   : access_type    if access_type    not in ["nan","NaN"]    else "",
                "priority"      : priority       if priority        not in ["nan","NaN"]   else "",
            })

    log.info(f"Extracted {len(records)} records from Excel.")
    return records


# ── Step 2: Scrape each URL ────────────────────────────────────────────────────
def scrape_url(url):
    """Scrape a URL and return extracted info."""
    result = {
        "page_title"       : "",
        "page_status"      : "",
        "page_live"        : False,
        "scraped_text"     : "",
        "dates_found"      : "",
        "fees_found"       : "",
        "contact_found"    : "",
        "last_scraped"     : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scrape_error"     : "",
    }

    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        result["page_status"] = str(resp.status_code)
        result["page_live"]   = resp.status_code == 200

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")

            # Title
            result["page_title"] = soup.title.string.strip() if soup.title else ""

            # Clean text
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = " ".join(soup.get_text().split())

            # Store first 500 chars of clean text
            result["scraped_text"] = text[:500]

            # Extract dates (various formats)
            date_patterns = [
                r"\b(January|February|March|April|May|June|July|August|"
                r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
                r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
                r"\b\d{4}-\d{2}-\d{2}\b",
                r"\b(Effective|Updated|Adopted|Expires?|Valid through|"
                r"Amended|Enacted|Revised)\s*:?\s*\S+",
            ]
            dates = []
            for p in date_patterns:
                dates.extend(re.findall(p, text, re.IGNORECASE))
            result["dates_found"] = " | ".join(str(d) for d in dates[:5])

            # Extract fee mentions
            fees = re.findall(r"\$[\d,]+(?:\.\d{2})?|\bfee[s]?\b[^.]{0,60}", text, re.IGNORECASE)
            result["fees_found"] = " | ".join(fees[:3])

            # Extract contact/phone
            phones = re.findall(r"\(?\d{3}\)?[\s\-\.]\d{3}[\s\-\.]\d{4}", text)
            result["contact_found"] = phones[0] if phones else ""

    except requests.exceptions.Timeout:
        result["scrape_error"] = "Timeout"
        result["page_status"]  = "Timeout"
    except requests.exceptions.ConnectionError as e:
        result["scrape_error"] = f"Connection error: {str(e)[:80]}"
        result["page_status"]  = "Connection Error"
    except Exception as e:
        result["scrape_error"] = str(e)[:120]
        result["page_status"]  = "Error"

    return result


# ── Step 3: Geocode county names ───────────────────────────────────────────────
def build_geocoder():
    geolocator = Nominatim(user_agent="scein_fellowship_scraper_v1")
    return RateLimiter(geolocator.geocode, min_delay_seconds=1)

GEOCODE_CACHE = {}

def geocode_region(geocode, county, state):
    """Return (latitude, longitude) for a county+state."""
    key = f"{county}, {state}"
    if key in GEOCODE_CACHE:
        return GEOCODE_CACHE[key]
    if not county:
        GEOCODE_CACHE[key] = ("", "")
        return ("", "")
    try:
        location = geocode(f"{key}, USA")
        if location:
            coords = (round(location.latitude, 6), round(location.longitude, 6))
        else:
            coords = ("", "")
    except Exception:
        coords = ("", "")
    GEOCODE_CACHE[key] = coords
    return coords


# ── Step 4: Main pipeline ──────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("SCEIN Scraper started")
    log.info(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    # Check Excel file
    if not os.path.exists(EXCEL_FILE):
        log.error(f"Excel file not found: {EXCEL_FILE}")
        log.error("Make sure the Excel file is in the same folder as this script.")
        return

    records   = extract_records_from_excel(EXCEL_FILE)
    geocode   = build_geocoder()
    results   = []
    total     = len(records)

    for idx, record in enumerate(records, 1):
        url = record["source_url"]
        log.info(f"[{idx}/{total}] Scraping: {url}")

        scraped = scrape_url(url)
        time.sleep(DELAY_BETWEEN_REQUESTS)

        # Geocode
        lat, lon = geocode_region(geocode, record["county"], record["state"])

        row = {
            # Identity
            "id"              : idx,
            "type"            : record["type"],
            "parameter_type"  : record["parameter_type"],
            "dataset_name"    : record["dataset_name"],
            # Location
            "county"          : record["county"],
            "state"           : record["state"],
            "data_region"     : record["data_region"],
            "latitude"        : lat,
            "longitude"       : lon,
            # Source
            "source_url"      : url,
            "host_name"       : record["host_name"],
            "priority"        : record["priority"],
            "access_type"     : record["access_type"],
            "data_type"       : record["data_type"],
            "data_age"        : record["data_age"],
            "description"     : record["description"],
            # Scraped
            "page_title"      : scraped["page_title"],
            "page_status"     : scraped["page_status"],
            "page_live"       : scraped["page_live"],
            "scraped_text"    : scraped["scraped_text"],
            "dates_found"     : scraped["dates_found"],
            "fees_found"      : scraped["fees_found"],
            "contact_found"   : scraped["contact_found"],
            "last_scraped"    : scraped["last_scraped"],
            "scrape_error"    : scraped["scrape_error"],
        }
        results.append(row)

    # Write CSV
    if results:
        fieldnames = list(results[0].keys())
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        live_count  = sum(1 for r in results if r["page_live"])
        error_count = sum(1 for r in results if r["scrape_error"])
        log.info("=" * 60)
        log.info(f"Done! {len(results)} records saved to {OUTPUT_CSV}")
        log.info(f"  Live pages   : {live_count}")
        log.info(f"  Errors       : {error_count}")
        log.info(f"  Output file  : {os.path.abspath(OUTPUT_CSV)}")
        log.info("Load this CSV into QGIS as a Delimited Text Layer.")
        log.info("=" * 60)
    else:
        log.warning("No records found. Check your Excel file path.")


if __name__ == "__main__":
    main()
