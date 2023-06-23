import argparse
import json
from datetime import datetime
from index import load_json


parser = argparse.ArgumentParser()
parser.add_argument('--type', choices=["top", "recent", "first", "reopen", "stale"], default="top", required=False)
parser.add_argument('--notitle', action="store_false", required=False)
parser.add_argument('--test', action="store_true", required=False)
args = parser.parse_args()

analysis = load_json("data/analysis")

occurrence = "last"

issues = None
if args.type == "top":
    issues = sorted(analysis["active"], key=lambda x: (x["freq"], x["fails"]), reverse=True)
if args.type == "recent":
    issues = sorted(analysis["active"], key=lambda x: x["last"], reverse=True)
if args.type == "first":
    occurrence = "first"
    issues = sorted(analysis["active"], key=lambda x: x["first"], reverse=True)
if args.type == "reopen":
    issues = sorted(analysis["should_reopen"], key=lambda x: x["first"], reverse=True)
if args.type == "stale":
    issues = sorted(analysis["stale_issues"], key=lambda x: x["last"], reverse=True)


legend = f"f-id\tissue\tfreq\ttotal\t{occurrence} occ."
if args.test:
    legend = f"{legend}\ttest"
if args.notitle:
    legend = f"{legend}\ttitle"
print(legend)

for item in issues:
    day = datetime.fromtimestamp(item["first" if args.type == "first" else "last"]).strftime("%Y-%m-%d")
    
    line = f"{item['name']}\t#{item['issue']}\t{item['freq']}\t{item['fails']}\t{day}"
    if args.test:
        line = f"{line}\t{item['test_id']}"
    if args.notitle:
        line = f"{line}\t{item['title']}"
    
    print(line)