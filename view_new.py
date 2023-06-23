import argparse
from datetime import datetime
from index import load_json
from shared import parse_time

parser = argparse.ArgumentParser()
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

legend = f"failure id,build,freq,total,first occ.,test,title"
print(legend)

for item in failures:
    first_ts = datetime.fromtimestamp(item["first"])
    last_ts = datetime.fromtimestamp(item["last"])

    if since and last_ts < since:
        continue

    day = first_ts.strftime("%Y-%m-%d")
    line = f"{item['name']},{item['link_id']},{item['freq']},{item['fails']},{day},{item['test_id']},\"{item['title']}\""
    print(line)
