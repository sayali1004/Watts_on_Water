# SCEIN Fellowship — Permits, Incentives & Regulations Pipeline
## Your Complete Weekly Auto-Refresh Setup

---

## 📁 Files in This Folder

| File | Purpose |
|---|---|
| `scraper.py` | Main Python scraper — reads Excel, scrapes all URLs, outputs CSV |
| `run_scraper.bat` | Double-click to run the scraper manually |
| `setup_task_scheduler.bat` | One-time setup — schedules weekly auto-run every Monday 8AM |
| `scraped_data.csv` | **The live dataset** — load this into QGIS |
| `QGIS_Setup_Guide.md` | Step-by-step QGIS connection instructions |
| `scraper.log` | Auto-generated log file (created after first run) |

---

## 🚀 Getting Started (Do This Once)

### 1. Install Python
Download from: https://www.python.org/downloads/
✅ During install, check **"Add Python to PATH"**

### 2. Put Your Excel File Here
Copy `SCEIN_Fellowship_Data_Tracker_Google_Sheets.xlsx` into this same folder.

### 3. Run the Scraper Once
Double-click `run_scraper.bat`
- It installs all required libraries automatically
- Scrapes all 80 URLs
- Updates `scraped_data.csv`
- Takes ~5-10 minutes

### 4. Set Up Weekly Auto-Refresh
Right-click `setup_task_scheduler.bat` → **Run as Administrator**
- This sets up Windows Task Scheduler
- Runs every Monday at 8:00 AM automatically

### 5. Connect to QGIS
Follow the instructions in `QGIS_Setup_Guide.md`

---

## 📊 What the Dataset Contains

**80 records** across:
- **69 Permits** — California county building/solar permit portals
- **11 Incentives** — State and federal solar incentive programs
- **0 Regulations** — (add links to your Excel to populate)

**Key fields for QGIS mapping:**
- `latitude` / `longitude` — pre-geocoded by county ✅
- `type` — Permit / Incentive / Regulation
- `county` / `state` — location info
- `page_live` — is the URL still active?
- `dates_found` — any dates scraped from the page
- `last_scraped` — when was this last refreshed?

---

## 🔄 Weekly Workflow (After Setup)

```
Every Monday 8AM
      ↓
Task Scheduler runs scraper.py
      ↓
scraped_data.csv updated with fresh data
      ↓
QGIS auto-reloads the layer
      ↓
Your map shows fresh data 🗺️
```

---

## ❓ Need Help?

Check `scraper.log` for detailed error messages after each run.
