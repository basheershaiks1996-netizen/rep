#!/usr/bin/env python
import json
from backend.database import load, prepare, build

db_path = "C:\\Users\\bashe\\Downloads\\NSE Live Tracker\\upstox_scanner\\Upstox_Historical_Data.db"

settings = {
    "database_timezone": "Asia/Kolkata",
    "cpr_narrow_percent": 0.35,
    "cpr_wide_percent": 0.70
}

try:
    print("Loading data...")
    df = load(db_path, "all_stock_indicators")
    print(f"✓ Loaded {len(df)} rows")
    
    print("Preparing data...")
    df = prepare(df, "Asia/Kolkata")
    print(f"✓ Prepared {len(df)} rows")
    
    print("Building results...")
    result = build(df, settings)
    print(f"✓ Built {len(result)} stocks")
    
    if len(result) > 0:
        first = result.iloc[0].to_dict()
        print(f"\n✓ First row keys: {list(first.keys())}")
        print(f"✓ Sample data: symbol={first.get('symbol')}, price={first.get('price')}, RSI={first.get('RSI')}")
    
    print("\n✓ All tests passed!")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
