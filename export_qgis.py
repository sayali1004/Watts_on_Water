
"""
Export Supabase permits/incentives/regulations data for QGIS
Creates CSV that joins with tl_2025_us_county.shp using NAME and STATEFP fields
"""

import os
import re
import pandas as pd
from supabase import create_client
from collections import defaultdict

# State abbreviation to FIPS code mapping
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
    'WY': '56', 'PR': '72', 'US': '00'  # US for federal
}

# Supabase credentials - REPLACE THESE WITH YOUR ACTUAL CREDENTIALS
SUPABASE_URL = 'https://kvgvutzrlmstberrsyzv.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2Z3Z1dHpybG1zdGJlcnJzeXp2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTYxMjY1NCwiZXhwIjoyMDkxMTg4NjU0fQ.lI_9aYyO96nEuqprEOXUf_RB0zeTE5RartbgR-G4oNQ'

def extract_county_from_parameter_name(param_name):
    """Extract county name from parameter name like 'Alameda County — Building permits'"""
    if not param_name:
        return None
    
    # Pattern: "Alameda County — ..." or "Contra Costa County —"
    match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+County', str(param_name))
    if match:
        return match.group(1)
    
    return None

def extract_state_from_parameter_name(param_name):
    """Extract state from parameter name or description"""
    if not param_name:
        return None
    
    # Look for state codes or "California"
    state_patterns = {
        'CA': ['California', ' CA ', ', CA'],
        'AL': ['Alabama', ' AL ', ', AL'],
        'AR': ['Arkansas', ' AR ', ', AR'],
        'CT': ['Connecticut', ' CT ', ', CT'],
        'US': ['US-Federal', 'United States', 'Federal']
    }
    
    name_str = str(param_name)
    for code, patterns in state_patterns.items():
        if any(p in name_str for p in patterns):
            return code
    
    return None

def fetch_all_data():
    """Fetch all records from Supabase"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("Fetching data from Supabase...")
    response = supabase.table('permits_data').select('*').execute()
    
    print(f"Fetched {len(response.data)} records")
    return response.data

def aggregate_by_county(data):
    """Aggregate data by county with detailed lists"""
    county_data = defaultdict(lambda: {
        'county': None,
        'state': None,
        'state_fips': None,
        'permits': [],
        'incentives': [],
        'regulations': [],
        'permit_count': 0,
        'incentive_count': 0,
        'regulation_count': 0,
        'permit_urls': [],
        'incentive_urls': [],
        'regulation_urls': []
    })
    
    skipped_no_county = 0
    skipped_no_state = 0
    
    for record in data:
        # Try to get county from database first, then extract from parameter_name
        county = record.get('county')
        if not county:
            county = extract_county_from_parameter_name(record.get('parameter_name'))
        
        # Try to get state from database first, then extract from parameter_name
        state = record.get('state')
        if not state:
            state = extract_state_from_parameter_name(record.get('parameter_name'))
        
        data_type = record.get('data_type')
        
        # Skip if no county or state found
        if not county:
            skipped_no_county += 1
            continue
        if not state:
            skipped_no_state += 1
            continue
        
        # Get FIPS code for state
        state_fips = STATE_ABBR_TO_FIPS.get(state, '00')
        
        key = f"{county}_{state}"
        
        # Set county info
        county_data[key]['county'] = county
        county_data[key]['state'] = state
        county_data[key]['state_fips'] = state_fips
        
        # Create summary string
        summary = f"{record.get('parameter_name', 'N/A')}"
        url = record.get('url', '')
        
        # Add to appropriate list
        if data_type == 'permit':
            county_data[key]['permits'].append(summary)
            county_data[key]['permit_urls'].append(url)
            county_data[key]['permit_count'] += 1
        elif data_type == 'incentive':
            county_data[key]['incentives'].append(summary)
            county_data[key]['incentive_urls'].append(url)
            county_data[key]['incentive_count'] += 1
        elif data_type == 'regulation':
            county_data[key]['regulations'].append(summary)
            county_data[key]['regulation_urls'].append(url)
            county_data[key]['regulation_count'] += 1
    
    if skipped_no_county > 0:
        print(f"⚠️  Skipped {skipped_no_county} records with no county information")
    if skipped_no_state > 0:
        print(f"⚠️  Skipped {skipped_no_state} records with no state information")
    
    return county_data

def export_to_csv(county_data, output_file='county_permits_for_qgis.csv'):
    """Export data to CSV formatted for QGIS join with shapefile"""
    
    if not county_data:
        print("❌ ERROR: No county data to export!")
        print("This usually means:")
        print("  1. County/state fields are empty in Supabase")
        print("  2. Parameter names don't contain county information")
        print("\nPlease check your Supabase data.")
        return None
    
    rows = []
    
    for key, data in county_data.items():
        # Create summary lists (first 3 items)
        permit_list = '; '.join(data['permits'][:3])
        if data['permit_count'] > 3:
            permit_list += f" ... and {data['permit_count'] - 3} more"
            
        incentive_list = '; '.join(data['incentives'][:3])
        if data['incentive_count'] > 3:
            incentive_list += f" ... and {data['incentive_count'] - 3} more"
            
        regulation_list = '; '.join(data['regulations'][:3])
        if data['regulation_count'] > 3:
            regulation_list += f" ... and {data['regulation_count'] - 3} more"
        
        rows.append({
            'NAME': data['county'],  # Join field - matches shapefile NAME column
            'STATEFP': data['state_fips'],  # Join field - matches shapefile STATEFP column
            'STATE_ABBR': data['state'],
            'COUNTY_KEY': key,
            'PERMIT_COUNT': data['permit_count'],
            'INCENTIVE_COUNT': data['incentive_count'],
            'REGULATION_COUNT': data['regulation_count'],
            'TOTAL_COUNT': data['permit_count'] + data['incentive_count'] + data['regulation_count'],
            'PERMIT_LIST': permit_list if permit_list else 'None',
            'INCENTIVE_LIST': incentive_list if incentive_list else 'None',
            'REGULATION_LIST': regulation_list if regulation_list else 'None',
            'PERMIT_URL_1': data['permit_urls'][0] if len(data['permit_urls']) > 0 else '',
            'INCENTIVE_URL_1': data['incentive_urls'][0] if len(data['incentive_urls']) > 0 else '',
            'REGULATION_URL_1': data['regulation_urls'][0] if len(data['regulation_urls']) > 0 else ''
        })
    
    df = pd.DataFrame(rows)
    
    # Sort by state and county
    df = df.sort_values(['STATEFP', 'NAME'])
    
    df.to_csv(output_file, index=False)
    print(f"\n✅ Exported {len(df)} counties to {output_file}")
    
    # Show sample
    print(f"\nSample data (first 10 rows):")
    print(df[['NAME', 'STATE_ABBR', 'PERMIT_COUNT', 'INCENTIVE_COUNT', 'REGULATION_COUNT', 'TOTAL_COUNT']].head(10).to_string())
    
    # Show summary statistics
    print(f"\n📊 Summary Statistics:")
    print(f"   Total counties: {len(df)}")
    print(f"   Total permits: {df['PERMIT_COUNT'].sum()}")
    print(f"   Total incentives: {df['INCENTIVE_COUNT'].sum()}")
    print(f"   Total regulations: {df['REGULATION_COUNT'].sum()}")
    print(f"   Total items: {df['TOTAL_COUNT'].sum()}")
    
    return output_file

def main():
    """Main execution"""
    print("="*60)
    print("QGIS Data Export Script")
    print("="*60)
    
    # Fetch data
    data = fetch_all_data()
    
    if not data:
        print("❌ No data fetched from Supabase!")
        return
    
    # Aggregate by county
    county_data = aggregate_by_county(data)
    
    print(f"\nAggregated data for {len(county_data)} counties")
    
    if not county_data:
        print("\n❌ ERROR: Could not aggregate any counties!")
        print("\nTroubleshooting:")
        print("1. Check if 'county' and 'state' fields exist in your Supabase table")
        print("2. Check if 'parameter_name' contains county information")
        print("3. Run your scraper.py to populate county/state fields")
        return
    
    # Export to CSV for QGIS
    csv_file = export_to_csv(county_data)
    
    if csv_file:
        print("\n" + "="*60)
        print("✅ SUCCESS! Next steps:")
        print("="*60)
        print(f"1. Open QGIS")
        print(f"2. Load shapefile: tl_2025_us_county.shp")
        print(f"3. Load CSV: {csv_file}")
        print(f"4. Join using NAME field")
        print(f"5. Style by TOTAL_COUNT, PERMIT_COUNT, etc.")
        print("="*60)

if __name__ == '__main__':
    main()