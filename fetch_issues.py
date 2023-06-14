from sh import gh
import json
import os
import time

#NO_COLOR=1 python fetch_issues.py

def load_json(name, folder="issues"):
    with open(f"{folder}/{name}.json", "r") as f:
        return json.load(f)

def save_json(obj, name, folder="issues"):
    with open(f"{folder}/{name}.json", "w") as b:
        json.dump(obj, b, indent=4)

if os.path.exists("issues/manifest.json"):
    manifest = load_json("manifest")
else:
    manifest = {
        "issues": [],
        "updatedAt": {}
    }

print("Fetching a list of recent ci issues")

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

    save_json(manifest, "manifest")
    save_json(issue, f"{num}")
    ended = time.time()
    i+=1

    print(f"\tfetched {i} / {len(fetch_list)} in {int(1000*(ended - started))} ms")