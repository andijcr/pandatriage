from sh import gh
import json

#NO_COLOR=1 python fetch_issues.py

#gh issue list -R redpanda-data/redpanda -l "ci-failure" -L 200 -s "open"

manifest = {
    "issues": []
}

for status in ["open", "close"]:
    issues = gh("issue", "list", "-R", "redpanda-data/redpanda", "-l", "ci-failure", "-L", "10000", "-s", status, "--json", "number")

    for issue in json.loads(str(issues)):
        num = issue["number"]
        issue = gh("issue", "view", "-R", "redpanda-data/redpanda", num, "--json", "number,title,body,comments,createdAt,updatedAt,state,comments")
        issue = json.loads(str(issue))

        if num not in manifest["issues"]:
            manifest["issues"].append(num)

        with open("issues/manifest.json", "w") as m:
            json.dump(manifest, m)
        
        with open(f"issues/{num}.json", "w") as b:
            json.dump(issue, b)
