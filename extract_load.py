import os
from datetime import UTC, datetime

import pandas as pd
import requests
from google.cloud import bigquery

API_KEY = os.environ["MARKETSTACK_API_KEY"].strip()
PROJECT_ID = os.environ["GCP_PROJECT_ID"].strip()
SYMBOLS = "AAPL,GOOGL,MSFT,NVDA"
TABLE_ID = f"{PROJECT_ID}.raw_stock.eod_prices"


def fetch_stock_eod():
    url = "https://api.apilayer.net/marketstack/v2/eod"
    params = {
        "access_key": API_KEY,
        "symbols": SYMBOLS,
        "limit": 100,
    }
    res = requests.get(url, params=params, timeout=20)
    if not res.ok:
        raise RuntimeError(f"API Error {res.status_code}: {res.text}")
    payload = res.json()

    if "data" not in payload or not payload["data"]:
        raise ValueError(f"Data kosong atau format tidak sesuai: {payload}")

    df = pd.DataFrame(payload["data"])
    cols = ["symbol", "exchange", "date", "open", "high", "low", "close", "volume"]
    for col in cols:
        if col not in df.columns:
            df[col] = None

    df = df[cols].copy()
    df["ingested_at"] = datetime.now(UTC)
    return df


def load_to_bigquery(df):
    client = bigquery.Client(project=PROJECT_ID)
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True,
    )
    job = client.load_table_from_dataframe(df, TABLE_ID, job_config=job_config)
    job.result()
    print(f"Sukses memuat {len(df)} baris ke {TABLE_ID}")


if __name__ == "__main__":
    stock_df = fetch_stock_eod()
    load_to_bigquery(stock_df)
