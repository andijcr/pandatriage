import argparse
from datetime import datetime
from index import load_json

parser = argparse.ArgumentParser()
parser.add_argument('--notitle', action="store_false", required=False)
parser.add_argument('--test', action="store_true", required=False)
args = parser.parse_args()

analysis = load_json("data/analysis")

occurrence = "last"

failures = sorted(analysis["should_open"], key=lambda x: x["first"], reverse=True)

legend = f"f-id\tbuild\tfreq\ttotal\tfirst occ."
if args.test:
    legend = f"{legend}\ttest"
if args.notitle:
    legend = f"{legend}\ttitle"
print(legend)

for item in failures:
    day = datetime.fromtimestamp(item["first"]).strftime("%Y-%m-%d")
    line = f"{item['name']}\t#{item['link_id']}\t{item['freq']}\t{item['fails']}\t{day}"
    if args.test:
        line = f"{line}\t{item['test_id']}"
    if args.notitle:
        line = f"{line}\t{item['title']}"
    print(line)
