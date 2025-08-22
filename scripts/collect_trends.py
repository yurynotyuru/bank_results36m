import os
import time
import json
import math
import logging
from datetime import datetime, timezone
from typing import List, Dict

import pandas as pd
from pytrends.request import TrendReq
import yaml

from scripts.utils.countries import COUNTRIES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("collect_trends")

CONFIG_PATH = "config/events.yaml"
OUTPUT_DIR = "output"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "google_trends_36m.csv")

def load_config(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def chunked(seq: List[str], size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i+size]

def init_pytrends(hl: str, tz: int) -> TrendReq:
    return TrendReq(hl=hl, tz=tz, timeout=(10, 25), retries=0, backoff_factor=0)

def fetch_batch(pytrends: TrendReq, keywords: List[str], timeframe: str, geo: str):
    for attempt in range(1, 5):
        try:
            pytrends.build_payload(
                kw_list=keywords,
                timeframe=timeframe,
                geo=geo,
                cat=0,
                gprop=""
            )
            df = pytrends.interest_over_time()
            if df.empty:
                logger.warning(f"No data returned for {geo} {keywords}")
                return pd.DataFrame()
            if "isPartial" in df.columns:
                df = df.drop(columns=["isPartial"])
            return df
        except Exception as e:
            wait = attempt * 2
            logger.warning(f"Attempt {attempt} failed for geo={geo} kws={keywords}: {e}. Retry in {wait}s")
            time.sleep(wait)
    logger.error(f"Giving up on geo={geo} kws={keywords}")
    return pd.DataFrame()

def collect(config: Dict) -> pd.DataFrame:
    brands = config["brands"]
    timeframe = config["timeframe"]
    hl = config.get("hl", "en-US")
    tz = config.get("tz", 0)
    pytrends = init_pytrends(hl=hl, tz=tz)

    records = []
    total_batches = len(COUNTRIES) * math.ceil(len(brands)/5)
    batch_index = 0

    for country in COUNTRIES:
        logger.info(f"Country {country} start")
        for kws in chunked(brands, 5):
            batch_index += 1
            df = fetch_batch(pytrends, kws, timeframe=timeframe, geo=country)
            if not df.empty:
                df_reset = df.reset_index()
                for _, row in df_reset.iterrows():
                    date_val = row['date']
                    for kw in kws:
                        value = row.get(kw)
                        records.append({
                            "date": date_val,
                            "brand": kw,
                            "country_iso2": country,
                            "value": int(value) if pd.notnull(value) else None
                        })
            time.sleep(1.2)
            if batch_index % 20 == 0:
                logger.info(f"Progress: {batch_index}/{total_batches} ({batch_index/total_batches:.1%})")

    df_all = pd.DataFrame(records)
    if df_all.empty:
        logger.warning("Final DataFrame is empty.")
    else:
        df_all = df_all.sort_values(["brand", "country_iso2", "date"]).reset_index(drop=True)
    return df_all

def write_csv(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df_out = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_out["date"]):
        df_out["date"] = pd.to_datetime(df_out["date"])
    df_out["date"] = df_out["date"].dt.strftime("%Y-%m-%d")
    df_out.to_csv(path, index=False, encoding="utf-8")
    logger.info(f"CSV written: {path} (rows={len(df_out)})")

def upload_to_sheets(df: pd.DataFrame):
    creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    tab_name = os.getenv("GOOGLE_SHEETS_TAB", "Trends_36m")
    write_mode = os.getenv("GOOGLE_SHEETS_WRITE_MODE", "replace").lower()

    if not creds_json or not spreadsheet_id:
        logger.info("Sheets credentials or spreadsheet ID not provided — skipping Sheets upload.")
        return

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        logger.error("gspread / google-auth not installed. Skipping Sheets upload.")
        return

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    info = json.loads(creds_json)
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(spreadsheet_id)

    headers = ["date", "brand", "country_iso2", "value"]
    df_sheet = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_sheet["date"]):
        df_sheet["date"] = pd.to_datetime(df_sheet["date"])
    df_sheet["date"] = df_sheet["date"].dt.strftime("%Y-%m-%d")
    df_sheet = df_sheet[headers]

    try:
        worksheet = sh.worksheet(tab_name)
    except Exception:
        worksheet = sh.add_worksheet(title=tab_name, rows="100", cols=str(len(headers)))

    if write_mode == "replace":
        worksheet.clear()
        values = [headers] + df_sheet.values.tolist()
    else:
        existing = worksheet.get_all_values()
        if existing and existing[0] == headers:
            values = df_sheet.values.tolist()
        else:
            values = [headers] + df_sheet.values.tolist()

    CHUNK = 15000
    start_row = 1
    cursor = start_row
    for i in range(0, len(values), CHUNK):
        chunk = values[i:i+CHUNK]
        end_row = cursor + len(chunk) - 1
        cell_range = f"A{cursor}:D{end_row}"
        worksheet.update(cell_range, chunk, value_input_option="RAW")
        cursor = end_row + 1

    logger.info(f"Uploaded {len(df_sheet)} rows to Google Sheets tab '{tab_name}' (mode={write_mode}).")

def main():
    start = datetime.now(timezone.utc)
    logger.info("Starting Google Trends collection (36m).")
    config = load_config(CONFIG_PATH)
    df = collect(config)
    write_csv(df, OUTPUT_CSV)
    upload_to_sheets(df)
    end = datetime.now(timezone.utc)
    logger.info(f"Done in {(end - start).total_seconds():.1f}s. Rows: {len(df)}")

if __name__ == "__main__":
    main()