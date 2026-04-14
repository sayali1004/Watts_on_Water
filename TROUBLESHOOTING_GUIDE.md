# SCEIN Data Pipeline - Complete Command Reference & Troubleshooting Guide

**For Technical Users | Step-by-Step Commands**

Last Updated: April 2026

---

## 📋 Table of Contents

1. [Daily Update Commands](#daily-update-commands)
2. [If Update Script Fails](#if-update-script-fails)
3. [Complete QGIS Setup from Scratch](#complete-qgis-setup-from-scratch)
4. [Join Troubleshooting](#join-troubleshooting)
5. [Data Type Issues](#data-type-issues)
6. [Emergency Recovery](#emergency-recovery)
7. [Verification Commands](#verification-commands)

---

## Daily Update Commands

### Standard Daily Workflow

```bash
# Step 1: Navigate to project folder
cd /Users/sayalishelke/Desktop/scein-pipeline

# Step 2: Get latest data from GitHub
./update_qgis_data.sh

# Expected output:
# Already up to date. (if no changes)
# OR
# Updating files... (if new data available)
# ✅ QGIS data updated! Latest CSV downloaded.
```

**Then in QGIS:**
1. Right-click `county_permits_for_qgis` layer
2. Click **Reload**

---

## If Update Script Fails

### Error: "Permission denied"

**Problem:** Script not executable

**Solution:**
```bash
cd /Users/sayalishelke/Desktop/scein-pipeline
chmod +x update_qgis_data.sh
./update_qgis_data.sh
```

---

### Error: "No such file or directory"

**Problem:** Script doesn't exist

**Solution - Recreate the script:**
```bash
cd /Users/sayalishelke/Desktop/scein-pipeline

# Create the update script
cat > update_qgis_data.sh << 'EOF'
#!/bin/bash

# Navigate to your project
cd ~/Desktop/scein-pipeline

# Pull latest from GitHub
git pull origin main

echo "✅ QGIS data updated! Latest CSV downloaded."
EOF

# Make it executable
chmod +x update_qgis_data.sh

# Test it
./update_qgis_data.sh
```

---

### Error: "fatal: not a git repository"

**Problem:** Git not initialized in folder

**Solution:**
```bash
cd /Users/sayalishelke/Desktop/scein-pipeline

# Check if .git folder exists
ls -la | grep .git

# If not, initialize git and connect to GitHub
git init
git remote add origin https://github.com/sayali1004/Watts_on_Water.git
git fetch origin
git checkout -b main
git branch --set-upstream-to=origin/main main
git pull origin main

# Now try the update script again
./update_qgis_data.sh
```

---

### Error: "Your local changes would be overwritten"

**Problem:** You modified files locally that conflict with GitHub

**Solution - Keep GitHub version:**
```bash
cd /Users/sayalishelke/Desktop/scein-pipeline

# Backup your local changes
mkdir backup_$(date +%Y%m%d)
cp county_permits_for_qgis.csv backup_$(date +%Y%m%d)/

# Discard local changes and get GitHub version
git reset --hard origin/main
git pull origin main

echo "✅ Reset to GitHub version. Your backup is in backup_YYYYMMDD/"
```

**Solution - Keep your local version:**
```bash
cd /Users/sayalishelke/Desktop/scein-pipeline

# Stash your changes
git stash

# Get GitHub updates
git pull origin main

# Apply your changes back (may cause conflicts)
git stash pop

# If conflicts, manually resolve and commit
```

---

## Complete QGIS Setup from Scratch

### If QGIS Project is Lost or Corrupted

**Step-by-step recreation:**

#### 1. Verify Data Files Exist

```bash
cd /Users/sayalishelke/Desktop/scein-pipeline

# Check CSV exists
ls -lh county_permits_for_qgis.csv
# Should show: ~2-3 MB file

# Check shapefile exists (look for folder or files)
ls -lh tl_2025_us_county.*
# Should show: .shp (126 MB), .shx, .dbf, .prj

# If CSV missing:
./update_qgis_data.sh

# If shapefile missing:
python export_with_propagation.py
# This downloads it automatically from US Census
```

#### 2. Open QGIS

```bash
# On Mac:
open /Applications/QGIS.app

# On Windows:
# Start → QGIS Desktop

# On Linux:
qgis
```

#### 3. Create New Project

1. **Project** → **New** (or Ctrl+N / Cmd+N)
2. Save immediately: **Project** → **Save As**
   - Location: `/Users/sayalishelke/Desktop/scein-pipeline/`
   - Name: `SCEIN_Map.qgz`
   - Click **Save**

#### 4. Load Shapefile (US Counties Map)

**Menu method:**
1. **Layer** → **Add Layer** → **Add Vector Layer**
2. Click **"..."** button
3. Navigate to: `/Users/sayalishelke/Desktop/scein-pipeline/`
4. Select: `tl_2025_us_county.shp`
5. Click **Open**
6. Click **Add**
7. Click **Close**

**Drag-and-drop method:**
1. Open Finder/Explorer
2. Navigate to `/Users/sayalishelke/Desktop/scein-pipeline/`
3. Drag `tl_2025_us_county.shp` into QGIS window

**Verify:** You should see US county map with ~3,235 counties

#### 5. Load CSV Data

**CRITICAL STEPS - Don't Skip:**

1. **Layer** → **Add Layer** → **Add Delimited Text Layer**
2. **File name:** Click **"..."**
   - Navigate to: `/Users/sayalishelke/Desktop/scein-pipeline/`
   - Select: `county_permits_for_qgis.csv`
3. **File Format:** Should auto-detect as **CSV**
4. **Record and Fields Options:**
   - ✅ **CHECK THIS BOX:** "First record has field names"
   - Number of header lines to discard: 0
5. **Geometry Definition:** **SELECT "No geometry (attribute only table)"**
   - ⚠️ THIS IS CRITICAL - Don't select any geometry option!
6. **Layer Settings:**
   - ✅ **CHECK THIS BOX:** "Detect field types"
   - ⚠️ THIS IS CRITICAL - Ensures numbers are read as numbers, not text!
7. **Sample Data:** Review to verify columns look correct
8. Click **Add**
9. Click **Close**

**Verify:** 
- Layer panel shows `county_permits_for_qgis` with table icon (📊)
- NOT a map layer icon
- Right-click → Open Attribute Table → Should show 3,229 rows

#### 6. Join Data to Map (THE CRITICAL STEP)

**Why this is important:**
The join connects county shapes (map) with data (CSV). Without it, you can't color the map by data values.

**Step-by-step:**

1. **Right-click** `tl_2025_us_county` layer (the map, not the CSV)
2. Select **Properties**
3. In left sidebar, click **"Joins"** tab

**SCREENSHOT CHECKPOINT:** You should see an empty list and buttons at bottom

4. Click the green **"+"** button (Add Join)

**Configure the join - EXACT SETTINGS:**

| Setting | Value | Why |
|---------|-------|-----|
| **Join layer** | `county_permits_for_qgis` | The data table to join |
| **Join field** | `NAME` | County name in CSV |
| **Target field** | `NAME` | County name in shapefile |
| **Cache join layer in memory** | ✅ CHECKED | Faster performance |
| **Custom field name prefix** | ❌ UNCHECKED | Cleaner field names |
| **Joined fields** | Leave default (all) | Gets all data columns |

5. Click **OK** (closes Add Join dialog)
6. Click **Apply** (applies changes but keeps Properties open)

**VERIFICATION CHECKPOINT:**

7. Still in Properties, click **"Fields"** tab (left sidebar)
8. Scroll down in the field list
9. **YOU SHOULD SEE** (if join worked):
   - Original shapefile fields (NAME, STATEFP, GEOID, etc.)
   - **NEW joined fields:**
     - `PERMIT_CNT` (or `county_permits_for_qgis_PERMIT_CNT`)
     - `INCENTV_CNT`
     - `REGULN_CNT`
     - `TOTAL_CNT`
     - `PERMIT_LST`
     - `INCENTV_LST`
     - `REGULN_LST`
     - `PERMIT_URLS`
     - `INCENTV_URLS`
     - `REGULN_URLS`

**If you DON'T see these fields:**
- Go back to Joins tab
- Remove the join (select it, click red "-")
- Try again with exact settings above
- See "Join Troubleshooting" section below

10. Click **OK** to close Properties

#### 7. Style the Map (Add Colors)

1. **Right-click** `tl_2025_us_county` → **Properties**
2. **Symbology** tab (left sidebar)
3. Top dropdown: Change from **"Single Symbol"** to **"Graduated"**

**Configure graduated symbology:**

| Setting | Value | Notes |
|---------|-------|-------|
| **Value** | `TOTAL_CNT` | Or PERMIT_CNT, INCENTV_CNT, REGULN_CNT |
| **Color ramp** | Click dropdown → Choose "Blues" or any scheme | Preview shows colors |
| **Mode** | Natural Breaks (Jenks) | Best for data distribution |
| **Classes** | 5 | Good default, adjust 3-7 as needed |

4. Click **"Classify"** button
   - You should see 5 rows appear with value ranges and colors

5. **OPTIONAL:** Adjust colors
   - Double-click any color square to change individual color
   - Or click "Color ramp" to change entire scheme

6. Click **Apply** to preview
7. If map looks good, click **OK**

**VERIFY:** Map should now be colored! Counties with more data = darker/different color

#### 8. Save Project

1. **Project** → **Save** (Ctrl+S / Cmd+S)
2. Confirm save location: `/Users/sayalishelke/Desktop/scein-pipeline/SCEIN_Map.qgz`

**DONE!** ✅

---

## Join Troubleshooting

### Problem: "Can't see TOTAL_CNT in Symbology dropdown"

**Diagnosis:** Join didn't work OR fields are text instead of numbers

**Check if join exists:**
```text
1. Right-click tl_2025_us_county → Properties
2. Joins tab
3. Do you see county_permits_for_qgis listed?
```

**If NO join listed:**
- Follow "Step 6: Join Data to Map" above exactly

**If join IS listed but fields not showing:**

```text
1. In Joins tab, select the join
2. Click red "-" to remove it
3. Click green "+" to add it again
4. CRITICAL: Make sure both "Join field" and "Target field" = NAME
5. Click OK → Apply
6. Go to Fields tab → Scroll down → Verify fields appear
```

---

### Problem: "Fields show as 'county_permits_for_qgis_TOTAL_CNT' (with prefix)"

**This is OKAY!** It still works. Use the full field name in Symbology.

**To remove prefix (Optional):**

```text
1. Right-click tl_2025_us_county → Properties → Joins
2. Select join → Click "-" to remove
3. Click "+" to add new join
4. Fill in settings same as before
5. ✅ CHECK "Custom field name prefix"
6. CRITICAL: Delete all text in the box next to it (make completely empty)
7. OK → Apply → OK
```

Now fields will be just `TOTAL_CNT` instead of `county_permits_for_qgis_TOTAL_CNT`.

---

### Problem: "Join exists, fields exist, but Symbology shows ALAND/AWATER only"

**Diagnosis:** Fields are stored as TEXT (String) instead of INTEGER (Number)

**Why:** CSV loaded without "Detect field types" checked

**Fix:**

```text
1. Remove county_permits_for_qgis layer:
   - Right-click → Remove Layer → OK

2. Re-add CSV (CAREFULLY this time):
   - Layer → Add Delimited Text Layer
   - Select county_permits_for_qgis.csv
   - Geometry: "No geometry"
   - ✅ CHECK "Detect field types" ← CRITICAL!
   - Add

3. Verify field types:
   - Right-click county_permits_for_qgis → Properties
   - Fields tab
   - Check PERMIT_CNT shows Type: Integer (NOT String)

4. Re-do the join:
   - Right-click tl_2025_us_county → Properties → Joins
   - Remove old join if exists
   - Add new join with county_permits_for_qgis

5. Try Symbology again
   - Should now see numeric fields in dropdown
```

---

## Data Type Issues

### How to Check Field Types

```text
Method 1 - In Properties:
1. Right-click county_permits_for_qgis → Properties
2. Fields tab
3. Look at "Type name" column:
   - ✅ GOOD: Integer, Integer64, Real
   - ❌ BAD: String, Text

Method 2 - In Attribute Table:
1. Right-click county_permits_for_qgis → Open Attribute Table
2. Click field header (e.g., PERMIT_CNT)
3. Values should be numbers without quotes
   - ✅ GOOD: 19, 32, 57
   - ❌ BAD: "19", "32", "57"
```

### Verify CSV File is Correct

```bash
cd /Users/sayalishelke/Desktop/scein-pipeline

# Check first 3 lines
head -3 county_permits_for_qgis.csv

# Should see:
# NAME,STATEFP,STATE_ABBR,PERMIT_CNT,INCENTV_CNT,REGULN_CNT,TOTAL_CNT,...
# Autauga,01,AL,19,32,6,57,...
# Baldwin,01,AL,19,32,6,57,...

# Numbers should NOT have quotes around them
# ✅ GOOD: ,19,32,6,57,
# ❌ BAD: ,"19","32","6","57",
```

**If CSV has quoted numbers:**

```bash
# Regenerate CSV
cd /Users/sayalishelke/Desktop/scein-pipeline
python export_with_propagation.py

# Verify it's fixed
head -3 county_permits_for_qgis.csv
```

---

## Emergency Recovery

### Scenario: Everything is broken, start fresh

**Full reset procedure:**

```bash
# Step 1: Backup current state
cd ~/Desktop
cp -r scein-pipeline scein-pipeline-backup-$(date +%Y%m%d_%H%M%S)

# Step 2: Get clean copy from GitHub
cd scein-pipeline
git fetch origin
git reset --hard origin/main
git clean -fd

# Step 3: Verify files exist
ls -lh county_permits_for_qgis.csv
ls -lh tl_2025_us_county.*

# Step 4: If shapefile missing, download it
python export_with_propagation.py

# Step 5: Open QGIS and follow "Complete QGIS Setup from Scratch" above
```

---

### Scenario: Can't connect to GitHub

**Manual CSV update:**

```bash
# Step 1: Go to GitHub in browser
# https://github.com/sayali1004/Watts_on_Water

# Step 2: Click on county_permits_for_qgis.csv

# Step 3: Click "Download" button (or Raw, then Save As)

# Step 4: Save to:
# /Users/sayalishelke/Desktop/scein-pipeline/county_permits_for_qgis.csv
# (Replace existing file)

# Step 5: In QGIS, reload:
# Right-click county_permits_for_qgis → Reload
```

---

### Scenario: Shapefile corrupted or missing

**Download fresh from US Census:**

```bash
cd /Users/sayalishelke/Desktop/scein-pipeline

# Download
curl -L "https://www2.census.gov/geo/tiger/TIGER2025/COUNTY/tl_2025_us_county.zip" -o tl_2025_us_county.zip

# Extract
unzip tl_2025_us_county.zip

# Clean up
rm tl_2025_us_county.zip

# Verify
ls -lh tl_2025_us_county.*
# Should see: .shp (126MB), .shx, .dbf, .prj

echo "✅ Shapefile downloaded"
```

---

## Verification Commands

### Check if Git is working

```bash
cd /Users/sayalishelke/Desktop/scein-pipeline

# Check Git status
git status

# Expected: "On branch main" and "Your branch is up to date"

# Check remote connection
git remote -v

# Expected: 
# origin  https://github.com/sayali1004/Watts_on_Water.git (fetch)
# origin  https://github.com/sayali1004/Watts_on_Water.git (push)
```

---

### Check file integrity

```bash
cd /Users/sayalishelke/Desktop/scein-pipeline

# Count rows in CSV (should be 3230: 1 header + 3229 counties)
wc -l county_permits_for_qgis.csv
# Expected: 3230 county_permits_for_qgis.csv

# Check CSV file size (should be 2-3 MB)
ls -lh county_permits_for_qgis.csv
# Expected: ~2.8M

# Check shapefile size (should be ~126 MB)
ls -lh tl_2025_us_county.shp
# Expected: 126M

# Verify CSV has correct columns
head -1 county_permits_for_qgis.csv
# Expected: NAME,STATEFP,STATE_ABBR,PERMIT_CNT,INCENTV_CNT,REGULN_CNT,TOTAL_CNT,...
```

---

### Check Python environment

```bash
# Check Python version
python --version
# Expected: Python 3.9+ or Python 3.11+

# Check required packages
pip list | grep -E "(pandas|geopandas|supabase)"
# Expected:
# pandas          2.x.x
# geopandas       0.x.x  
# supabase        2.x.x

# If missing packages:
pip install pandas geopandas supabase pyogrio --break-system-packages
```

---

### Test export script manually

```bash
cd /Users/sayalishelke/Desktop/scein-pipeline

# Run export (should take 30-60 seconds)
python export_with_propagation.py

# Check output
# Expected to see:
# Loading counties from shapefile...
# ✅ Loaded 3235 counties from 56 states
# Fetching data from Supabase...
# Fetched 640 records
# 📊 Data categorization:
#    County-specific: 12
#    State-level: 191 across 9 states
#    Federal: 53
#    Unknown: 384
# ✅ Exported 3229 counties to county_permits_for_qgis.csv
```

---

## Common Error Messages & Fixes

### Error: "ModuleNotFoundError: No module named 'geopandas'"

```bash
pip install geopandas pyogrio --break-system-packages
```

---

### Error: "FileNotFoundError: tl_2025_us_county.shp"

```bash
# Shapefile missing - download it
python export_with_propagation.py
# Script will auto-download from US Census
```

---

### Error: "Invalid URL" when connecting to Supabase

**Problem:** Credentials not set or wrong format

**Check script:**
```bash
cd /Users/sayalishelke/Desktop/scein-pipeline
grep "SUPABASE_URL" export_with_propagation.py

# Should show your actual URL, not "YOUR_SUPABASE_URL"
```

**Fix if needed:**
```bash
# Edit the file
code export_with_propagation.py
# or
nano export_with_propagation.py

# Find these lines (around line 35):
# SUPABASE_URL = os.getenv('SUPABASE_URL')
# SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Replace with:
# SUPABASE_URL = 'https://yourproject.supabase.co'
# SUPABASE_KEY = 'your-actual-key-here'

# Save and run again
python export_with_propagation.py
```

---

## Quick Command Cheat Sheet

```bash
# Daily update
cd /Users/sayalishelke/Desktop/scein-pipeline && ./update_qgis_data.sh

# Force fresh download from GitHub
cd /Users/sayalishelke/Desktop/scein-pipeline && git reset --hard origin/main && git pull

# Regenerate CSV manually
cd /Users/sayalishelke/Desktop/scein-pipeline && python export_with_propagation.py

# Check file status
cd /Users/sayalishelke/Desktop/scein-pipeline && ls -lh *.csv *.shp

# Verify CSV row count
cd /Users/sayalishelke/Desktop/scein-pipeline && wc -l county_permits_for_qgis.csv

# View CSV headers
cd /Users/sayalishelke/Desktop/scein-pipeline && head -1 county_permits_for_qgis.csv
```

---

## Support & Resources

**GitHub Repository:**
https://github.com/sayali1004/Watts_on_Water

**Check Automation Status:**
https://github.com/sayali1004/Watts_on_Water/actions

**QGIS Documentation:**
https://docs.qgis.org/

**File Locations:**
- Project: `/Users/sayalishelke/Desktop/scein-pipeline/`
- Data: `county_permits_for_qgis.csv`
- Map: `tl_2025_us_county.shp`
- Project file: `SCEIN_Map.qgz`

---

**Last Updated:** April 13, 2026
**Version:** 1.0
