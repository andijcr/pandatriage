import sys
from index import load_json

manifest = load_json("data/failures/manifest")

for id in manifest["failures"]:
    failure = load_json(f"data/failures/{id}")

    for issue in failure["issues"]:
        if int(sys.argv[1]) == issue["number"]:
            print(f"{id} {issue['title']}")
            break