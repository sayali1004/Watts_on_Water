# SCEIN Fellowship Data Pipeline
## Complete User Handbook

**Version 1.0 | April 2026**

---

## 📖 Table of Contents

1. [What This System Does](#what-this-system-does)
2. [How It Works (Simple Explanation)](#how-it-works)
3. [What You'll Need](#what-youll-need)
4. [Initial Setup (One-Time)](#initial-setup)
5. [Daily Workflow](#daily-workflow)
6. [Creating Maps in QGIS](#creating-maps-in-qgis)
7. [Troubleshooting](#troubleshooting)
8. [Technical Details (For IT)](#technical-details)
9. [FAQ](#faq)

---

## What This System Does

This automated system:
- **Collects** permit, incentive, and regulation data from 640+ websites
- **Organizes** data by county, state, and federal level
- **Distributes** state and federal data to all relevant counties
- **Creates** ready-to-use map files for QGIS visualization
- **Updates** automatically every day

**End Result:** You can create maps showing permits, incentives, and regulations for all 3,235 US counties with just a few clicks!

---

## How It Works

Think of it like a pipeline:

```
Google Sheets (your data source)
    ↓ (every 30 minutes)
Automated Scraper (collects data from websites)
    ↓
Database (stores everything)
    ↓ (every day at 9 AM)
CSV File (ready for maps)
    ↓
Your Computer (makes maps in QGIS)
```

**The good news:** Steps 1-4 happen automatically! You only need to do step 5.

---

## What You'll Need

### Software (Free)
- **QGIS Desktop** - Download from https://qgis.org/download/
  - Version 3.28 or newer
  - Works on Mac, Windows, Linux

### Files (Already on this computer)
Location: `/Users/sayalishelke/Desktop/scein-pipeline/`

You'll use:
- `county_permits_for_qgis.csv` - The data file (auto-updated daily)
- `tl_2025_us_county.shp` - US county map (+ 3 other files: .shx, .dbf, .prj)
- `update_qgis_data.sh` - Script to get fresh data
- `SCEIN_Map.qgz` - Your saved QGIS project (once you create it)

### Access You'll Need
- This computer (where files are located)
- Internet connection (to download updates)

---

## Initial Setup (One-Time)

### Step 1: Install QGIS

1. Go to https://qgis.org/download/
2. Download the installer for your operating system
3. Run the installer
4. Follow the on-screen instructions
5. Open QGIS to verify it works

**Time needed:** 10-15 minutes

---

### Step 2: Load the Map for the First Time

#### A. Open QGIS
- Find QGIS in your Applications folder
- Double-click to open

#### B. Load the US County Shapefile

1. Click **Layer** menu → **Add Layer** → **Add Vector Layer**
2. Click the **"..."** button next to "Vector Dataset(s)"
3. Navigate to: `/Users/sayalishelke/Desktop/scein-pipeline/`
4. Look for files starting with `tl_2025_us_county`
5. Select: `tl_2025_us_county.shp`
6. Click **"Add"**
7. Click **"Close"**

**You should now see a map of all US counties!**

#### C. Load the Data File (CSV)

1. Click **Layer** menu → **Add Layer** → **Add Delimited Text Layer**
2. Click the **"..."** button next to "File name"
3. Navigate to: `/Users/sayalishelke/Desktop/scein-pipeline/`
4. Select: `county_permits_for_qgis.csv`
5. **IMPORTANT:** Scroll down to "Geometry Definition"
6. Select **"No geometry (attribute only table)"**
7. ✅ Check the box: **"Detect field types"**
8. Click **"Add"**
9. Click **"Close"**

**You should now see both layers in the left panel:**
- `tl_2025_us_county` (the map)
- `county_permits_for_qgis` (the data - looks like a table icon)

#### D. Join the Map and Data Together

This connects the county shapes with the permit/incentive data.

1. **Right-click** on `tl_2025_us_county` in the left panel
2. Click **"Properties"**
3. In the left sidebar, click **"Joins"**
4. Click the green **"+"** button at the bottom
5. Fill in these settings:
   - **Join layer:** `county_permits_for_qgis`
   - **Join field:** `NAME`
   - **Target field:** `NAME`
   - ✅ Check: **"Cache join layer in memory"**
   - ❌ Uncheck: **"Custom field name prefix"** (or leave it blank)
6. Click **"OK"**
7. Click **"Apply"** (don't close yet!)

#### E. Verify the Join Worked

1. Still in Properties, click **"Fields"** tab (in left sidebar)
2. Scroll down in the list
3. You should see new fields like:
   - `PERMIT_CNT`
   - `INCENTV_CNT`
   - `REGULN_CNT`
   - `TOTAL_CNT`

**If you see these, the join worked!** ✅

8. Click **"OK"** to close Properties

#### F. Color the Map

1. **Right-click** `tl_2025_us_county` → **Properties**
2. Click **"Symbology"** in left sidebar
3. At the top, change the dropdown from **"Single Symbol"** to **"Graduated"**
4. **Value:** Select `TOTAL_CNT` (or `PERMIT_CNT`, `INCENTV_CNT`, `REGULN_CNT`)
5. **Color ramp:** Click the dropdown and choose a color scheme
   - **Blues** - Light to dark blue
   - **Reds** - Light to dark red
   - **RdYlGn** - Red-Yellow-Green
6. **Mode:** Select **"Natural Breaks (Jenks)"**
7. Click the **"Classify"** button
8. Click **"OK"**

**Your map is now colored by data!** 🎨

Counties with more permits/incentives will be darker.

#### G. Save Your Project

1. Click **Project** menu → **Save As**
2. Navigate to: `/Users/sayalishelke/Desktop/scein-pipeline/`
3. File name: `SCEIN_Map.qgz`
4. Click **"Save"**

**Setup complete!** 🎉

---

## Daily Workflow

### Getting Fresh Data (5 seconds)

The data updates automatically every day at 9 AM. To get the latest:

1. **Open Terminal** (or Command Prompt on Windows)
2. Type these commands:
   ```bash
   cd /Users/sayalishelke/Desktop/scein-pipeline
   ./update_qgis_data.sh
   ```
3. Press **Enter**
4. You'll see: "✅ QGIS data updated!"

**That's it!** The latest data is now on your computer.

---

### Opening Your Map

1. **Open QGIS**
2. Click **Project** menu → **Open Recent**
3. Select **"SCEIN_Map.qgz"**

**OR**

1. Open QGIS
2. Click **Project** → **Open**
3. Navigate to: `/Users/sayalishelke/Desktop/scein-pipeline/`
4. Select: `SCEIN_Map.qgz`
5. Click **"Open"**

---

### Refreshing the Map with New Data

After running `./update_qgis_data.sh`:

1. In QGIS, look at the **Layers** panel (left side)
2. **Right-click** on `county_permits_for_qgis`
3. Click **"Reload"**

**Your map now shows the latest data!**

---

## Creating Maps in QGIS

### Viewing Different Data Types

You can create separate maps for:
- **Permits only**
- **Incentives only**
- **Regulations only**
- **Total (all combined)**

**How to switch:**

1. **Right-click** `tl_2025_us_county` → **Properties**
2. **Symbology** tab
3. **Value:** Change the dropdown to:
   - `PERMIT_CNT` - Shows permits
   - `INCENTV_CNT` - Shows incentives
   - `REGULN_CNT` - Shows regulations
   - `TOTAL_CNT` - Shows everything
4. Click **"Classify"**
5. Click **"OK"**

---

### Changing Colors

1. **Right-click** `tl_2025_us_county` → **Properties**
2. **Symbology** tab
3. Click the **Color ramp** dropdown
4. Choose a different color scheme
5. Click **"Classify"**
6. Click **"OK"**

---

### Adding County Labels

1. **Right-click** `tl_2025_us_county` → **Properties**
2. **Labels** tab (in left sidebar)
3. Change dropdown from **"No Labels"** to **"Single Labels"**
4. **Value:** Select `NAME`
5. Adjust **Font size:** 8-10pt works well
6. Click **"OK"**

**County names now appear on the map!**

---

### Adding Hover Popups (Map Tips)

Show information when you hover over a county:

1. **Right-click** `tl_2025_us_county` → **Properties**
2. **Display** tab (or "Map Tips" in some versions)
3. In the **HTML Map Tip** box, paste this:

```html
<h3>[% "NAME" %] County, [% "STATE_ABBR" %]</h3>
<b>Total Items:</b> [% "TOTAL_CNT" %]<br>
<b>Permits:</b> [% "PERMIT_CNT" %]<br>
<b>Incentives:</b> [% "INCENTV_CNT" %]<br>
<b>Regulations:</b> [% "REGULN_CNT" %]<br>
<hr>
<b>Sample Permits:</b><br>
[% "PERMIT_LST" %]<br>
<b>Sample Incentives:</b><br>
[% "INCENTV_LST" %]<br>
<b>Sample Regulations:</b><br>
[% "REGULN_LST" %]
```

4. Click **"OK"**
5. **Enable Map Tips:** Click **View** menu → **Show Map Tips** (or press Ctrl+I / Cmd+I)

**Now hover over any county to see its data!**

---

### Exporting a Map Image

To share your map:

1. Click **Project** menu → **New Print Layout**
2. Give it a name (e.g., "US Permits Map")
3. Click **OK**
4. Click **Add Item** → **Add Map**
5. Drag a rectangle on the page
6. Your map appears!

**Add a title:**
1. **Add Item** → **Add Label**
2. Draw a box at the top
3. In the right panel, type your title in **Main Properties**

**Add a legend:**
1. **Add Item** → **Add Legend**
2. Draw a box on the side
3. The legend appears automatically

**Export:**
1. **Layout** menu → **Export as Image**
2. Choose location and filename
3. Click **"Save"**

**You now have a PNG/JPG image to share!**

---

## Troubleshooting

### Problem: "update_qgis_data.sh: command not found"

**Solution:**
```bash
cd /Users/sayalishelke/Desktop/scein-pipeline
chmod +x update_qgis_data.sh
./update_qgis_data.sh
```

---

### Problem: Map is all gray / no colors

**Cause:** The join didn't work or data didn't load.

**Solution:**
1. Check that `county_permits_for_qgis.csv` exists in the folder
2. Remove and re-add the CSV layer
3. Make sure you checked **"Detect field types"** when adding CSV
4. Re-do the join (see Initial Setup → Step 2D)

---

### Problem: Can't see TOTAL_CNT in Symbology dropdown

**Cause:** Fields are loaded as text instead of numbers.

**Solution:**
1. Remove the CSV layer
2. Re-add it
3. **IMPORTANT:** ✅ Check **"Detect field types"** before clicking Add
4. Re-do the join

---

### Problem: Data looks old / numbers haven't changed

**Solution:**
```bash
# Get fresh data
cd /Users/sayalishelke/Desktop/scein-pipeline
./update_qgis_data.sh

# Then in QGIS:
# Right-click county_permits_for_qgis → Reload
```

---

### Problem: QGIS crashes or freezes

**Solution:**
1. Save your work: **Project → Save**
2. Restart QGIS
3. **Project → Open Recent → SCEIN_Map.qgz**

If it keeps crashing:
- Check you have at least 4GB of RAM available
- Close other programs
- Try a simpler color scheme (fewer classes)

---

## Technical Details (For IT)

### System Architecture

**Components:**
- **Data Source:** Google Sheets (640 records)
- **Scraper:** Python script, runs on GitHub Actions
- **Database:** Supabase (PostgreSQL)
- **Export:** Python script, generates CSV
- **Visualization:** QGIS Desktop

**Automation:**
- GitHub Actions runs scraper every 30 min (8AM-6PM UTC, weekdays)
- GitHub Actions runs export daily at 9 AM UTC (weekdays)
- CSV committed back to repository automatically

**Data Flow:**
1. Google Sheets → Download (GitHub Actions)
2. Scraper extracts URLs → Web scraping → Clean data
3. Save to Supabase (permits_data table)
4. Export script:
   - Categorizes: county-specific, state-level, federal
   - Distributes state data to all counties in state
   - Distributes federal data to all US counties
5. Generates CSV with aggregated counts
6. User pulls CSV → Joins in QGIS → Creates maps

### File Locations

**On This Computer:**
- Project folder: `/Users/sayalishelke/Desktop/scein-pipeline/`
- Shapefile: `tl_2025_us_county.shp` (+ .shx, .dbf, .prj)
- Data CSV: `county_permits_for_qgis.csv` (auto-updated)
- Update script: `update_qgis_data.sh`
- QGIS project: `SCEIN_Map.qgz`

**On GitHub:**
- Repository: https://github.com/sayali1004/Watts_on_Water
- Workflows: `.github/workflows/`
- Scripts: `scraper.py`, `export_with_propagation.py`

**Database:**
- Supabase project (credentials in GitHub Secrets)
- Table: `permits_data`
- ~640 records

### Data Schema

**CSV Columns:**
- `NAME` - County name (join key)
- `STATEFP` - State FIPS code
- `STATE_ABBR` - State abbreviation (CA, TX, etc.)
- `PERMIT_CNT` - Number of permits (integer)
- `INCENTV_CNT` - Number of incentives (integer)
- `REGULN_CNT` - Number of regulations (integer)
- `TOTAL_CNT` - Total count (integer)
- `PERMIT_LST` - Sample permits (text, first 5)
- `INCENTV_LST` - Sample incentives (text, first 5)
- `REGULN_LST` - Sample regulations (text, first 5)
- `PERMIT_URLS` - Permit URLs (text, first 3, semicolon-separated)
- `INCENTV_URLS` - Incentive URLs (text, first 3)
- `REGULN_URLS` - Regulation URLs (text, first 3)

**Shapefile:**
- Source: US Census TIGER/Line 2025
- Features: 3,235 counties
- Key field: `NAME` (county name)

### Scripts

**update_qgis_data.sh:**
```bash
#!/bin/bash
cd ~/Desktop/scein-pipeline
git pull origin main
echo "✅ QGIS data updated!"
```

**export_with_propagation.py:**
- Fetches data from Supabase
- Categorizes by scope (county/state/federal)
- Distributes accordingly
- Exports to CSV

### Maintenance

**Weekly:**
- Check GitHub Actions for failures
- Verify CSV file size (should be ~2-3 MB)

**Monthly:**
- Verify data counts match expectations
- Check for new states/counties in source data

**As Needed:**
- Update Google Sheets URL if changed
- Update Supabase credentials if rotated
- Re-download shapefile if Census updates

---

## FAQ

### How often does data update?

**Automatically:**
- Scraper runs every 30 minutes (business days, 8AM-6PM)
- CSV export runs daily at 9 AM
- CSV is available on this computer after running `./update_qgis_data.sh`

**You control:**
- When you run the update script
- When you reload the map in QGIS

---

### Can I work offline?

**Yes!** Once you have the data files, QGIS works completely offline.

**BUT:** To get fresh data, you need internet to run `./update_qgis_data.sh`

---

### What if I accidentally delete a file?

**Don't panic!**

**For the CSV:**
```bash
cd /Users/sayalishelke/Desktop/scein-pipeline
./update_qgis_data.sh
```
This re-downloads it from GitHub.

**For the shapefile:**
It's backed up in GitHub. Contact IT to restore it.

**For your QGIS project:**
You'll need to recreate it following "Initial Setup" above. Only takes 10 minutes!

---

### Can multiple people use this?

**Yes!** Each person needs:
1. QGIS installed on their computer
2. Access to this project folder (or a copy)
3. To run `./update_qgis_data.sh` to get data

**Everyone sees the same data** because it comes from the same source.

---

### How do I share my map with someone?

**Option 1: Export as image**
- Follow "Exporting a Map Image" above
- Share the PNG/JPG file

**Option 2: Share QGIS project**
- Copy the entire `/scein-pipeline/` folder
- Give to colleague
- They open `SCEIN_Map.qgz` in QGIS

**Option 3: Print**
- In Print Layout, click **Layout → Print**

---

### What happens if the automation breaks?

**You can still work!**

The last CSV file is saved locally. You can keep using it until IT fixes the automation.

**To check automation status:**
- Go to: https://github.com/sayali1004/Watts_on_Water/actions
- Look for green checkmarks (working) or red X's (broken)

---

### Where did this data come from originally?

**Source:** Google Sheets maintained by SCEIN Fellowship team

**Contains:** 640 URLs to permits, incentives, and regulations

**Updates:** Manual updates to Google Sheets trigger automatic re-scraping

---

### Who do I contact for help?

**For map/visualization questions:**
- [Your Name/Team]

**For technical/automation issues:**
- IT Department
- GitHub repository: https://github.com/sayali1004/Watts_on_Water

**For QGIS help:**
- QGIS Documentation: https://docs.qgis.org/
- QGIS Tutorials: https://www.qgistutorials.com/

---

## Quick Reference Card

**🔄 Get Fresh Data:**
```bash
cd /Users/sayalishelke/Desktop/scein-pipeline
./update_qgis_data.sh
```

**🗺️ Open Map:**
- Open QGIS
- Project → Open Recent → SCEIN_Map.qgz

**♻️ Reload Data:**
- Right-click `county_permits_for_qgis` → Reload

**🎨 Change Colors:**
- Right-click `tl_2025_us_county` → Properties → Symbology

**📊 Switch Data:**
- Symbology → Value → Pick: PERMIT_CNT, INCENTV_CNT, REGULN_CNT, or TOTAL_CNT

**💾 Save:**
- Project → Save (Ctrl+S / Cmd+S)

**📤 Export:**
- Project → New Print Layout → Layout → Export as Image

---

## Version History

**v1.0 - April 2026**
- Initial handbook
- Complete setup instructions
- Daily workflow documented
- Troubleshooting guide added

---

**End of Handbook**

For the latest version of this document, check:
`/Users/sayalishelke/Desktop/scein-pipeline/USER_HANDBOOK.md`
