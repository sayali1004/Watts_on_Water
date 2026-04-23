
"""
Export Supabase permits/incentives/regulations data for QGIS
One row per item (permit/incentive/regulation) — no county aggregation.
Join with tl_2025_us_county.shp using NAME + STATEFP fields.
"""

import os
import re
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

STATE_ABBR_TO_FIPS = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06',
    'CO': '08', 'CT': '09', 'DE': '10', 'DC': '11', 'FL': '12',
    'GA': '13', 'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18',
    'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23',
    'MD': '24', 'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28',
    'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33',
    'NJ': '34', 'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38',
    'OH': '39', 'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44',
    'SC': '45', 'SD': '46', 'TN': '47', 'TX': '48', 'UT': '49',
    'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55',
    'WY': '56', 'PR': '72', 'US': '00'
}

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


def extract_county(param_name):
    if not param_name:
        return None
    match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+County', str(param_name))
    return match.group(1) if match else None


def extract_state(param_name, description=None):
    text = ' '.join(filter(None, [str(param_name or ''), str(description or '')]))
    state_patterns = {
        'CA': ['California', ' CA ', ', CA'],
        'AL': ['Alabama', ' AL '], 'AK': ['Alaska', ' AK '],
        'AZ': ['Arizona', ' AZ '], 'AR': ['Arkansas', ' AR '],
        'CO': ['Colorado', ' CO '], 'CT': ['Connecticut', ' CT '],
        'FL': ['Florida', ' FL '], 'GA': ['Georgia', ' GA '],
        'TX': ['Texas', ' TX '], 'NY': ['New York', ' NY '],
        'NC': ['North Carolina', ' NC '], 'SC': ['South Carolina', ' SC '],
        'VA': ['Virginia', ' VA '], 'WA': ['Washington', ' WA '],
        'OR': ['Oregon', ' OR '], 'PA': ['Pennsylvania', ' PA '],
        'OH': ['Ohio', ' OH '], 'MI': ['Michigan', ' MI '],
    }
    for code, patterns in state_patterns.items():
        if any(p in text for p in patterns):
            return code
    return None


def get_scope(param_name, description=None):
    text = ' '.join(filter(None, [str(param_name or ''), str(description or '')]))
    federal_keywords = ['US-Federal', 'Federal', 'United States', 'National', 'IRS', 'Department of Energy']
    if any(kw in text for kw in federal_keywords):
        return 'federal'
    county = extract_county(param_name)
    state = extract_state(param_name, description)
    if county and state:
        return 'county'
    if state:
        return 'state'
    return 'unknown'


def fetch_all_data():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Fetching data from Supabase...")
    response = supabase.table('permits_data').select('*').execute()
    print(f"Fetched {len(response.data)} records")
    return response.data


def export_to_csv(data, output_file='county_permits_for_qgis.csv'):
    rows = []

    for record in data:
        param_name = record.get('parameter_name')
        description = record.get('description')

        county = record.get('county') or extract_county(param_name)
        state = record.get('state') or extract_state(param_name, description)
        scope = get_scope(param_name, description)
        state_fips = STATE_ABBR_TO_FIPS.get(state, '') if state else ''

        def val(key):
            v = record.get(key)
            return '' if v is None else v

        rows.append({
            # -- QGIS join fields --
            'NAME': county or '',       # matches shapefile NAME column
            'STATEFP': state_fips,      # matches shapefile STATEFP column
            'STATE_ABBR': state or '',
            'SCOPE': scope,             # county / state / federal / unknown

            # -- Requested output columns --
            'CATEGORY': val('data_type'),               # Permit / Incentive / Regulation
            'OWNER_CLASS': val('owner_class'),           # Federal / State / Local
            'ITEM_TYPE': val('item_type'),               # e.g. Solar, Net Metering, Grant Program
            'TYPE_II': val('type_ii'),                   # Water / Solar (once column added to Excel)
            'DATASET_NAME': val('parameter_name'),       # Dataset Name (col 5)
            'SOURCE_ACCREDITATION': val('source_accreditation'),
            'URL': val('url'),
            'DATA_AGE': val('data_age'),
            'DESCRIPTION': val('description'),
            'APPLICABLE_SYSTEM_TYPES': val('applicable_system_types'),
            'MIN_SYSTEM_SIZE_MW': val('min_system_size_mw'),
            'MAX_SYSTEM_SIZE_MW': val('max_system_size_mw'),
            'COST': val('cost'),

            # -- Scraped fields --
            'STATUS': val('status'),
            'EFFECTIVE_DATE': val('effective_date'),
            'EXPIRY_DATE': val('expiry_date'),
            'TIMEFRAME_DAYS': val('timeframe_days'),
        })

    df = pd.DataFrame(rows)
    df = df.sort_values(['STATEFP', 'NAME', 'DATA_TYPE'])
    df.to_csv(output_file, index=False)

    print(f"\n✅ Exported {len(df)} rows to {output_file}")
    print(f"\nBreakdown by type:")
    print(df['DATA_TYPE'].value_counts().to_string())
    print(f"\nBreakdown by scope:")
    print(df['SCOPE'].value_counts().to_string())

    return output_file


def main():
    print("=" * 60)
    print("QGIS Data Export — one row per permit/incentive/regulation")
    print("=" * 60)

    data = fetch_all_data()
    if not data:
        print("No data fetched from Supabase.")
        return

    csv_file = export_to_csv(data)

    print("\n" + "=" * 60)
    print("Next steps in QGIS:")
    print("  1. Load shapefile: tl_2025_us_county.shp")
    print("  2. Load CSV:", csv_file)
    print("  3. Join on NAME + STATEFP (one-to-many relation)")
    print("  4. Filter by DATA_TYPE or SCOPE as needed")
    print("=" * 60)


if __name__ == '__main__':
    main()
