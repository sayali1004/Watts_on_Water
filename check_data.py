"""
Quick script to check what your Supabase data actually looks like
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env or environment")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch first 10 records
response = supabase.table('permits_data').select('*').limit(10).execute()

print("Sample of 10 records from your database:\n")
for i, record in enumerate(response.data, 1):
    print(f"Record {i}:")
    print(f"  parameter_name: {record.get('parameter_name')}")
    print(f"  county: {record.get('county')}")
    print(f"  state: {record.get('state')}")
    print(f"  data_type: {record.get('data_type')}")
    print()