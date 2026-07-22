# Groww-Style SQLite Intraday Screener

Reads `Upstox_Historical_Data.db`, table `all_stock_indicators`, and provides a local Groww-style screener.

Features:
- Latest 5-minute row per symbol
- Price change %
- 52W performance when 365+ days of history are available
- RSI, ADX, CCI, MACD histogram
- CPR classification (Narrow / Normal / Wide)
- Search, sorting and dynamic filters
- Automatic SQLite refresh every 30 seconds
- No Upstox API calls required by the screener

## Required columns
instrument_key, symbol, timestamp, open, high, low, close, volume,
RSI, CCI, ADX, macd_line, macd_signal, macd_histogram, vwap,
prevHigh, prevLow, ema_close_9, bb_upper, bb_middle, bb_lower,
pivot, pivot_r1, pivot_r2, pivot_r3, pivot_s1, pivot_s2, pivot_s3,
ma_20, ma_50, ma_200

## Setup
1. Put `Upstox_Historical_Data.db` in `data/`, or set an absolute path in `config/settings.json`.
2. Run `pip install -r requirements.txt`.
3. Run `python -m backend.main` or double-click `run.bat`.
4. Open http://127.0.0.1:8000

The browser polls SQLite every 30 seconds. If another process adds new 5-minute rows, the dashboard picks them up automatically.

## CPR
Pivot = (Previous High + Previous Low + Previous Close) / 3
BC = (Previous High + Previous Low) / 2
TC = (2 * Pivot) - BC

True 52W performance requires approximately 52 weeks of database history. With only 5 days of data it correctly shows N/A.
