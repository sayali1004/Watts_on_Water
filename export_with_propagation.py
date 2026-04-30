"""
Pre-compute propagated QGIS exports — fast, no live SQL joins in QGIS.

Outputs:
  choropleth.csv    — one row per county, with counts (for choropleth map)
  detail_propagated.csv — one row per county-item (for click-to-explore)
"""

import os
import pandas as pd
import geopandas as gpd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

STATE_FIPS_TO_ABBR = {
    '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA',
    '08': 'CO', '09': 'CT', '10': 'DE', '11': 'DC', '12': 'FL',
    '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL', '18': 'IN',
    '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME',
    '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS',
    '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH',
    '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND',
    '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI',
    '45': 'SC', '46': 'SD', '47': 'TN', '48': 'TX', '49': 'UT',
    '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV', '55': 'WI',
    '56': 'WY', '72': 'PR'
}

ITEM_COLS = [
    'CATEGORY', 'OWNER_CLASS', 'ITEM_TYPE', 'DATASET_NAME',
    'SOURCE_ACCREDITATION', 'URL', 'DATA_AGE', 'DESCRIPTION',
    'APPLICABLE_SYSTEM_TYPES', 'MIN_SYSTEM_SIZE_MW', 'MAX_SYSTEM_SIZE_MW',
    'COST', 'STATUS', 'SCOPE', 'STATE_ABBR'
]


def fetch_csv():
    df = pd.read_csv('county_permits_for_qgis.csv', dtype=str)
    df.columns = [c.upper() for c in df.columns]
    return df


def load_counties(shapefile='tl_2025_us_county.shp'):
    gdf = gpd.read_file(shapefile)[['NAME', 'STATEFP', 'GEOID']]
    return gdf


def propagate(items_df, counties_df):
    """Return detail rows: one row per county × applicable item."""
    county_items = items_df[items_df['SCOPE'] == 'county'].copy()
    state_items  = items_df[items_df['SCOPE'] == 'state'].copy()
    federal_items = items_df[items_df['SCOPE'] == 'federal'].copy()
    unknown_items = items_df[items_df['SCOPE'] == 'unknown'].copy()

    detail_rows = []

    # County-specific: exact NAME + STATEFP match
    merged_county = counties_df.merge(
        county_items[ITEM_COLS + ['NAME', 'STATEFP']],
        on=['NAME', 'STATEFP'], how='inner'
    )
    detail_rows.append(merged_county[['NAME', 'STATEFP', 'GEOID'] + ITEM_COLS])

    # State-level: match on STATEFP only
    state_items_fips = state_items.copy()
    state_items_fips['STATEFP'] = state_items_fips['STATEFP'].map(
        lambda x: x if len(str(x)) == 2 else None
    )
    # Use STATE_ABBR to get STATEFP
    abbr_to_fips = {v: k for k, v in STATE_FIPS_TO_ABBR.items()}
    state_items_fips['STATEFP'] = state_items_fips['STATE_ABBR'].map(abbr_to_fips)
    state_items_fips = state_items_fips.dropna(subset=['STATEFP'])
    merged_state = counties_df[['NAME', 'STATEFP', 'GEOID']].merge(
        state_items_fips[ITEM_COLS + ['STATEFP']],
        on='STATEFP', how='inner'
    )
    detail_rows.append(merged_state[['NAME', 'STATEFP', 'GEOID'] + ITEM_COLS])

    # Federal: applies to every county
    if not federal_items.empty:
        federal_items['_key'] = 1
        all_counties = counties_df[['NAME', 'STATEFP', 'GEOID']].copy()
        all_counties['_key'] = 1
        merged_federal = all_counties.merge(federal_items[ITEM_COLS + ['_key']], on='_key').drop(columns='_key')
        detail_rows.append(merged_federal[['NAME', 'STATEFP', 'GEOID'] + ITEM_COLS])

    # Unknown scope: include as-is (no county assignment)
    if not unknown_items.empty:
        unk = unknown_items[ITEM_COLS].copy()
        unk['NAME'] = ''
        unk['STATEFP'] = ''
        unk['GEOID'] = ''
        detail_rows.append(unk[['NAME', 'STATEFP', 'GEOID'] + ITEM_COLS])

    return pd.concat(detail_rows, ignore_index=True)


def build_choropleth(detail_df, counties_df):
    """Aggregate counts per county from the detail rows."""
    county_detail = detail_df[detail_df['NAME'] != '']
    counts = county_detail.groupby(['NAME', 'STATEFP', 'GEOID']).agg(
        total_count=('URL', 'count'),
        permit_count=('CATEGORY', lambda x: (x == 'permit').sum()),
        incentive_count=('CATEGORY', lambda x: (x == 'incentive').sum()),
        regulation_count=('CATEGORY', lambda x: (x == 'regulation').sum()),
    ).reset_index()

    # Left join to include counties with 0 items
    choropleth = counties_df[['NAME', 'STATEFP', 'GEOID']].merge(
        counts, on=['NAME', 'STATEFP', 'GEOID'], how='left'
    ).fillna(0)
    for col in ['total_count', 'permit_count', 'incentive_count', 'regulation_count']:
        choropleth[col] = choropleth[col].astype(int)

    return choropleth.sort_values(['STATEFP', 'NAME'])


def main():
    import sys
    shapefile = sys.argv[1] if len(sys.argv) > 1 else 'tl_2025_us_county.shp'

    print("Loading county permits CSV...")
    items_df = fetch_csv()
    print(f"  {len(items_df)} items")

    print("Loading shapefile counties...")
    counties_df = load_counties(shapefile)
    print(f"  {len(counties_df)} counties")

    print("Propagating federal/state/county items...")
    detail_df = propagate(items_df, counties_df)
    detail_df.to_csv('detail_propagated.csv', index=False)
    print(f"  detail_propagated.csv → {len(detail_df)} rows")

    print("\n✅ Done. Load detail_propagated.csv in QGIS:")
    print("   1. Add shapefile + detail_propagated.csv (no geometry)")
    print("   2. Project → Properties → Relations → link on NAME + STATEFP")
    print("   3. Click any county to see all applicable items")


if __name__ == '__main__':
    main()
