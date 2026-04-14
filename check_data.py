"""
Quick script to check what your Supabase data actually looks like
"""
import os
from supabase import create_client

SUPABASE_URL = 'https://kvgvutzrlmstberrsyzv.supabase.co'  # Replace with yours
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2Z3Z1dHpybG1zdGJlcnJzeXp2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTYxMjY1NCwiZXhwIjoyMDkxMTg4NjU0fQ.lI_9aYyO96nEuqprEOXUf_RB0zeTE5RartbgR-G4oNQ'  # Replace with yours

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