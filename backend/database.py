import sqlite3
from pathlib import Path
import pandas as pd

REQUIRED = [
"instrument_key","symbol","timestamp","open","high","low","close","volume",
"rsi","cci","adx","macd_line","macd_signal","macd_histogram","vwap",
"prevhigh","prevlow","ema_close_9","bb_upper","bb_middle","bb_lower",
"pivot","pivot_r1","pivot_r2","pivot_r3","pivot_s1","pivot_s2","pivot_s3",
"ma_20","ma_50","ma_200","virgin_cpr"
]


def qi(name):
    return '"' + str(name).replace('"','""') + '"'

def connect(path):
    return sqlite3.connect(
        f"file:{Path(path).resolve()}?mode=ro", uri=True, timeout=10
    )

def load(path, table):
    with connect(path) as con:
        cols = {r[1] for r in con.execute(f"PRAGMA table_info({qi(table)})")}
        if not cols:
            raise RuntimeError(f"Table '{table}' not found.")
        missing = set(REQUIRED) - cols
        if missing:
            raise RuntimeError("Missing columns: " + ", ".join(sorted(missing)))

        return pd.read_sql_query(f"""
        SELECT {",".join(qi(c) for c in REQUIRED)}
        FROM {qi(table)}
        """, con)

def prepare(df, timezone):
    if df.empty:
        return df
    df = df.copy()
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], errors="coerce"
    )
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize(timezone)
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert(timezone)
    nums = [c for c in REQUIRED if c not in
            ["instrument_key","symbol","timestamp","virgin_cpr"]]
    for c in nums:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df.dropna(subset=["symbol","timestamp","close"]).sort_values(
        ["symbol","timestamp"]
    )

def previous_close(df, symbol, current_date):
    x = df[(df.symbol == symbol) & (df.timestamp.dt.date < current_date)]
    return None if x.empty else float(x.iloc[-1].close)

def cpr(row, prev_close):
    if pd.isna(row.prevhigh) or pd.isna(row.prevlow) or prev_close is None:
        return None
    pivot = (row.prevhigh + row.prevlow + prev_close) / 3
    bc = (row.prevhigh + row.prevlow) / 2
    tc = 2 * pivot - bc
    return pivot, bc, tc

def build(df, settings):
    if df.empty:
        return pd.DataFrame()

    df = df.copy().sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    df["date"] = df["timestamp"].dt.normalize()

    result_data = []

    for symbol, symbol_data in df.groupby("symbol", sort=False):
        symbol_data = symbol_data.sort_values("timestamp")
        latest_row = symbol_data.iloc[-1]
        current_date = latest_row["timestamp"].normalize()
        current_volume = float(symbol_data.loc[symbol_data["timestamp"].dt.normalize() == current_date, "volume"].sum())

        daily_closes = symbol_data.groupby(symbol_data["timestamp"].dt.normalize(), sort=False)["close"].last()
        prev_close = None
        if len(daily_closes) >= 2:
            prev_close = float(daily_closes.iloc[-2])

        price_change = None
        if prev_close is not None and prev_close != 0:
            price_change = (latest_row["close"] - prev_close) / prev_close * 100

        cpr_type = "N/A"
        cpr_pivot = None
        cpr_bc = None
        cpr_tc = None

        if not pd.isna(latest_row["prevhigh"]) and not pd.isna(latest_row["prevlow"]) and prev_close is not None:
            cpr_pivot = (latest_row["prevhigh"] + latest_row["prevlow"] + prev_close) / 3
            cpr_bc = (latest_row["prevhigh"] + latest_row["prevlow"]) / 2
            cpr_tc = 2 * cpr_pivot - cpr_bc

            width_pct = abs(cpr_tc - cpr_bc) / abs(cpr_pivot) * 100 if cpr_pivot else 0
            if width_pct <= settings["cpr_narrow_percent"]:
                cpr_type = "Narrow"
            elif width_pct >= settings["cpr_wide_percent"]:
                cpr_type = "Wide"
            else:
                cpr_type = "Normal"

            pass

        result_data.append({
            "symbol": latest_row["symbol"],
            "instrument_key": latest_row["instrument_key"],
            "timestamp": latest_row["timestamp"].isoformat(),
            "price": latest_row["close"],
            "price_change": price_change,
            "RSI": latest_row["rsi"],
            "ADX": latest_row["adx"],
            "CCI": latest_row["cci"],
            "macd_histogram": latest_row["macd_histogram"],
            "cpr": cpr_type,
            "virgin_cpr": latest_row.get("virgin_cpr"),
            "volume": current_volume,
            "prevhigh": latest_row.get("prevhigh"),
            "prevlow": latest_row.get("prevlow"),
            "cpr_pivot": cpr_pivot,
            "cpr_bc": cpr_bc,
            "cpr_tc": cpr_tc,
            "pivot_r1": latest_row.get("pivot_r1"),
            "pivot_r2": latest_row.get("pivot_r2"),
            "pivot_r3": latest_row.get("pivot_r3"),
            "pivot_s1": latest_row.get("pivot_s1"),
            "pivot_s2": latest_row.get("pivot_s2"),
            "pivot_s3": latest_row.get("pivot_s3")
        })

    return pd.DataFrame(result_data)
