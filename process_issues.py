import json
import re
from datetime import datetime
from collections import defaultdict

def load_json(name):
    with open(f"issues/{name}.json", "r") as f:
        return json.load(f)

def save_json(obj, name):
    with open(f"workspace/{name}.json", "w") as b:
        json.dump(obj, b, indent=4)

manifest = load_json("manifest")

open_misformatted = []
open_conflicts = defaultdict(lambda: defaultdict(lambda: []))
closed_misformatted = []
skinny = []

def content_gen(issue):
    yield issue["body"]
    for comment in issue["comments"]:
        yield comment["body"]

def timestamp(ymdTHMSZ):
    dt = datetime.strptime(ymdTHMSZ, "%Y-%m-%dT%H:%M:%SZ")
    return dt.timestamp()

for num in manifest["issues"]:
    issue = load_json(f"{num}")
    lean = { "number": num }
    m = re.search("^Class: +([^\r]+)\r\nMethod: +([^\r]+)\r", issue["body"], re.MULTILINE)
    if m:
        lean["class"] = m.group(1)
        lean["method"] = m.group(2)
        lean["builds"] = []
        lean["state"] = issue["state"]
        lean["title"] = issue["title"]
        lean["createdAt"] = timestamp(issue["createdAt"])
        lean["updatedAt"] = timestamp(issue["updatedAt"])
        for content in content_gen(issue):
            for x in re.findall("(https://buildkite.com/redpanda/redpanda/builds/\d+)#[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}", content):
                if x not in lean["builds"]:
                    lean["builds"].append(x)
        skinny.append(lean)
    else:
        if issue["state"] == "OPEN":
            open_misformatted.append(num)
        else:
            closed_misformatted.append(num)

issues = defaultdict(lambda: [])
for issue in skinny:
    issues[f"{issue['class']}.{issue['method']}"].append(issue)

for test_id in issues:
    for i in range(0, len(issues[test_id])):
        for j in range(i+1, len(issues[test_id])):
            for link in issues[test_id][i]["builds"]:
                if link in issues[test_id][j]["builds"]:
                    open_conflicts[issues[test_id][i]["number"]][issues[test_id][j]["number"]].append(link)
                    open_conflicts[issues[test_id][j]["number"]][issues[test_id][i]["number"]].append(link)

save_json(open_misformatted, "open_misformatted")
save_json(closed_misformatted, "closed_misformatted")
save_json(open_conflicts, "open_conflicts")
save_json(skinny, "processed")
