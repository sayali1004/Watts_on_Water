"""
SMART Export for QGIS - Distributes state/federal data to all counties
- County-specific data → only that county
- State-level data → ALL counties in that state  
- Federal data → ALL counties in ALL states
"""

import os
import re
import pandas as pd
import geopandas as gpd
from supabase import create_client
from collections import defaultdict

# Import county lookup
try:
    from county_state_lookup import COUNTY_TO_STATE_FIPS
except ImportError:
    COUNTY_TO_STATE_FIPS = {}

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

STATE_ABBR_TO_FIPS = {v: k for k, v in STATE_FIPS_TO_ABBR.items()}

# Credentials from environment variables
# Credentials

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://kvgvutzrlmstberrsyzv.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2Z3Z1dHpybG1zdGJlcnJzeXp2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTYxMjY1NCwiZXhwIjoyMDkxMTg4NjU0fQ.lI_9aYyO96nEuqprEOXUf_RB0zeTE5RartbgR-G4oNQ')

def download_shapefile_if_missing():
    """Download US county shapefile from Census if not present"""
    shapefile_path = 'tl_2025_us_county.shp'
    
    # Check if shapefile already exists
    if os.path.exists(shapefile_path):
        print(f"✅ Using existing shapefile: {shapefile_path}")
        return shapefile_path
    
    # Download if missing
    print("📥 Shapefile not found. Downloading from US Census...")
    import zipfile
    import urllib.request
    
    url = "https://www2.census.gov/geo/tiger/TIGER2025/COUNTY/tl_2025_us_county.zip"
    zip_path = "tl_2025_us_county.zip"
    
    try:
        # Download
        print(f"   Downloading from {url}")
        urllib.request.urlretrieve(url, zip_path)
        
        # Extract
        print(f"   Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall('.')
        
        # Clean up zip
        os.remove(zip_path)
        
        print(f"✅ Shapefile downloaded successfully")
        return shapefile_path
        
    except Exception as e:
        print(f"❌ Error downloading shapefile: {e}")
        raise

def find_shapefile():
    """Find or download the shapefile"""
    return download_shapefile_if_missing()

def load_all_counties_from_shapefile(shapefile_path):
    """Load all US counties from shapefile"""
    print(f"Loading counties from shapefile: {shapefile_path}")
    gdf = gpd.read_file(shapefile_path)
    
    counties = []
    for idx, row in gdf.iterrows():
        counties.append({
            'name': row['NAME'],
            'state_fips': row['STATEFP'],
            'state_abbr': STATE_FIPS_TO_ABBR.get(row['STATEFP'], row['STATEFP'])
        })
    
    print(f"✅ Loaded {len(counties)} counties from {len(gdf['STATEFP'].unique())} states")
    return counties

def extract_county_and_state(parameter_name, description=None):
    """Extract county and state, return scope (county/state/federal)"""
    if not parameter_name:
        return None, None, None, 'unknown'
    
    text = str(parameter_name)
    if description:
        text += " " + str(description)
    
    # Check for federal indicators
    federal_keywords = ['US-Federal', 'Federal', 'United States', 'National', 'IRS', 'Department of Energy']
    if any(kw in text for kw in federal_keywords):
        return None, None, None, 'federal'
    
    # Extract county name
    county_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+County', text)
    county_name = county_match.group(1) if county_match else None
    
    # Extract state
    state_abbr = None
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
    
    for state, patterns in state_patterns.items():
        if any(p in text for p in patterns):
            state_abbr = state
            break
    
    # Determine scope
    if county_name and state_abbr:
        return county_name, state_abbr, STATE_ABBR_TO_FIPS.get(state_abbr), 'county'
    elif state_abbr:
        return None, state_abbr, STATE_ABBR_TO_FIPS.get(state_abbr), 'state'
    else:
        return None, None, None, 'unknown'

def fetch_all_data():
    """Fetch all records from Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("Fetching data from Supabase...")
    response = supabase.table('permits_data').select('*').execute()
    
    print(f"Fetched {len(response.data)} records\n")
    return response.data

def categorize_data(data):
    """Categorize data by scope: county, state, or federal"""
    county_data = []
    state_data = defaultdict(list)
    federal_data = []
    unknown_data = []
    
    for record in data:
        county, state, state_fips, scope = extract_county_and_state(
            record.get('parameter_name'),
            record.get('description')
        )
        
        record_info = {
            'parameter_name': record.get('parameter_name'),
            'url': record.get('url'),
            'data_type': record.get('data_type'),
            'description': record.get('description'),
            'county': county,
            'state': state,
            'state_fips': state_fips
        }
        
        if scope == 'county':
            county_data.append(record_info)
        elif scope == 'state':
            state_data[state_fips].append(record_info)
        elif scope == 'federal':
            federal_data.append(record_info)
        else:
            unknown_data.append(record_info)
    
    print(f"📊 Data categorization:")
    print(f"   County-specific: {len(county_data)}")
    print(f"   State-level: {len([item for items in state_data.values() for item in items])} across {len(state_data)} states")
    print(f"   Federal: {len(federal_data)}")
    print(f"   Unknown: {len(unknown_data)}")
    
    return county_data, state_data, federal_data, unknown_data

def aggregate_for_counties(all_counties, county_data, state_data, federal_data):
    """Create records for each county with applicable data"""
    
    result = {}
    
    for county_info in all_counties:
        county_name = county_info['name']
        state_fips = county_info['state_fips']
        state_abbr = county_info['state_abbr']
        
        key = f"{county_name}_{state_abbr}"
        
        result[key] = {
            'county': county_name,
            'state': state_abbr,
            'state_fips': state_fips,
            'permits': [],
            'incentives': [],
            'regulations': [],
            'permit_urls': [],
            'incentive_urls': [],
            'regulation_urls': [],
            'permit_count': 0,
            'incentive_count': 0,
            'regulation_count': 0
        }
        
        # Add county-specific data
        for record in county_data:
            if record['county'] == county_name and record['state_fips'] == state_fips:
                data_type = record['data_type']
                if data_type == 'permit':
                    result[key]['permits'].append(record['parameter_name'])
                    result[key]['permit_urls'].append(record.get('url', ''))
                    result[key]['permit_count'] += 1
                elif data_type == 'incentive':
                    result[key]['incentives'].append(record['parameter_name'])
                    result[key]['incentive_urls'].append(record.get('url', ''))
                    result[key]['incentive_count'] += 1
                elif data_type == 'regulation':
                    result[key]['regulations'].append(record['parameter_name'])
                    result[key]['regulation_urls'].append(record.get('url', ''))
                    result[key]['regulation_count'] += 1
        
        # Add state-level data
        for record in state_data.get(state_fips, []):
            data_type = record['data_type']
            name = record['parameter_name'] + " (State-level)"
            if data_type == 'permit':
                result[key]['permits'].append(name)
                result[key]['permit_urls'].append(record.get('url', ''))
                result[key]['permit_count'] += 1
            elif data_type == 'incentive':
                result[key]['incentives'].append(name)
                result[key]['incentive_urls'].append(record.get('url', ''))
                result[key]['incentive_count'] += 1
            elif data_type == 'regulation':
                result[key]['regulations'].append(name)
                result[key]['regulation_urls'].append(record.get('url', ''))
                result[key]['regulation_count'] += 1
        
        # Add federal data
        for record in federal_data:
            data_type = record['data_type']
            name = record['parameter_name'] + " (Federal)"
            if data_type == 'permit':
                result[key]['permits'].append(name)
                result[key]['permit_urls'].append(record.get('url', ''))
                result[key]['permit_count'] += 1
            elif data_type == 'incentive':
                result[key]['incentives'].append(name)
                result[key]['incentive_urls'].append(record.get('url', ''))
                result[key]['incentive_count'] += 1
            elif data_type == 'regulation':
                result[key]['regulations'].append(name)
                result[key]['regulation_urls'].append(record.get('url', ''))
                result[key]['regulation_count'] += 1
    
    return result

def export_to_csv(county_data, output_file='county_permits_for_qgis.csv'):
    """Export to CSV"""
    
    rows = []
    for key, data in county_data.items():
        # Only include counties with data
        if data['permit_count'] + data['incentive_count'] + data['regulation_count'] == 0:
            continue
        
        permit_list = '; '.join(data['permits'][:5])
        if data['permit_count'] > 5:
            permit_list += f" (+{data['permit_count'] - 5} more)"
        
        incentive_list = '; '.join(data['incentives'][:5])
        if data['incentive_count'] > 5:
            incentive_list += f" (+{data['incentive_count'] - 5} more)"
        
        regulation_list = '; '.join(data['regulations'][:5])
        if data['regulation_count'] > 5:
            regulation_list += f" (+{data['regulation_count'] - 5} more)"
        
        # Create URL lists (first 3 URLs)
        permit_urls = '; '.join([url for url in data['permit_urls'][:3] if url])
        incentive_urls = '; '.join([url for url in data['incentive_urls'][:3] if url])
        regulation_urls = '; '.join([url for url in data['regulation_urls'][:3] if url])
        
        rows.append({
            'NAME': data['county'],
            'STATEFP': data['state_fips'],
            'STATE_ABBR': data['state'],
            'PERMIT_CNT': data['permit_count'],
            'INCENTV_CNT': data['incentive_count'],
            'REGULN_CNT': data['regulation_count'],
            'TOTAL_CNT': data['permit_count'] + data['incentive_count'] + data['regulation_count'],
            'PERMIT_LST': permit_list or 'None',
            'INCENTV_LST': incentive_list or 'None',
            'REGULN_LST': regulation_list or 'None',
            'PERMIT_URLS': permit_urls or 'None',
            'INCENTV_URLS': incentive_urls or 'None',
            'REGULN_URLS': regulation_urls or 'None'
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values(['STATEFP', 'NAME'])
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Exported {len(df)} counties to {output_file}")
    print(f"\n📊 Sample (first 10):")
    print(df[['NAME', 'STATE_ABBR', 'PERMIT_CNT', 'INCENTV_CNT', 'REGULN_CNT', 'TOTAL_CNT']].head(10))
    print(f"\n📈 Totals:")
    print(f"   Counties with data: {len(df)}")
    print(f"   Total permit entries: {df['PERMIT_CNT'].sum()}")
    print(f"   Total incentive entries: {df['INCENTV_CNT'].sum()}")
    print(f"   Total regulation entries: {df['REGULN_CNT'].sum()}")
    
    return output_file

def main():
    print("="*70)
    print("SMART QGIS Export - State & Federal Data Distribution")
    print("="*70 + "\n")
    
    # Find and load shapefile
    shapefile_path = find_shapefile()
    all_counties = load_all_counties_from_shapefile(shapefile_path)
    
    # Fetch data
    data = fetch_all_data()
    
    # Categorize
    county_data, state_data, federal_data, unknown = categorize_data(data)
    
    # Aggregate
    print(f"\n🔄 Distributing data to all counties...")
    aggregated = aggregate_for_counties(all_counties, county_data, state_data, federal_data)
    
    # Export
    csv_file = export_to_csv(aggregated)
    
    if csv_file:
        print("\n" + "="*70)
        print("✅ READY FOR QGIS!")
        print("="*70)
        print(f"CSV file created: {csv_file}")
        print("="*70)

if __name__ == '__main__':
    main()