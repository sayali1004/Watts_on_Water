# SCEIN Fellowship Data Pipeline - Complete Setup Guide
### Zero-Cost, Automated, Live-Updating System

## 🎯 Overview

This system automatically scrapes permit/incentive/regulation data from your Excel links, stores it in Supabase, and displays it live in QGIS. All free, no servers needed.

**Stack:**
- GitHub Actions (free cron replacement)
- Supabase (free PostgreSQL + PostGIS)
- QGIS (free desktop GIS)
- Python scraper

---

## 📋 Step 1: Setup Supabase (5 minutes)

### 1.1 Create Account
1. Go to [supabase.com](https://supabase.com)
2. Sign up (free tier - no credit card needed)
3. Create a new project
   - Choose a database password (save this!)
   - Choose region closest to you
   - Wait 2 minutes for project creation

### 1.2 Get Credentials
1. In your project dashboard, go to **Settings** > **API**
2. Copy these values:
   - `Project URL` (looks like: https://xxxxx.supabase.co)
   - `anon public` key (starts with eyJ...)
   - `service_role` key (starts with eyJ... - KEEP SECRET!)

3. Go to **Settings** > **Database**
4. Scroll to **Connection String** > **URI**
5. Copy the connection string (you'll need this for QGIS)

### 1.3 Run SQL Schema
1. In Supabase dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy the entire contents of `supabase_schema_scein.sql`
4. Paste and click **Run**
5. You should see: "Success. No rows returned"

---

## 📋 Step 2: Setup GitHub Repository (10 minutes)

### 2.1 Create Repository
1. Go to [github.com](https://github.com)
2. Create new repository (public or private - free either way)
3. Name it: `scein-data-pipeline`

### 2.2 Upload Files
Clone or upload these files to your repo:
```
scein-data-pipeline/
├── .github/
│   └── workflows/
│       └── scrape.yml
├── scein_scraper.py
├── requirements.txt
└── SCEIN_Fellowship_Data_Tracker_Google_Sheets__1_.xlsx
```

### 2.3 Configure Secrets
1. In your GitHub repo, go to **Settings** > **Secrets and variables** > **Actions**
2. Click **New repository secret**
3. Add these secrets:

**Secret 1:**
- Name: `SUPABASE_URL`
- Value: Your Project URL from Supabase (https://xxxxx.supabase.co)

**Secret 2:**
- Name: `SUPABASE_KEY`
- Value: Your `service_role` key from Supabase

---

## 📋 Step 3: Test the Scraper (Optional but Recommended)

Before running the full scraper, test with a small sample:

```bash
# Clone your repo locally
git clone https://github.com/YOUR_USERNAME/scein-data-pipeline
cd scein-data-pipeline

# Install dependencies
pip install -r requirements.txt

# Set environment variables (replace with your values)
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_KEY="your_service_role_key"
export MAX_URLS=5  # Test with just 5 URLs

# Run scraper
python scein_scraper.py
```

If successful, you'll see:
```
INFO - Reading sheet: Permits
INFO - Reading sheet: Incentives
INFO - Reading sheet: Regulations
INFO - Total records to scrape: 5
INFO - Scraping: https://...
INFO - Saving 5 records to Supabase
INFO - Successfully saved all 5 records
```

Check Supabase:
1. Go to **Table Editor** > `permits_data`
2. You should see 5 rows

---

## 📋 Step 4: Schedule Automated Scraping

### 4.1 Trigger Manual Run
1. In GitHub, go to **Actions**
2. Click **Scrape Permits Data**
3. Click **Run workflow** > **Run workflow**
4. Wait 5-15 minutes (scraping ~600 URLs takes time)
5. Check for green checkmark ✓

### 4.2 Configure Schedule
The workflow is already set to run daily at 2 AM UTC. To change:

Edit `.github/workflows/scrape.yml`:
```yaml
schedule:
  - cron: '0 2 * * *'  # 2 AM UTC daily
  # Examples:
  # - cron: '0 */6 * * *'  # Every 6 hours
  # - cron: '0 0 * * 0'    # Weekly on Sunday
```

### 4.3 Monitor Runs
- Go to **Actions** tab in GitHub
- Click on any run to see logs
- Download artifacts if errors occur

---

## 📋 Step 5: Connect QGIS (10 minutes)

### 5.1 Install QGIS
1. Download from [qgis.org](https://qgis.org/download/)
2. Install (choose Long Term Release version)

### 5.2 Add Supabase Connection

1. Open QGIS
2. Go to **Browser** panel (left side)
3. Right-click **PostGIS** > **New Connection**

Fill in:
- **Name:** `SCEIN Supabase`
- **Host:** `db.xxxxx.supabase.co` (from your connection string)
- **Port:** `5432`
- **Database:** `postgres`
- **SSL mode:** `require`
- **Authentication:**
  - **Username:** `postgres`
  - **Password:** (your database password from Step 1.1)

Click **Test Connection** - should see "Connection successful"

### 5.3 Add Data Layers

1. Expand **PostGIS** > **SCEIN Supabase**
2. Double-click `public.permits_data` to add layer
3. Alternative views to add:
   - `public.active_permits`
   - `public.active_incentives`
   - `public.active_regulations`
   - `public.california_county_stats`

---

## 📋 Step 6: Configure Auto-Refresh in QGIS

### Option A: Manual Python Script in QGIS Console
1. In QGIS, go to **Plugins** > **Python Console**
2. Paste this script:

```python
from PyQt5.QtCore import QTimer

def refresh_all():
    for layer in QgsProject.instance().mapLayers().values():
        if layer.dataProvider().name() == 'postgres':
            layer.reload()
    iface.mapCanvas().refresh()
    print(f"✓ Refreshed at {QDateTime.currentDateTime().toString()}")

# Refresh every 5 minutes (300000 ms)
timer = QTimer()
timer.timeout.connect(refresh_all)
timer.start(300000)

# Store timer to prevent garbage collection
if not hasattr(iface, 'refresh_timer'):
    iface.refresh_timer = timer

print("Auto-refresh enabled: every 5 minutes")
```

### Option B: QGIS Startup Script (Persistent)
1. Go to **Settings** > **Options** > **System**
2. Enable **Environment** > **Custom variables**
3. Go to **Settings** > **Options** > **Python**
4. Copy the script above to **Startup script path**

---

## 📋 Step 7: Visualize Your Data

### 7.1 Basic Styling by Type

Right-click layer > **Properties** > **Symbology**:

**Categorized by `data_type`:**
- `permit`: Blue
- `incentive`: Green  
- `regulation`: Orange

### 7.2 Filter by Status

Add filter: `status = 'active'`

Right-click layer > **Filter** > paste SQL:
```sql
"status" = 'active' AND "data_type" = 'permit'
```

### 7.3 Add Heatmap (if using location data)

After geocoding counties:
1. Right-click layer > **Duplicate Layer**
2. Change symbology to **Heatmap**
3. Set radius based on zoom level

---

## 🔧 Advanced: Add Geocoding (Optional)

To add spatial coordinates for mapping:

### Option 1: Use Python with Geopy

```python
# geocode_counties.py
from geopy.geocoders import Nominatim
from supabase import create_client
import time

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
geolocator = Nominatim(user_agent="scein_geocoder")

# Get unique counties
result = supabase.table('permits_data').select('county, state').execute()
counties = set((r['county'], r['state']) for r in result.data if r['county'])

for county, state in counties:
    try:
        location = geolocator.geocode(f"{county} County, {state}, USA")
        if location:
            # Update all records for this county
            supabase.table('permits_data').update({
                'location': f'POINT({location.longitude} {location.latitude})'
            }).eq('county', county).eq('state', state).execute()
            
            print(f"✓ {county}, {state}: {location.latitude}, {location.longitude}")
            time.sleep(1)  # Rate limiting
    except Exception as e:
        print(f"✗ {county}, {state}: {e}")
```

Run manually or add to GitHub Actions workflow.

---

## 🔄 How It Works

### Data Flow:
```
Excel File (GitHub)
    ↓
GitHub Actions (daily 2 AM)
    ↓
Python Scraper (scein_scraper.py)
    ↓  (scrapes URLs)
Web Pages
    ↓  (extracts data)
Supabase PostgreSQL
    ↓  (real-time connection)
QGIS Desktop (auto-refresh every 5 min)
```

### What Gets Updated:
- **GitHub Actions** checks for changes to Excel file
- If file updated → scraper runs
- Scraper reads ALL URLs from Excel
- For each URL:
  - Fetches webpage
  - Extracts: title, dates, costs, requirements, status
  - Stores in Supabase
- Supabase triggers update timestamp
- QGIS auto-refreshes layer

---

## 📊 Monitoring & Maintenance

### Check Scraper Health

In Supabase SQL Editor:
```sql
-- View scraping health
SELECT * FROM scraping_health;

-- Recent errors
SELECT * FROM permits_data 
WHERE status = 'error' 
ORDER BY scraped_at DESC 
LIMIT 10;

-- Oldest data (needs re-scraping)
SELECT data_type, county, MAX(scraped_at) as last_scrape
FROM permits_data
GROUP BY data_type, county
HAVING MAX(scraped_at) < NOW() - INTERVAL '7 days'
ORDER BY last_scrape;
```

### Manual Triggers

**Re-scrape specific URLs:**
1. Update Excel file with just those URLs
2. Trigger GitHub Actions manually
3. Restore full Excel file

**Full re-scrape:**
1. Delete all from Supabase: `DELETE FROM permits_data;`
2. Trigger GitHub Actions

---

## ⚠️ Troubleshooting

### Scraper Fails in GitHub Actions
- Check **Actions** > **Scrape Permits Data** > Click failed run
- Look for error in logs
- Common issues:
  - Wrong credentials → Update secrets
  - Network timeout → Add retry logic
  - Excel file missing → Ensure file is committed

### QGIS Connection Fails
- Verify host: `db.xxxxx.supabase.co` (NOT `https://xxxxx.supabase.co`)
- Check firewall allows port 5432
- Verify SSL mode is `require`

### No Data in QGIS
- Check Supabase Table Editor → does `permits_data` have rows?
- If no: Run GitHub Actions workflow manually
- Refresh QGIS layer: Right-click > **Reload**

---

## 💰 Cost Breakdown (All FREE)

| Service | Free Tier Limits | Your Usage | Cost |
|---------|-----------------|------------|------|
| **Supabase** | 500 MB database, 2 GB bandwidth/month | ~50 MB for 600 URLs | $0 |
| **GitHub Actions** | 2,000 minutes/month | ~15 min/day = 450 min/month | $0 |
| **QGIS** | Unlimited | Unlimited | $0 |
| **Python** | Open source | Unlimited | $0 |

**Total:** $0/month ✅

---

## 🚀 Next Steps

1. **Add more data fields:** Edit `scein_scraper.py` to extract additional fields
2. **Improve scraping logic:** Customize extraction patterns for specific websites
3. **Add geocoding:** Implement county→coordinates mapping
4. **Create dashboards:** Use Supabase + Grafana or build custom dashboard
5. **Export functionality:** Add endpoints to export data as CSV/GeoJSON
6. **Notification system:** Set up alerts when key permits expire

---

## 📚 Resources

- [Supabase Docs](https://supabase.com/docs)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [QGIS Documentation](https://docs.qgis.org/)
- [BeautifulSoup Docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

---

## 🆘 Support

Questions? Issues? 

1. Check logs in GitHub Actions
2. Check data in Supabase Table Editor
3. Test scraper locally with `MAX_URLS=1`
4. Review connection settings in QGIS

---

**You now have a fully automated, zero-cost, live-updating data pipeline! 🎉**
