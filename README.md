cron command to refresh the dataset every Monday, at 8 AM, run this on your personal PC, with all the environment setup as it is, 
and then run this command on your terminal/bash.

command 1 : crontab -l
```
```
command 2 : 0 8 * * 1 cd '/Users/sayalishelke/desktop/Watts_on_Water/scein_pipeline' && python3 scraper.py >> scraper.log 2>&1

Cron schedule format : 
```
It's the cron schedule format. Each number/symbol means something:
0 8 * * 1
│ │ │ │ │
│ │ │ │ └── Day of week (1 = Monday)
│ │ │ └──── Month (* = every month)
│ │ └────── Day of month (* = every day)
│ └──────── Hour (8 = 8AM)
└────────── Minute (0 = at :00)
```

✅ Scraper — reads Excel, scrapes URLs
✅ Cron — runs every Monday 8AM automatically
✅ CSV — updates weekly
✅ QGIS — reloads every hour, map stays fresh
