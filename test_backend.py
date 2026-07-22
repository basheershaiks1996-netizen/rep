import pandas as pd
from backend.database import build


def test_build_does_not_include_52w_performance_column():
    df = pd.DataFrame([
        {
            "instrument_key": "A",
            "symbol": "TEST",
            "timestamp": pd.Timestamp("2024-01-02 10:00:00", tz="UTC"),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 1000,
            "rsi": 55.0,
            "cci": 10.0,
            "adx": 15.0,
            "macd_line": 1.0,
            "macd_signal": 0.5,
            "macd_histogram": 0.2,
            "vwap": 100.0,
            "prevhigh": 110.0,
            "prevlow": 90.0,
            "ema_close_9": 100.0,
            "bb_upper": 110.0,
            "bb_middle": 100.0,
            "bb_lower": 90.0,
            "pivot": 100.0,
            "pivot_r1": 105.0,
            "pivot_r2": 110.0,
            "pivot_r3": 115.0,
            "pivot_s1": 95.0,
            "pivot_s2": 90.0,
            "pivot_s3": 85.0,
            "ma_20": 100.0,
            "ma_50": 100.0,
            "ma_200": 100.0,
        }
    ])

    result = build(df, {"cpr_narrow_percent": 0.35, "cpr_wide_percent": 0.70})

    assert "performance_52w" not in result.columns
    assert len(result) == 1
    assert result.iloc[0]["pivot_r1"] == 105.0
    assert result.iloc[0]["pivot_s1"] == 95.0
    assert result.iloc[0]["volume"] == 1000.0
