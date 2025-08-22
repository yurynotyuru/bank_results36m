# Google Trends 36M Collection

Collects Google Trends interest for defined banking brands across countries (excluding RU, UA, BY, AM, AZ, KZ, KG, TJ, TM, UZ — Moldova (MD) kept) over the last 36 months (`today 36-m`).

Outputs:
- CSV: `output/google_trends_36m.csv`
- Optional Google Sheets tab: `Trends_36m` (replace by default)

## Run locally
```bash
pip install -r requirements.txt
export GOOGLE_SHEETS_CREDENTIALS='{"type":"service_account", ...}'
export GOOGLE_SHEETS_SPREADSHEET_ID=1swAbeQOnaY7Yw4G4afGajvzNdS0yUA5sUk4vChcTI74
python scripts/collect_trends.py
```

## GitHub Actions
Triggered manually or via weekly cron (Monday 06:00 UTC). Produces artifact `google_trends_36m`.

## Columns
`date` (YYYY-MM-DD), `brand`, `country_iso2`, `value` (0–100 relative interest)