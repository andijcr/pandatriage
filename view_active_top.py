import json
from datetime import datetime

def load_json(name, folder="workspace"):
    with open(f"{folder}/{name}.json", "r") as f:
        return json.load(f)

analysis = load_json("ci-analysis")

should_open = sorted(analysis["active"], key=lambda x: (x["freq"], x["fails"]), reverse=True)

for item in should_open:
    day = datetime.fromtimestamp(item["last"]).strftime("%Y-%m-%d")
    print(f"{item['issue']}\t{item['freq']}\t{item['fails']}\t{day}\t{item['title']}")