import psycopg2
import re
import json
import os.path
import os

def load_json(name, folder="builds"):
    with open(f"{folder}/{name}.json", "r") as f:
        return json.load(f)

def save_json(obj, name, folder="builds"):
    with open(f"{folder}/{name}.json", "w") as b:
        json.dump(obj, b, indent=4)

host = os.getenv("CI_DB_HOST")
database = "perfregressiondb"
user = os.getenv("CI_DB_USER")
password = os.getenv("CI_DB_PWD")

if os.path.exists("builds/manifest.json"):
    manifest = load_json("manifest")
else:
    manifest = {
        "builds": [],
        "last-id": -1
    }

conn = psycopg2.connect(f"host={host} dbname={database} user={user} password={password}")
cur = conn.cursor()
cur.execute(f"SELECT id, ts, name, data, meta FROM test_results WHERE id > {manifest['last-id']} AND name LIKE 'summary-%' ORDER BY ts ASC")
records = cur.fetchall()

r = re.compile("summary-ducktape-build-([a-z]+)-clang-([a-z0-9]+)-0")

fetched = 0

for record in records:
    fetched += 1

    m = r.match(record[2])
    if not m:
        assert False
    
    build = {
        "id": record[0],
        "day": record[1].strftime("%Y-%m-%d"),
        "ts": record[1].timestamp(),
        "build": m.group(1),
        "arch": m.group(2),
        "name": record[2],
        "data": record[3],
        "meta": record[4]
    }

    manifest["builds"].append(record[0])
    manifest["last-id"] = record[0]

    with open("builds/manifest.json", "w") as m:
        json.dump(manifest, m)
    
    with open(f"builds/{record[0]}.json", "w") as b:
        json.dump(build, b)

print(f"fetched {fetched} builds")