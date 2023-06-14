import psycopg2
import re
import json
import os.path
import os
import time
from sh import gh

host = os.getenv("CI_DB_HOST")
database = "perfregressiondb"
user = os.getenv("CI_DB_USER")
password = os.getenv("CI_DB_PWD")

re_build_arch = re.compile("summary-ducktape-build-([a-z]+)-clang-([a-z0-9]+)-0")

def load_json(name, folder):
    with open(f"{folder}/{name}.json", "r") as f:
        return json.load(f)

def save_json(obj, name, folder):
    with open(f"{folder}/{name}.json", "w") as b:
        json.dump(obj, b, indent=4)


def fetch_ci_runs():
    if os.path.exists("builds/manifest.json"):
        manifest = load_json("manifest", "builds")
    else:
        manifest = {
            "builds": [],
            "last-id": -1
        }

    print("Fetching a list of recent ci-runs")

    conn = psycopg2.connect(f"host={host} dbname={database} user={user} password={password}")
    cur = conn.cursor()
    cur.execute(f"SELECT count(*) FROM test_results WHERE id > {manifest['last-id']} AND name LIKE 'summary-%'")
    count = cur.fetchone()[0]
    if count > 0:
        print(f"Fetching {count} ci-runs")
    else:
        print("No new ci runs were found")

    fetched = 0
    while True:
        started = time.time()
        cur.execute(f"SELECT id, ts, name, data, meta FROM test_results WHERE id > {manifest['last-id']} AND name LIKE 'summary-%' ORDER BY id ASC LIMIT 100")
        records = cur.fetchall()

        if len(records) == 0:
            break

        for record in records:
            fetched += 1

            m = re_build_arch.match(record[2])
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

            save_json(manifest, "manifest", "builds")
            save_json(build, f"{record[0]}", "builds")
    
        ended = time.time()
        print(f"\tfetched {len(records)} ({fetched} / {count}) in {int(ended - started)}s")

def fetch_ci_issues():
    print("Fetching a list of recent ci issues")

    if os.path.exists("issues/manifest.json"):
        manifest = load_json("manifest", "issues")
    else:
        manifest = {
            "issues": [],
            "updatedAt": {}
        }

    fetch_list = set()

    for status in ["open", "close"]:
        issues = gh("issue", "list", "-R", "redpanda-data/redpanda", "-l", "ci-failure", "-L", "10000", "-s", status, "--json", "number,updatedAt")

        for issue in json.loads(str(issues)):
            num = issue["number"]
            updatedAt = issue["updatedAt"]

            if str(num) in manifest["updatedAt"]:
                if manifest["updatedAt"][str(num)] == updatedAt:
                    continue
            
            fetch_list.add(num)

    if len(fetch_list) > 0:
        print(f"Fetching {len(fetch_list)} ci issues")
    else:
        print("No new or updated issues were found")

    i = 0
    for num in fetch_list:
        started = time.time()
        issue = gh("issue", "view", "-R", "redpanda-data/redpanda", num, "--json", "number,title,body,comments,createdAt,updatedAt,state,comments")
        issue = json.loads(str(issue))

        if num not in manifest["issues"]:
            manifest["issues"].append(num)
            manifest["updatedAt"][str(num)] = issue["updatedAt"]

        save_json(manifest, "manifest", "issues")
        save_json(issue, f"{num}", "issues")
        ended = time.time()
        i+=1

        print(f"\tfetched issue #{num} ({i} / {len(fetch_list)}) in {int(1000*(ended - started))} ms")


fetch_ci_runs()
fetch_ci_issues()