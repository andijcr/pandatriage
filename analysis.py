import json
import re
import os
from collections import defaultdict
import time

def load_json(name, folder="failures"):
    with open(f"{folder}/{name}.json", "r") as f:
        return json.load(f)

def save_json(obj, name):
    with open(f"workspace/{name}.json", "w") as b:
        json.dump(obj, b, indent=4)

manifest = load_json("manifest")

def is_closed(failure):
    # has issue
    # all issues are closed
    # no occurence after an issue is closed (2 days precision)
    if len(failure["issues"]) == 0:
        return False
    if not all(map(lambda x: x["state"]=="CLOSED", failure["issues"])):
        return False
    occurence = max(map(lambda x: x["ts"], failure["fails"]))
    closed = max(map(lambda x: x["updatedAt"], failure["issues"]))
    return occurence < closed + 2*24*60*60

def should_reopen(failure):
    if len(failure["issues"]) == 0:
        return False
    if not all(map(lambda x: x["state"]=="CLOSED", failure["issues"])):
        return False
    occurence = max(map(lambda x: x["ts"], failure["fails"]))
    closed = max(map(lambda x: x["updatedAt"], failure["issues"]))
    return occurence >= closed + 2*24*60*60

def no_ci(failure):
    return len(failure["issues"]) == 0

def is_stale_issue(failure):
    if len(failure["issues"]) == 0:
        return False
    if all(map(lambda x: x["state"]=="CLOSED", failure["issues"])):
        return False
    occurence = max(map(lambda x: x["ts"], failure["fails"]))
    return occurence + 2*30*24*60*60 < time.time()

def is_stale_failure(failure):
    occurence = max(map(lambda x: x["ts"], failure["fails"]))
    return occurence + 2*30*24*60*60 < time.time()

closed = []
reopen = []
noci = []
active = []
stale_issues = []
stale_failures = []

for id in manifest["failures"]:
    failure = load_json(id)

    last_occurence = max(map(lambda x: x["ts"], failure["fails"]))
    first_occurence = min(map(lambda x: x["ts"], failure["fails"]))

    collection = None

    if is_stale_issue(failure):
        collection = stale_issues
    elif is_stale_failure(failure):
        collection = stale_failures
    elif is_closed(failure):
        collection = closed
    elif should_reopen(failure):
        collection = reopen
    elif no_ci(failure):
        collection = noci
    else:
        collection = active
    
    collection.append({
        "name": failure["name"],
        "fails": len(failure["fails"]),
        "passes": failure["test"]["passes"],
        "first": min(map(lambda x: x["ts"], failure["fails"])),
        "last": max(map(lambda x: x["ts"], failure["fails"]))
    })

save_json({
    "stale_issues": stale_issues,
    "stale_failures": stale_failures,
    "should_reopen": reopen,
    "should_open": noci,
    "active": active
}, "ci-analysis")