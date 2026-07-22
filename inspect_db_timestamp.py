import sqlite3
import json
from pathlib import Path
base = Path(r"C:/Users/bashe/Downloads/groww_sqlite_intraday_screener")
settings = json.loads((base / "config" / "settings.json").read_text(encoding="utf-8"))
db_path = settings["database_path"]
if not Path(db_path).is_absolute():
    db_path = str(base / Path(db_path))
with sqlite3.connect(db_path) as con:
    cur = con.cursor()
    cur.execute(f"SELECT MAX(timestamp) FROM {settings['table_name']}")
    print('max_raw:', cur.fetchone()[0])
    cur.execute(f"SELECT timestamp FROM {settings['table_name']} ORDER BY timestamp DESC LIMIT 5")
    print('top5:')
    for row in cur.fetchall():
        print(row[0])
