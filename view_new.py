import argparse
from datetime import datetime
from index import load_json
from shared import parse_time

parser = argparse.ArgumentParser()
parser.add_argument('--notitle', action="store_false", required=False)
parser.add_argument('--test', action="store_true", required=False)
parser.add_argument('--since', type=parse_time, metavar='PERIOD',
                    help='Show only unassigned failures which have had an occurrence looking back PERIOD from now, like 24h, 60m, 2d')
args = parser.parse_args()

analysis = load_json("data/analysis")

occurrence = "last"

failures = sorted(analysis["should_open"], key=lambda x: x["first"], reverse=True)

since = None
if (args.since):
    since_period = args.since
    since = datetime.utcnow() - since_period
    print(f'Showing unassigned failures which had an occurence in the last {since_period} (after {since} UTC)')

legend = f"f-id\tbuild\tfreq\ttotal\tfirst occ."
if args.test:
    legend = f"{legend}\ttest"
if args.notitle:
    legend = f"{legend}\ttitle"
print(legend)

for item in failures:
    first_ts = datetime.fromtimestamp(item["first"])
    last_ts = datetime.fromtimestamp(item["last"])

    if since and last_ts < since:
        continue

    day = first_ts.strftime("%Y-%m-%d")
    line = f"{item['name']}\t#{item['link_id']}\t{item['freq']}\t{item['fails']}\t{day}"
    if args.test:
        line = f"{line}\t{item['test_id']}"
    if args.notitle:
        line = f"{line}\t{item['title']}"
    print(line)
