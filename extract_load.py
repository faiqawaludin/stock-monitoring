import os
from datetime import datetime, timezone
import pandas as pd
import requests
from google.cloud import bigquery

API_KEY = os.environ["MARKETSTACK_API_KEY"].strip()
PROJECT_ID = os.environ["GCP_PROJECT_ID"].strip()
SYMBOLS = "AAPL,GOOGL,MSFT,NVDA"
TABLE_ID = f"{PROJECT_ID}.raw_stocks.eod_prices"


def fetch_stock_eod():
    # 1. Coba endpoint Marketstack v2 (untuk API Key dari marketstack.com)
    res_v2 = requests.get(
        "https://api.marketstack.com/v2/eod",
        params={"access_key": API_KEY, "symbols": SYMBOLS, "limit": 100},
        timeout=20,
    )
    if res_v2.ok:
        payload = res_v2.json()
    else:
        # 2. Fallback ke gateway APILayer tanpa /v1 (untuk API Key dari apilayer.com)
        res_apilayer = requests.get(
            "https://api.apilayer.com/marketstack/eod",
            headers={"apikey": API_KEY},
            params={"symbols": SYMBOLS, "limit": 100},
            timeout=20,
        )
        if res_apilayer.ok:
            payload = res_apilayer.json()
        else:
            raise RuntimeError(
                f"Autentikasi API gagal (panjang MARKETSTACK_API_KEY={len(API_KEY)} karakter).\n"
                f"- Marketstack v2 ({res_v2.status_code}): {res_v2.text}\n"
                f"- APILayer ({res_apilayer.status_code}): {res_apilayer.text}"
            )

    if "data" not in payload or not payload["data"]:
        raise ValueError(f"Data kosong atau format tidak sesuai: {payload}")

    df = pd.DataFrame(payload["data"])
    cols = ["symbol", "exchange", "date", "open", "high", "low", "close", "volume"]
    df = df[cols].copy()
    df["ingested_at"] = datetime.now(timezone.utc)
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
