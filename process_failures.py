import json
import re
import os
from collections import defaultdict

def load_json(name, folder="failures"):
    with open(f"{folder}/{name}.json", "r") as f:
        return json.load(f)

def save_json(obj, name, folder="failures"):
    with open(f"{folder}/{name}.json", "w") as b:
        json.dump(obj, b, indent=4)

issues = defaultdict(lambda: [])

for issue in load_json("processed", folder="workspace"):
    issues[f"{issue['class']}.{issue['method']}"].append(issue)

manifest = load_json("manifest")

for id in manifest["failures"]:
    failure = load_json(id)
    failure["name"] = id
    tickets = []
    for fail in failure["fails"]:
        if len(tickets) > 0:
            break
        for issue in issues[failure["test_id"]]:
            if fail["link"] in issue["builds"]:
                tickets.append({
                    "state": issue["state"],
                    "createdAt": issue["createdAt"],
                    "updatedAt": issue["updatedAt"],
                    "number": issue["number"],
                    "link": fail["link"]
                })
    failure["issues"] = tickets
    save_json(failure, str(id))
