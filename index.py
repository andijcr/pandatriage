import psycopg2
import re
import json
import os.path
import os
import time
import shutil
from sh import gh
from datetime import datetime
from collections import defaultdict
import argparse

def getenv(key: str):
    v = os.getenv(key)
    if not v:
        raise RuntimeError(f'You must set {key} in the environment before running {os.path.basename(__file__)}')
    return v

host = getenv("CI_DB_HOST")
database = "perfregressiondb"
user = getenv("CI_DB_USER")
password = getenv("CI_DB_PWD")


re_build_arch = re.compile("summary-ducktape-build-([a-z]+)-clang-([a-z0-9]+)-0")

ignored_stacktrace_prefixes = [
    [
        "runner_client.py:run",
        "runner_client.py:run_test",
        "cluster.py:wrapped"
    ],
    [
        "runner_client.py:run",
        "runner_client.py:run_test",
        "mode_checks.py:f",
        "cluster.py:wrapped"
    ],
    [
        "runner_client.py:run",
        "runner_client.py:run_test",
        "_mark.py:wrapper",
        "mode_checks.py:f",
        "cluster.py:wrapped"
    ]
]

error_classes = {
    "TimeoutError": "^TimeoutError",
    "NodeCrash": "^<NodeCrash",
    "BadLogLines": "^<BadLogLines",
    "RuntimeError": "^RuntimeError",
    "HTTPError": "^HTTPError",
    "AssertionError": "^AssertionError",
    "CalledProcessError": "^CalledProcessError",
    "RpkException": "^RpkException",
    "ValueError": "^ValueError",
    "ConnectionError": "^ConnectionError",
    "KafkaTimeoutError": "^KafkaTimeoutError",
    "TypeError": "^TypeError",
    "SSHException": "^SSHException",
    "ConsistencyViolationException": "^ConsistencyViolationException",
    "ConnectTimeout": "^ConnectTimeout",
    "Exception": "^Exception\(",
    "KafkaException": "^KafkaException",
    "RemoteCommandError": "^RemoteCommandError",
    "RetryError": "^RetryError"
}

def main():

    # because otherwise g() returns results with ASCII escape codes to colorize
    os.environ['NO_COLOR'] = '1' 

    os.makedirs("data/builds", exist_ok=True)
    os.makedirs("data/failures", exist_ok=True)
    os.makedirs("data/issues", exist_ok=True)
    shutil.rmtree("data/open", ignore_errors=True)
    os.makedirs("data/open", exist_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument('--reindex', action='store_true', required=False)
    args = parser.parse_args()
    
    fetch_ci_runs()
    fetch_ci_issues()
    process_ci_runs(args.reindex)
    process_ci_issues()
    process_failures()
    analyze()

def load_json(name):
    with open(f"{name}.json", "r") as f:
        return json.load(f)

def save_json(name, obj):
    with open(f"{name}.json", "w") as b:
        json.dump(obj, b, indent=4)


def fetch_ci_runs():
    if os.path.exists("data/builds/manifest.json"):
        manifest = load_json("data/builds/manifest")
    else:
        manifest = {
            "builds": [],
            "last-fetched-id": -1,
            "last-processed-id": -1
        }

    print("Fetching a list of recent ci-runs")

    conn = psycopg2.connect(f"host={host} dbname={database} user={user} password={password}")
    cur = conn.cursor()
    cur.execute(f"SELECT count(*) FROM test_results WHERE id > {manifest['last-fetched-id']} AND name LIKE 'summary-%'")
    count = cur.fetchone()[0]
    if count > 0:
        print(f"Fetching {count} ci-runs")
    else:
        print("No new ci runs were found")

    fetched = 0
    while True:
        started = time.time()
        cur.execute(f"SELECT id, ts, name, data, meta FROM test_results WHERE id > {manifest['last-fetched-id']} AND name LIKE 'summary-%' ORDER BY id ASC LIMIT 100")
        records = cur.fetchall()

        if len(records) == 0:
            break

        for record in records:
            fetched += 1

            build = "release"
            arch = "amd64"
            type = "cdt"

            if record[2] != "cdt":
                m = re_build_arch.match(record[2])
                if not m:
                    assert False
                build = m.group(1)
                arch = m.group(2)
                type = "pr-merged"
        
            build = {
                "id": record[0],
                "day": record[1].strftime("%Y-%m-%d"),
                "ts": record[1].timestamp(),
                "build": build,
                "arch": arch,
                "type": type,
                "name": record[2],
                "data": record[3],
                "meta": record[4]
            }

            manifest["builds"].append(record[0])
            manifest["last-fetched-id"] = record[0]

            save_json("data/builds/manifest", manifest)
            save_json(f"data/builds/{record[0]}", build)
    
        ended = time.time()
        print(f"\tfetched {len(records)} ({fetched} / {count}) in {int(ended - started)}s")

def fetch_ci_issues():
    print("Fetching a list of recent ci issues")

    if os.path.exists("data/issues/manifest.json"):
        manifest = load_json("data/issues/manifest")
    else:
        manifest = {
            "issues": [],
            "updatedAt": {}
        }

    fetch_list = set()

    for status in ["open", "closed"]:
        issues = gh("issue", "list", "-R", "redpanda-data/redpanda", "-L", "10000", "-s", status, "--json", "number,updatedAt", "--search", "label:ci-failure -label:rpunit -label:ci-ignore")

        for issue in json.loads(str(issues)):
            num = issue["number"]
            updatedAt = issue["updatedAt"]

            if str(num) in manifest["updatedAt"]:
                if manifest["updatedAt"][str(num)] == updatedAt:
                    continue
            
            fetch_list.add(num)

    if len(fetch_list) > 0:
        print(f"Fetching {len(fetch_list)} ci issues")
    else:
        print("No new or updated issues were found")

    i = 0
    for num in fetch_list:
        started = time.time()
        issue = gh("issue", "view", "-R", "redpanda-data/redpanda", num, "--json", "number,title,body,comments,createdAt,updatedAt,state,comments,labels")
        issue = json.loads(str(issue))

        if num not in manifest["issues"]:
            manifest["issues"].append(num)
            manifest["updatedAt"][str(num)] = issue["updatedAt"]

        save_json("data/issues/manifest", manifest)
        save_json(f"data/issues/{num}", issue)
        ended = time.time()
        i+=1

        print(f"\tfetched issue #{num} ({i} / {len(fetch_list)}) in {int(1000*(ended - started))} ms")

def is_prefix(prefix, stacktrace):
    if len(prefix) > len(stacktrace):
        return False
    for i in range(0, len(prefix)):
        if prefix[i] != stacktrace[i]:
            return False
    return True

def get_signature(test_run):
    lines = test_run["summary"].splitlines()

    i=0
    title=[]
    while lines[i] != "Traceback (most recent call last):":
        title.append(lines[i])
        i+=1
    title = title[0]

    i+=1
    stacktrace = []
    while True:
        m = re.match('  File "([^"]+)", line \d+, in ([a-z_A-Z0-9<>]+)', lines[i])
        if not m:
            assert "File" not in lines[i]
            break
        path = os.path.basename(m.group(1))
        method = m.group(2)
        stacktrace.append(f"{path}:{method}")
        i+=2
    for prefix in ignored_stacktrace_prefixes:
        if is_prefix(prefix, stacktrace):
            stacktrace = stacktrace[len(prefix):]
            break
    
    result = ""
    result += test_run["cls_name"] + "\n"
    result += test_run["function_name"] + "\n"
    
    label = ""
    for ec in error_classes:
        if re.match(error_classes[ec], title):
            label = ec
            break
    
    result += f"{label}\n"
    for item in stacktrace:
        result += item + "\n"
    return result, title

def process_ci_runs(reindex):
    ciignore = {}
    if os.path.exists(".ciignore.json"):
        for item in load_json(".ciignore"):
            ciignore[item["build"]] = item["only"] if "only" in item else None
    
    manifest = load_json("data/builds/manifest")

    if not(reindex) and manifest["last-processed-id"] == manifest["last-fetched-id"]:
        print("All ci runs are processed")
        return

    print(f"Processing {len(manifest['builds'])} ci-runs")

    tests = dict()
    failures = dict()

    i=0
    for id in manifest["builds"]:
        print(f"\tprocessing ci-run #{id} ({i}/{len(manifest['builds'])})")
        build = load_json(f"data/builds/{id}")

        manifest["last-processed-id"] = id

        for test_run in build["data"]["ducktape_plus_cluster_config"]["results"]:
            test_id = f"{test_run['cls_name']}.{test_run['function_name']}"

            if test_id not in tests:
                tests[test_id] = {
                    "first_build_ts": build["ts"],
                    "last_build_ts": build["ts"],
                    "first_build_id": id,
                    "last_build_id": id,
                    "runs": 0,
                    "passes": 0
                }
            
            tests[test_id]["runs"] += 1
            tests[test_id]["last_build_id"] = build["id"]
            tests[test_id]["last_build_ts"] = build["ts"]

            if test_run["test_status"] in ["PASS", "OPASS"]:
                tests[test_id]["passes"] += 1
            
            if test_run["test_status"] == "FAIL":
                link_id = int(re.match(".+/([0-9]+)$", build["meta"]["buildkite_env_vars"]["BUILDKITE_BUILD_URL"]).group(1))
                if link_id in ciignore:
                    if ciignore[link_id] == None or test_id in ciignore[link_id]:
                        continue

                signature, title = get_signature(test_run)

                if signature not in failures:
                    failures[signature] = {
                        "test_id": test_id,
                        "id": id,
                        "stacktrace": test_run["summary"],
                        "run_time_seconds": test_run["run_time_seconds"],
                        "module_name": test_run["module_name"],
                        "cls_name": test_run["cls_name"],
                        "function_name": test_run["function_name"],
                        "injected_args": test_run["injected_args"],
                        "signature": signature,
                        "fails": []
                    }

                failures[signature]["fails"].append({
                    "title": title,
                    "id": id,
                    "ts": build["ts"],
                    "type": build["type"],
                    "build": build["build"],
                    "arch": build["arch"],
                    "link": build["meta"]["buildkite_env_vars"]["BUILDKITE_BUILD_URL"]
                })

        i+=1
    
    save_json("data/builds/manifest", manifest)

    manifest = {
        "failures": []
    }

    i = 0
    for signature in failures:
        i+=1
        failure = failures[signature]
        failure["test"] = tests[failure["test_id"]]
        manifest["failures"].append(i)
        save_json(f"data/failures/{i}", failure)

    save_json("data/failures/manifest", manifest)

def process_ci_issues():
    def content_gen(issue):
        yield issue["body"]
        for comment in issue["comments"]:
            yield comment["body"]

    def timestamp(ymdTHMSZ):
        dt = datetime.strptime(ymdTHMSZ, "%Y-%m-%dT%H:%M:%SZ")
        return dt.timestamp()
    
    manifest = load_json("data/issues/manifest")
    print(f"Processing {len(manifest['issues'])} ci-issues")

    open_misformatted = []
    open_conflicts = defaultdict(lambda: defaultdict(lambda: []))
    closed_misformatted = []
    skinny = []

    for num in manifest["issues"]:
        issue = load_json(f"data/issues/{num}")
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
            lean["labels"] = list(map(lambda x: x["name"], issue["labels"]))
            lean["opt"] = None
            for content in content_gen(issue):
                if lean["opt"] == None:
                    for opt_json in re.findall("```([^(```)]+)```", content, re.MULTILINE):
                        try:
                            lean["opt"] = json.loads(opt_json)
                            break
                        except json.decoder.JSONDecodeError:
                            continue

                # for now we don't require a fragment, since issues created by this tool lack them, 
                # regex for fragment was:
                # #[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}
                for x in re.findall("(https://buildkite.com/redpanda/redpanda/builds/\d+)", content):
                    if x not in lean["builds"]:
                        lean["builds"].append(x)
            if lean["opt"] == None:
                lean["opt"] = dict()
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
            if issues[test_id][i]["state"] != "OPEN":
                continue
            for j in range(i+1, len(issues[test_id])):
                if issues[test_id][j]["state"] != "OPEN":
                    continue
                for link in issues[test_id][i]["builds"]:
                    if link in issues[test_id][j]["builds"]:
                        open_conflicts[issues[test_id][i]["number"]][issues[test_id][j]["number"]].append(link)
                        open_conflicts[issues[test_id][j]["number"]][issues[test_id][i]["number"]].append(link)

    save_json("data/misformatted-open-issues", open_misformatted)
    save_json("data/misformatted-closed-issues", closed_misformatted)
    save_json("data/conflicting-open-issues", open_conflicts)
    save_json("data/issues", skinny)

def process_failures():
    issues = defaultdict(lambda: [])

    for issue in load_json("data/issues"):
        issues[f"{issue['class']}.{issue['method']}"].append(issue)

    manifest = load_json("data/failures/manifest")

    print(f"Linkning {len(manifest['failures'])} test failures with existing ci-issues")

    for id in manifest["failures"]:
        failure = load_json(f"data/failures/{id}")
        failure["name"] = id
        tickets = []
        for fail in failure["fails"]:
            if len(tickets) > 0:
                break
            for issue in issues[failure["test_id"]]:
                if fail["link"] in issue["builds"]:
                    tickets.append({
                        "state": issue["state"],
                        "title": issue["title"],
                        "createdAt": issue["createdAt"],
                        "updatedAt": issue["updatedAt"],
                        "number": issue["number"],
                        "link": fail["link"],
                        "labels": issue["labels"],
                        "opt": issue["opt"],
                    })
        failure["issues"] = tickets
        save_json(f"data/failures/{id}", failure)

def analyze():
    def is_closed(failure):
        if len(failure["issues"]) == 0:
            return False
        if not all(map(lambda x: x["state"]=="CLOSED", failure["issues"])):
            return False
        return True
    
    def is_resolved(failure, precision_s = 2*24*60*60):
        # a failure is resolved if it:
        #  - has an least one assosiated issue
        #  - all issues are closed
        #  - no occurence after an issue is closed (with precision_s)
        if not is_closed(failure):
            return False
        occurence = max(map(lambda x: x["ts"], failure["fails"]))
        closed = max(map(lambda x: x["updatedAt"], failure["issues"]))
        # using `occurence < closed + precision_s` instead of `occurence < closed`
        # as a safety measure against timezone shenanigans; with a 2d delta we
        # don't need to worry if `occurence`` & `closed` are from the same time
        # zone
        return occurence < closed + precision_s

    def should_reopen(failure, precision_s = 2*24*60*60):
        # returns True if a failure:
        #  - has an least one associated issue
        #  - all issues are closed
        #  - there is a recurrence at least precision_s later after last closed issue
        if len(failure["issues"]) == 0:
            return False
        if not all(map(lambda x: x["state"]=="CLOSED", failure["issues"])):
            return False
        occurence = max(map(lambda x: x["ts"], failure["fails"]))
        closed = max(map(lambda x: x["updatedAt"], failure["issues"]))
        return occurence >= closed + precision_s

    def should_open(failure):
        return len(failure["issues"]) == 0

    def active_issue(failure):
        open = [x for x in failure["issues"] if x["state"] == "OPEN"]
        return sorted(open, key=lambda x: x["updatedAt"], reverse=True)[0]

    def last_issue(failure):
        return sorted(failure["issues"], key=lambda x: x["updatedAt"], reverse=True)[0]

    def is_stale_issue(failure):
        if len(failure["issues"]) == 0:
            return False
        if all(map(lambda x: x["state"]=="CLOSED", failure["issues"])):
            return False
        if any(map(lambda x: x["state"]=="OPEN" and "ci-disabled-test" in x["labels"], failure["issues"])):
            return False
        occurence = max(map(lambda x: x["ts"], failure["fails"]))
        return occurence + 2*30*24*60*60 < time.time()

    def is_stale_failure(failure):
        if len(failure["issues"]) != 0:
            return False
        occurence = max(map(lambda x: x["ts"], failure["fails"]))
        return occurence + 2*30*24*60*60 < time.time()
    
    def first_fail(failure):
        return sorted(failure["fails"], key=lambda x: x["ts"])[0]
    
    issues = dict()
    for issue in load_json("data/issues"):
        issues[issue["number"]] = issue
    
    def get_duplicate(failure):
        result = None
        duplicatee = None
        for issue in failure["issues"]:
            if "duplicate" in issue['opt']:
                m = re.match("^https://github.com/redpanda-data/redpanda/issues/(\d+)$", issue["opt"]["duplicate"])
                if not m:
                    raise Exception(f"can't load issue #{issue['number']}: {issue['opt']['duplicate']} isn't a link to an issue")
                iid = int(m.group(1))
                assert result == None or result == iid, f"a failure can't be a duplicate of diff issues: {result} & {iid}"
                result = iid
                duplicatee = issue
        if not is_closed(failure):
            assert result == None
        return result, duplicatee["number"] if duplicatee != None else None
    
    failures = {}
    fid_by_test = defaultdict(lambda: [])
    manifest = load_json("data/failures/manifest")
    for id in manifest["failures"]:
        failure = load_json(f"data/failures/{id}")
        failures[id] = failure
        fid_by_test[failure["test_id"]].append(id)

    def get_root(failure):
        number, duplicatee = get_duplicate(failure)
        if number == None:
            failure["duplicated"] = False
            return failure
        failure["duplicated"] = True
        failure["double"] = duplicatee
        assert number in issues, f"can't find duplicate #{number}"
        test_id = f"{issues[number]['class']}.{issues[number]['method']}"
        assert test_id in fid_by_test, f"can't find test_id: {test_id}"
        fd = None
        for fid in fid_by_test[test_id]:
            failure2 = failures[fid]
            for issue in failure2["issues"]:
                if issue["number"] == number:
                    if fd != None:
                        assert False, f"found fid:{failure2['id']} by #{number} of fid:{failure['id']} conflicting with fid={fd['id']}"
                    fd = failure2
        assert fd != None, f"can't find failure by #{number} of fid:{failure['id']}"
        return get_root(fd)
    
    for id in failures:
        failure = failures[id]
        root = get_root(failure)
        if failure != root:
            if "duplicates" not in root:
                root["duplicates"] = [ root ]
            root["duplicates"].append(failure)

    resolved = []
    reopen = []
    noci = []
    active = []
    stale_issues = []
    stale_failures = []

    for id in failures:
        failure = failures[id]

        if failure["duplicated"]:
            continue

        collection = None

        freq = int(1000000 * len(failure["fails"]) / (len(failure["fails"]) + failure["test"]["passes"]))
        fails = len(failure["fails"])
        first = min(map(lambda x: x["ts"], failure["fails"]))
        last = max(map(lambda x: x["ts"], failure["fails"]))

        sub = []
        if "duplicates" in failure:
            x = 1
            failed_builds = set()
            for f in failure["duplicates"]:
                if f != failure:
                    iid = f["double"]
                else:
                    iid = active_issue(failure)["number"]
                
                sub.append({
                    "freq": int(1000000 * len(f["fails"]) / (len(f["fails"]) + f["test"]["passes"])),
                    "name": f["name"],
                    "issue": iid,
                    "fails": len(f["fails"]),
                    "first": min(map(lambda x: x["ts"], f["fails"])),
                    "last": min(map(lambda x: x["ts"], f["fails"])),
                    "test_id": f["test_id"],
                    "title": issues[iid]["title"]
                })
                
                x = x * (1 - len(f["fails"]) / (len(f["fails"]) + f["test"]["passes"]))
                for fail in f["fails"]:
                    first = min(first, fail["ts"])
                    last = max(last, fail["ts"])
                    failed_builds.add(fail["id"])
            freq = int(1000000 * (1 - x))
            fails = len(failed_builds)

        entry = {
            "title": failure["fails"][0]["title"].replace("\r", "").split("\n")[0],
            "freq": freq
        }

        if is_stale_issue(failure):
            issue = active_issue(failure)
            entry = {
                "issue": issue["number"],
                "title": issue["title"],
                "freq": freq
            }
            collection = stale_issues
        elif is_stale_failure(failure):
            collection = stale_failures
        elif is_resolved(failure):
            collection = resolved
        elif should_reopen(failure):
            issue = last_issue(failure)
            entry = {
                "issue": issue["number"],
                "title": issue["title"],
                "freq": freq
            }
            collection = reopen
        elif should_open(failure):
            c = f"CI Failure (key symptom) in `{failure['cls_name']}.{failure['function_name']}`\n" +\
                "\n" +\
                "\n".join(map(lambda x: x["link"], failure["fails"])) + "\n" +\
                "\n" +\
                "```\n" +\
                f"Module: {failure['module_name']}\n" +\
                f"Class: {failure['cls_name']}\n" +\
                f"Method: {failure['function_name']}\n" +\
                (f"Arguments: {json.dumps(failure['injected_args'], indent=4)}\n" if failure['injected_args'] != None else "") +\
                "```\n" +\
                "\n" +\
                "```\n" +\
                f"test_id:    {failure['test_id']}\n" +\
                f"status:     FAIL\n" +\
                f"run time:   {failure['run_time_seconds']:.3f} seconds\n" +\
                "\n" +\
                f"{failure['stacktrace']}" +\
                "```\n"
            
            with open(f"data/open/{id}.md", "w") as f:
                f.write(c)

            entry["link_id"] = int(re.match(".+/([0-9]+)$", first_fail(failure)["link"]).group(1))
            collection = noci
        else:
            issue = active_issue(failure)
            entry = {
                "issue": issue["number"],
                "title": issue["title"],
                "freq": freq
            }
            collection = active
        
        if "duplicates" in failure:
            entry["title"] = "* " + entry["title"]
            
        collection.append(entry | {
            "test_id": failure["test_id"],
            "name": failure["name"],
            "fails": fails,
            "passes": failure["test"]["passes"],
            "runs": failure["test"]["runs"],
            "first": first,
            "last": last,
            "sub": sub
        })

    save_json("data/analysis", {
        "stale_issues": stale_issues,
        "should_reopen": reopen,
        "should_open": noci,
        "active": active
    })

if __name__ == "__main__":
    main()
