import sys
from index import load_json

manifest = load_json("data/failures/manifest")

for id in manifest["failures"]:
    failure = load_json(f"data/failures/{id}")

    for fail in failure["fails"]:
        if fail["link"] == sys.argv[1]:
            print(f"{id} {failure['test_id']}")
            break
