import json
import sys

def load_json(name, folder="failures"):
    with open(f"{folder}/{name}.json", "r") as f:
        return json.load(f)

manifest = load_json("manifest")

for id in manifest["failures"]:
    failure = load_json(id)

    for fail in failure["fails"]:
        if fail["link"] == sys.argv[1]:
            print(id)