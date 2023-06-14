import json
import sys

def load_json(name, folder="failures"):
    with open(f"{folder}/{name}.json", "r") as f:
        return json.load(f)

manifest = load_json("manifest")

for id in manifest["failures"]:
    failure = load_json(id)

    for issue in failure["issues"]:
        if int(sys.argv[1]) == issue["number"]:
            print(f"{id} {issue['title']}")
            break