import json
from pathlib import Path
from datetime import datetime
from threading import Lock
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from . import database as database_module

load = database_module.load
prepare = database_module.prepare
build = database_module.build

BASE = Path(__file__).resolve().parent.parent
with open(BASE/"config/settings.json", encoding="utf-8") as f:
    SETTINGS = json.load(f)

DB = Path(SETTINGS["database_path"])
if not DB.is_absolute():
    DB = BASE / DB

app = FastAPI(title="Groww-Style SQLite Screener")
app.mount("/static", StaticFiles(directory=BASE/"frontend"), name="static")

CACHE = {"mtime": None, "payload": None}
CACHE_LOCK = Lock()

WATCH_PATHS = [BASE / "backend", BASE / "frontend", BASE / "config"]
WATCH_EXTENSIONS = {".py", ".js", ".css", ".html", ".json"}

def get_reload_mtime():
    max_mtime = 0.0
    for path in WATCH_PATHS:
        if not path.exists():
            continue
        for file_path in path.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in WATCH_EXTENSIONS:
                continue
            try:
                mtime = file_path.stat().st_mtime
            except OSError:
                continue
            if mtime > max_mtime:
                max_mtime = mtime
    return max_mtime


def clear_cache():
    with CACHE_LOCK:
        CACHE["mtime"] = None
        CACHE["payload"] = None

@app.get("/api/reload")
def reload_status():
    return {"reload_mtime": get_reload_mtime()}

@app.get("/")
def home():
    return FileResponse(BASE/"frontend/index.html")

@app.get("/api/results")
def results():
    try:
        mtime = DB.stat().st_mtime if DB.exists() else None
        refresh = True
        with CACHE_LOCK:
            if CACHE["payload"] is not None and CACHE["mtime"] == mtime:
                refresh = False

        if not refresh:
            payload = CACHE["payload"].copy()
            payload["last_updated"] = datetime.now().isoformat()
            payload.setdefault("latest_db_timestamp", None)
            return payload

        df = prepare(load(DB, SETTINGS["table_name"]), SETTINGS["database_timezone"])
        result = build(df, SETTINGS)
        records = result.to_dict("records") if not result.empty else []
        for r in records:
            for k, v in list(r.items()):
                try:
                    if pd.isna(v):
                        r[k] = None
                except Exception:
                    pass

        latest_db_timestamp = None
        if not df.empty:
            latest_db_timestamp = df["timestamp"].max().isoformat()

        payload = {
            "results": records,
            "latest_db_timestamp": latest_db_timestamp,
            "last_updated": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
            "row_count": len(df),
            "symbol_count": int(df.symbol.nunique()) if not df.empty else 0,
            "error": None
        }
        with CACHE_LOCK:
            CACHE["mtime"] = mtime
            CACHE["payload"] = payload
        return payload
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "results": [],
            "last_updated": datetime.now().isoformat(),
            "row_count": 0,
            "symbol_count": 0,
            "error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000)
