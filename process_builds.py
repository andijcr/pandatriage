import json
import re
import os

ignored_stacktraces = [
    [
        "runner_client.py:run",
        "runner_client.py:run_test",
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

def load_json(name):
    with open(f"builds/{name}.json", "r") as f:
        return json.load(f)

def save_json(obj, name):
    with open(f"failures/{name}.json", "w") as b:
        json.dump(obj, b, indent=4)

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
    for prefix in ignored_stacktraces:
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
    

manifest = load_json("manifest")

tests = dict()
failures = dict()

i=0
for id in manifest["builds"]:
    build = load_json(id)

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
            signature, title = get_signature(test_run)

            if signature not in failures:
                failures[signature] = {
                    "test_id": test_id,
                    "id": id,
                    "stacktrace": test_run["summary"],
                    "signature": signature,
                    "fails": []
                }

            failures[signature]["fails"].append({
                "title": title,
                "id": id,
                "ts": build["ts"],
                "build": build["build"],
                "arch": build["arch"],
                "link": build["meta"]["buildkite_env_vars"]["BUILDKITE_BUILD_URL"]
            })

    print(f"{i}/{len(manifest['builds'])}")
    i+=1

manifest = {
    "failures": []
}

i = 0
for signature in failures:
    i+=1
    failure = failures[signature]
    failure["test"] = tests[failure["test_id"]]
    manifest["failures"].append(i)
    save_json(failure, str(i))

save_json(manifest, "manifest")