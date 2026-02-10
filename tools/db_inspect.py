import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parents[1] / "data" / "app.db"
print("DB:", db_path)

con = sqlite3.connect(str(db_path))
cur = con.cursor()

print("\nTables:")
for (name,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print("-", name)

print("\nSchema (users):")
try:
    rows = cur.execute("PRAGMA table_info('users')").fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print("No users table?", e)

print("\nFirst users:")
try:
    rows = cur.execute("SELECT * FROM users LIMIT 20").fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print("Can't select from users:", e)

con.close()