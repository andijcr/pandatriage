import argparse
import json
from datetime import datetime
from index import load_json


parser = argparse.ArgumentParser()
parser.add_argument('--type', choices=["top", "recent", "first", "reopen", "stale"], default="top", required=False)
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


legend = f"failure id,issue id,freq,total,{occurrence} occ.,test,title"
print(legend)

for item in issues:
    day = datetime.fromtimestamp(item["first" if args.type == "first" else "last"]).strftime("%Y-%m-%d")
    line = f"{item['name']},{item['issue']},{item['freq']},{item['fails']},{day},{item['test_id']},\"{item['title']}\""
    print(line)