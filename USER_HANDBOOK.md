# SCEIN Fellowship Data Pipeline
## Complete User Handbook

**Version 2.0 | May 2026**

---

## Table of Contents

1. [Tech Stack](#1-tech-stack)
2. [Pipeline Architecture](#2-pipeline-architecture)
3. [Prerequisites & Installation](#3-prerequisites--installation)
4. [Repository Setup](#4-repository-setup)
5. [Supabase Setup](#5-supabase-setup)
6. [GitHub Actions Setup](#6-github-actions-setup)
7. [Running the Scraper](#7-running-the-scraper)
8. [Running the Exports](#8-running-the-exports)
9. [QGIS Setup](#9-qgis-setup)
10. [Updating Data Monthly](#10-updating-data-monthly)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Tech Stack

| Component | Tool | Purpose |
|---|---|---|
| Data source | Excel (.xlsx) | Contains 640+ URLs for permits, incentives, regulations |
| Scraper | Python 3.11 | Reads Excel, scrapes each URL, extracts metadata |
| Database | Supabase (PostgreSQL) | Stores all scraped records |
| Automation | GitHub Actions | Runs scraper monthly, triggered manually |
| Export | Python (pandas, geopandas) | Pulls from Supabase, generates QGIS-ready CSVs |
| Visualization | QGIS 3.28+ | Choropleth map + click-to-explore detail |

**Python packages required:**
```
pandas
openpyxl
requests
beautifulsoup4
supabase
lxml
python-dateutil
python-dotenv
geopandas
```

---

## 2. Pipeline Architecture

```
Excel File (.xlsx)
    │
    │  read_excel_data() — reads 10 columns per row:
    │  Dataset Name, Description, Source Accreditation,
    │  Data Age, Owner Class, Item Type, Applicable System
    │  Types, Min/Max System Size, Cost, URL
    ▼
scraper.py
    │  For each URL → HTTP request → scrape webpage
    │  Extracts: title, full text, dates, cost, timeframe, status
    │  Upserts to Supabase on conflict (url, data_type, excel_sheet, excel_row)
    ▼
Supabase (permits_data table)
    │  640+ records
    │  One row per item (permit / incentive / regulation)
    │
    ├──▶ export_qgis.py
    │         Pulls all records from Supabase
    │         Fills missing state info using county lookup
    │         Outputs: county_permits_for_qgis.csv
    │         (one row per item, flat — for analysis)
    │
    └──▶ export_with_propagation.py
              Pulls county_permits_for_qgis.csv
              Reads shapefile to get all 3,235 US counties
              Distributes items by scope:
                - County-specific → only that county
                - State-level → all counties in that state
                - Federal → all 3,235 US counties
              Outputs: detail_propagated.csv
              (~210,000 rows — one per county-item pair)
                    │
                    ▼
                  QGIS
                    ├── Choropleth layer (counts per county)
                    └── 3 relation layers (click to explore)
                          Permits / Regulations / Incentives
```

---

## 3. Prerequisites & Installation

### 3.1 Python

Install Python 3.11 or newer:
- Download from https://python.org/downloads
- Verify: `python --version`

### 3.2 Git

- Mac: `xcode-select --install`
- Windows: download from https://git-scm.com

### 3.3 QGIS

- Download QGIS 3.28 or newer from https://qgis.org/download/
- Install and open to verify it works

### 3.4 US County Shapefile

Download the 2025 US county shapefile from the US Census:
- Go to: https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- Download: `tl_2025_us_county.zip`
- Extract — you need these 4 files together in the same folder:
  - `tl_2025_us_county.shp`
  - `tl_2025_us_county.shx`
  - `tl_2025_us_county.dbf`
  - `tl_2025_us_county.prj`

---

## 4. Repository Setup

### 4.1 Clone the repository

```bash
git clone https://github.com/sayali1004/Watts_on_Water.git
cd Watts_on_Water
```

### 4.2 Install Python dependencies

```bash
pip install -r requirements_local.txt
```

### 4.3 Create your .env file

```bash
cp .env.example .env
```

Open `.env` and fill in your Supabase credentials:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

> The service role key is found in your Supabase project: Settings → API → service_role (secret)

---

## 5. Supabase Setup

### 5.1 Create a Supabase project

1. Go to https://supabase.com and sign in
2. Click **New Project**
3. Choose a name, database password, and region
4. Wait for the project to be ready (~2 minutes)

### 5.2 Run the schema

1. In your Supabase project → click **SQL Editor**
2. Open `supabase_schema_scein.sql` from the repository
3. Copy the entire file contents
4. Paste into the SQL Editor
5. Click **Run**

This creates the `permits_data` table with all required columns and the composite unique constraint `unique_permit_row (url, data_type, excel_sheet, excel_row)`.

### 5.3 Verify

In Supabase → **Table Editor** → you should see `permits_data` listed.

---

## 6. GitHub Actions Setup

The scraper runs automatically every 1st of the month via GitHub Actions.

### 6.1 Add Supabase credentials as GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings → Secrets and variables → Actions**
3. Click **New repository secret** — add two secrets:
   - Name: `SUPABASE_URL` → Value: your Supabase project URL
   - Name: `SUPABASE_KEY` → Value: your service role key

### 6.2 Verify the workflow

- Go to repository → **Actions** tab
- You should see **Scrape SCEIN Data** listed
- Click **Run workflow** to trigger it manually

### 6.3 Workflow schedule

The workflow runs automatically on the **1st of every month at 8 AM UTC**.
To trigger manually: Actions → Scrape SCEIN Data → Run workflow → Run workflow.

---

## 7. Running the Scraper

The scraper reads the Excel file, visits each URL, and saves data to Supabase.

### 7.1 Locally

Make sure your `.env` file has valid Supabase credentials, then:

```bash
cd Watts_on_Water
python scraper.py
```

### 7.2 What the scraper reads from Excel

| Column | Index | Field |
|---|---|---|
| Description | 1 | description |
| Dataset Name | 5 | parameter_name |
| Source Accreditation | 7 | source_accreditation |
| Source URL | 8 | url |
| Data Age | 9 | data_age |
| Owner Class | 11 | owner_class |
| Permit/Incentive/Regulation Type | 19 | item_type |
| Applicable System Types | 20 | applicable_system_types |
| Min System Size [MW] | 22 | min_system_size_mw |
| Max System Size [MW] | 23 | max_system_size_mw |
| Cost [$] | 24 | cost |

### 7.3 What the scraper extracts from each webpage

- Page title
- Full text content (up to 10,000 characters)
- Effective date, expiry date, last updated
- Requirements
- Cost (if not already in Excel)
- Processing timeframe (days)
- Status: active / expired / pending / amended

### 7.4 Upsert logic

Records are upserted (insert or update) using the composite unique key:
`(url, data_type, excel_sheet, excel_row)`

This means running the scraper again on the same data updates existing records rather than creating duplicates.

---

## 8. Running the Exports

Two export scripts generate the files needed for QGIS.

### 8.1 Export flat CSV (county_permits_for_qgis.csv)

```bash
python export_qgis.py
```

**Output:** `county_permits_for_qgis.csv`
- One row per item (permit / incentive / regulation)
- 640 rows
- Columns: NAME, STATEFP, STATE_ABBR, SCOPE, CATEGORY, OWNER_CLASS, ITEM_TYPE, DATASET_NAME, SOURCE_ACCREDITATION, URL, DATA_AGE, DESCRIPTION, APPLICABLE_SYSTEM_TYPES, MIN_SYSTEM_SIZE_MW, MAX_SYSTEM_SIZE_MW, COST, STATUS, EFFECTIVE_DATE, EXPIRY_DATE, TIMEFRAME_DAYS

**SCOPE values:**
- `county` — applies to one specific county
- `state` — applies to all counties in a state
- `federal` — applies to all US counties
- `unknown` — could not determine scope

### 8.2 Export propagated detail CSV (detail_propagated.csv)

```bash
python export_with_propagation.py /path/to/tl_2025_us_county.shp
```

**Output:** `detail_propagated.csv`
- ~210,000 rows
- One row per county × applicable item
- Federal items distributed to all 3,235 counties
- State items distributed to all counties in that state
- County items kept for their specific county only
- Same columns as above, plus NAME (county) and STATEFP

> This file is large (~50MB) but pre-computed so QGIS loads it fast.

---

## 9. QGIS Setup

### 9.1 Load the base layers

**Load the shapefile:**
1. Layer → Add Layer → Add Vector Layer
2. Browse to `tl_2025_us_county.shp` → Add

**Load the detail CSV:**
1. Layer → Add Layer → Add Delimited Text Layer
2. Browse to `detail_propagated.csv`
3. Geometry definition: **No geometry**
4. Click Add

### 9.2 Create the choropleth (color by count)

**Create a count virtual layer:**
1. Layer → Create Layer → New Virtual Layer
2. Paste in the Query box:
```sql
SELECT NAME, STATEFP,
  COUNT(*) AS total_count,
  SUM(CASE WHEN CATEGORY='permit' THEN 1 ELSE 0 END) AS permit_count,
  SUM(CASE WHEN CATEGORY='incentive' THEN 1 ELSE 0 END) AS incentive_count,
  SUM(CASE WHEN CATEGORY='regulation' THEN 1 ELSE 0 END) AS regulation_count
FROM detail_propagated
WHERE NAME != ''
GROUP BY NAME, STATEFP
```
3. Click Add — rename this layer `counts_layer`

**Join counts to shapefile:**
1. Right-click `tl_2025_us_county` → Properties → Joins → green **+**
2. Join layer: `counts_layer` | Join field: `NAME` | Target field: `NAME`
3. Check **Custom field name prefix** → clear it (leave blank)
4. OK → OK

**Apply graduated colors:**
1. Right-click `tl_2025_us_county` → Properties → Symbology
2. Change to **Graduated**
3. Value: `total_count`
4. Color ramp: Yellow → Red (or any preference)
5. Mode: **Natural Breaks (Jenks)** | Classes: **5**
6. Click **Classify** → OK

### 9.3 Create the 3 category layers

These power the click-to-explore detail. Do this 3 times:

**Layer → Create Layer → New Virtual Layer:**

```sql
-- Layer 1 — rename to: permits_layer
SELECT * FROM detail_propagated WHERE CATEGORY = 'permit'
```
```sql
-- Layer 2 — rename to: regulations_layer
SELECT * FROM detail_propagated WHERE CATEGORY = 'regulation'
```
```sql
-- Layer 3 — rename to: incentives_layer
SELECT * FROM detail_propagated WHERE CATEGORY = 'incentive'
```

### 9.4 Set up 3 Relations

Go to **Project → Properties → Relations → green +** (do this 3 times):

| Name | Referenced layer | Referenced field | Referencing layer | Referencing field | Strength |
|---|---|---|---|---|---|
| Permits | tl_2025_us_county | NAME | permits_layer | NAME | Association |
| Regulations | tl_2025_us_county | NAME | regulations_layer | NAME | Association |
| Incentives | tl_2025_us_county | NAME | incentives_layer | NAME | Association |

Click OK to close Project Properties.

### 9.5 Configure the Feature Form

1. Right-click `tl_2025_us_county` → Properties → **Attributes Form**
2. At the top switch to **Drag and Drop Designer**
3. On the right, add 3 Group Boxes (click +):
   - Group: `Permits` → drag the **Permits** relation into it
   - Group: `Regulations` → drag the **Regulations** relation into it
   - Group: `Incentives` → drag the **Incentives** relation into it
4. Click OK

### 9.6 Configure multiline description display

Do this for each of the 3 category layers:

1. Right-click `permits_layer` → Properties → **Attributes Form**
2. Click **DESCRIPTION** in the field list
3. Widget Type → **Text Edit**
4. Check **Multiline**
5. Click OK

Repeat for `regulations_layer` and `incentives_layer`.

### 9.7 Click to explore

1. Select the **Identify Features** tool (ⓘ in toolbar)
2. Click any county on the map
3. Double-click the county in the Identify Results panel
4. The Feature Form opens with 3 collapsible sections:
   - **Permits** — all permits applicable to that county
   - **Regulations** — all regulations applicable to that county
   - **Incentives** — all incentives applicable to that county
5. Each section includes: Dataset Name, URL, Description, Item Type, Owner Class, Source Accreditation, Data Age, System Types, Min/Max System Size, Cost, Status, Scope

### 9.8 Save the project

Project → Save As → save as `SCEIN_Map.qgz` in the project folder.

---

## 10. Updating Data Monthly

When new data is added to the Excel file or the monthly scrape runs:

### 10.1 Re-run the scraper (if updating manually)

```bash
python scraper.py
```

### 10.2 Regenerate the flat CSV

```bash
python export_qgis.py
```

### 10.3 Regenerate the propagated CSV

```bash
python export_with_propagation.py /path/to/tl_2025_us_county.shp
```

### 10.4 Reload in QGIS

1. Open QGIS → open `SCEIN_Map.qgz`
2. Right-click `detail_propagated` → **Reload**
3. Right-click `counts_layer` (virtual layer) → **Reload**
4. The map automatically reflects the new data

### 10.5 Push updated files to GitHub

```bash
git add county_permits_for_qgis.csv detail_propagated.csv
git commit -m "Update exported data"
git push origin main
```

---

## 11. Troubleshooting

### Virtual layer is slow to load

**Cause:** Complex OR join logic computed live in QGIS.

**Fix:** Make sure you are using `detail_propagated.csv` (pre-computed) not the raw `county_permits_for_qgis.csv` for the relations. The virtual layers for the 3 categories use simple `WHERE CATEGORY =` filters which are fast.

---

### "Name or service not known" in GitHub Actions

**Cause:** `SUPABASE_URL` or `SUPABASE_KEY` secrets are not set or wrong.

**Fix:** Go to GitHub → Settings → Secrets and variables → Actions → update both secrets.

---

### "No unique constraint matching ON CONFLICT specification"

**Cause:** The `unique_permit_row` composite constraint is missing from the database.

**Fix:** Run the `DO $$...$$` block from `supabase_schema_scein.sql` in Supabase SQL Editor.

---

### export_with_propagation.py — "Operation not permitted"

**Cause:** macOS is blocking Python from reading files on the Desktop.

**Fix:** System Settings → Privacy & Security → Full Disk Access → add Terminal → toggle ON → restart Terminal.

---

### Choropleth shows all the same color

**Cause:** The join didn't work or `total_count` field is missing.

**Fix:**
1. Check the virtual layer `counts_layer` loaded correctly
2. Re-do the join: Properties → Joins → remove old join → add new one
3. Symbology → re-classify

---

### Description text is cut off in QGIS

**Fix:** Right-click the layer → Properties → Attributes Form → click DESCRIPTION → Widget Type: **Text Edit** → check **Multiline** → OK.

---

**Repository:** https://github.com/sayali1004/Watts_on_Water

**End of Handbook**
