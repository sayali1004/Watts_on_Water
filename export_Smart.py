"""
SMART Export for QGIS - Auto-detects counties and their states
Uses comprehensive county-to-state lookup from US Census data
"""

import os
import re
import pandas as pd
from supabase import create_client
from collections import defaultdict

# Import the county lookup (you'll need to download county_state_lookup.py)
try:
    from county_state_lookup import COUNTY_TO_STATE_FIPS
    print("✅ Loaded county-to-state lookup")
except ImportError:
    print("⚠️  County lookup not found - will use basic extraction only")
    COUNTY_TO_STATE_FIPS = {}

# State FIPS to abbreviation mapping
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

# Supabase credentials - REPLACE WITH YOURS
SUPABASE_URL = 'https://kvgvutzrlmstberrsyzv.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2Z3Z1dHpybG1zdGJlcnJzeXp2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTYxMjY1NCwiZXhwIjoyMDkxMTg4NjU0fQ.lI_9aYyO96nEuqprEOXUf_RB0zeTE5RartbgR-G4oNQ'

def extract_county_and_state(parameter_name, description=None):
    """
    Intelligently extract county and state from parameter_name
    Returns (county_name, state_abbr, state_fips)
    """
    if not parameter_name:
        return None, None, None
    
    text = str(parameter_name)
    if description:
        text += " " + str(description)
    
    # 1. Try to extract county name with "County" keyword
    county_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+County', text)
    county_name = county_match.group(1) if county_match else None
    
    # 2. Try to find state explicitly mentioned
    state_abbr = None
    state_patterns = {
        'CA': ['California', ' CA ', ', CA', 'CA-'],
        'AL': ['Alabama', ' AL ', ', AL', 'AL-'],
        'AK': ['Alaska', ' AK ', ', AK', 'AK-'],
        'AZ': ['Arizona', ' AZ ', ', AZ', 'AZ-'],
        'AR': ['Arkansas', ' AR ', ', AR', 'AR-'],
        'CO': ['Colorado', ' CO ', ', CO', 'CO-'],
        'CT': ['Connecticut', ' CT ', ', CT', 'CT-'],
        'DE': ['Delaware', ' DE ', ', DE', 'DE-'],
        'FL': ['Florida', ' FL ', ', FL', 'FL-'],
        'GA': ['Georgia', ' GA ', ', GA', 'GA-'],
        'HI': ['Hawaii', ' HI ', ', HI', 'HI-'],
        'ID': ['Idaho', ' ID ', ', ID', 'ID-'],
        'IL': ['Illinois', ' IL ', ', IL', 'IL-'],
        'IN': ['Indiana', ' IN ', ', IN', 'IN-'],
        'IA': ['Iowa', ' IA ', ', IA', 'IA-'],
        'KS': ['Kansas', ' KS ', ', KS', 'KS-'],
        'KY': ['Kentucky', ' KY ', ', KY', 'KY-'],
        'LA': ['Louisiana', ' LA ', ', LA', 'LA-'],
        'ME': ['Maine', ' ME ', ', ME', 'ME-'],
        'MD': ['Maryland', ' MD ', ', MD', 'MD-'],
        'MA': ['Massachusetts', ' MA ', ', MA', 'MA-'],
        'MI': ['Michigan', ' MI ', ', MI', 'MI-'],
        'MN': ['Minnesota', ' MN ', ', MN', 'MN-'],
        'MS': ['Mississippi', ' MS ', ', MS', 'MS-'],
        'MO': ['Missouri', ' MO ', ', MO', 'MO-'],
        'MT': ['Montana', ' MT ', ', MT', 'MT-'],
        'NE': ['Nebraska', ' NE ', ', NE', 'NE-'],
        'NV': ['Nevada', ' NV ', ', NV', 'NV-'],
        'NH': ['New Hampshire', ' NH ', ', NH', 'NH-'],
        'NJ': ['New Jersey', ' NJ ', ', NJ', 'NJ-'],
        'NM': ['New Mexico', ' NM ', ', NM', 'NM-'],
        'NY': ['New York', ' NY ', ', NY', 'NY-'],
        'NC': ['North Carolina', ' NC ', ', NC', 'NC-'],
        'ND': ['North Dakota', ' ND ', ', ND', 'ND-'],
        'OH': ['Ohio', ' OH ', ', OH', 'OH-'],
        'OK': ['Oklahoma', ' OK ', ', OK', 'OK-'],
        'OR': ['Oregon', ' OR ', ', OR', 'OR-'],
        'PA': ['Pennsylvania', ' PA ', ', PA', 'PA-'],
        'RI': ['Rhode Island', ' RI ', ', RI', 'RI-'],
        'SC': ['South Carolina', ' SC ', ', SC', 'SC-'],
        'SD': ['South Dakota', ' SD ', ', SD', 'SD-'],
        'TN': ['Tennessee', ' TN ', ', TN', 'TN-'],
        'TX': ['Texas', ' TX ', ', TX', 'TX-'],
        'UT': ['Utah', ' UT ', ', UT', 'UT-'],
        'VT': ['Vermont', ' VT ', ', VT', 'VT-'],
        'VA': ['Virginia', ' VA ', ', VA', 'VA-'],
        'WA': ['Washington', ' WA ', ', WA', 'WA-'],
        'WV': ['West Virginia', ' WV ', ', WV', 'WV-'],
        'WI': ['Wisconsin', ' WI ', ', WI', 'WI-'],
        'WY': ['Wyoming', ' WY ', ', WY', 'WY-'],
    }
    
    for state, patterns in state_patterns.items():
        if any(p in text for p in patterns):
            state_abbr = state
            break
    
    # 3. If we have county but no state, look it up
    if county_name and not state_abbr and COUNTY_TO_STATE_FIPS:
        possible_states = COUNTY_TO_STATE_FIPS.get(county_name, [])
        if len(possible_states) == 1:
            # Only one possible state for this county
            state_fips = possible_states[0]
            state_abbr = STATE_FIPS_TO_ABBR.get(state_fips)
        elif len(possible_states) > 1:
            # Multiple states - try to guess from context
            # Default to California if it's one of the options (most common in your data)
            if '06' in possible_states:
                state_fips = '06'
                state_abbr = 'CA'
            else:
                state_fips = possible_states[0]
                state_abbr = STATE_FIPS_TO_ABBR.get(state_fips)
    
    # 4. Convert state abbr to FIPS
    state_fips = STATE_ABBR_TO_FIPS.get(state_abbr) if state_abbr else None
    
    return county_name, state_abbr, state_fips

def fetch_all_data():
    """Fetch all records from Supabase"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("Fetching data from Supabase...")
    response = supabase.table('permits_data').select('*').execute()
    
    print(f"Fetched {len(response.data)} records\n")
    return response.data

def aggregate_by_county(data):
    """Aggregate data by county"""
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
    
    processed = 0
    skipped = 0
    
    for record in data:
        # Extract county and state
        county, state, state_fips = extract_county_and_state(
            record.get('parameter_name'),
            record.get('description')
        )
        
        if not county or not state:
            skipped += 1
            continue
        
        processed += 1
        key = f"{county}_{state}"
        
        # Set county info
        county_data[key]['county'] = county
        county_data[key]['state'] = state
        county_data[key]['state_fips'] = state_fips
        
        # Add data
        summary = record.get('parameter_name', 'N/A')
        url = record.get('url', '')
        data_type = record.get('data_type')
        
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
    
    print(f"✅ Processed: {processed} records")
    print(f"⚠️  Skipped: {skipped} records (no county/state found)")
    
    return county_data

def export_to_csv(county_data, output_file='county_permits_for_qgis.csv'):
    """Export to CSV"""
    if not county_data:
        print("\n❌ No county data to export!")
        return None
    
    rows = []
    for key, data in county_data.items():
        permit_list = '; '.join(data['permits'][:3])
        if data['permit_count'] > 3:
            permit_list += f" (+{data['permit_count'] - 3} more)"
        
        incentive_list = '; '.join(data['incentives'][:3])
        if data['incentive_count'] > 3:
            incentive_list += f" (+{data['incentive_count'] - 3} more)"
        
        regulation_list = '; '.join(data['regulations'][:3])
        if data['regulation_count'] > 3:
            regulation_list += f" (+{data['regulation_count'] - 3} more)"
        
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
            'PERMIT_URL': data['permit_urls'][0] if data['permit_urls'] else '',
            'INCENTV_URL': data['incentive_urls'][0] if data['incentive_urls'] else '',
            'REGULN_URL': data['regulation_urls'][0] if data['regulation_urls'] else ''
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values(['STATEFP', 'NAME'])
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Exported {len(df)} counties to {output_file}")
    print(f"\n📊 Sample (first 10):")
    print(df[['NAME', 'STATE_ABBR', 'PERMIT_CNT', 'INCENTV_CNT', 'REGULN_CNT']].head(10))
    print(f"\n📈 Totals:")
    print(f"   Permits: {df['PERMIT_CNT'].sum()}")
    print(f"   Incentives: {df['INCENTV_CNT'].sum()}")
    print(f"   Regulations: {df['REGULN_CNT'].sum()}")
    
    return output_file

def main():
    print("="*60)
    print("SMART QGIS Export - Auto County/State Detection")
    print("="*60 + "\n")
    
    data = fetch_all_data()
    county_data = aggregate_by_county(data)
    
    print(f"\nFound {len(county_data)} unique counties\n")
    
    if county_data:
        csv_file = export_to_csv(county_data)
        if csv_file:
            print("\n" + "="*60)
            print("✅ READY FOR QGIS!")
            print("="*60)
            print(f"1. Load: tl_2025_us_county.shp")
            print(f"2. Load: {csv_file}")
            print(f"3. Join on: NAME field")
            print("="*60)
    else:
        print("\n❌ No counties found - check your data!")

if __name__ == '__main__':
    main()