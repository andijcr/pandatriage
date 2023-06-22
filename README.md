## Configuration

Set CI DB credentials (environment variables):

* `CI_DB_HOST`
* `CI_DB_USER`
* `CI_DB_PWD`

Search for "Redpanda Test Results DB" on wiki

### Dependencies

Install [gh](https://cli.github.com/) CLI binary.

Then choose venv or global install for python modules, with venv recommended.

#### venv

Using `venv` is the easiest way to set up the dependencies independently of the rest of your system.

One time setup (should show `venv setup OK` as the last line of output):

```bash
python3 -m venv venv && source venv/bin/activate && pip3 install -r requirements.txt && echo "venv setup OK"
```

When you return to use the tool in a new tty, you need to activate the venv:

```bash
source venv/bin/activate
```

#### Global install

* `pip3 install -r requirements.txt`

Use gh to set its credentials

## Usage

Correlate issues with failures. The first run takes ~30 mins because it downloads Redpanda Test Results DB
and gh issues locally from scratch. The follow up will fetch only delta.

```
python3 index.py
```

When you already used the tool and pull new version you should either `rm -rf data` or use `python3 index.py --reindex`.
The latter is faster because it doesn't download the test db again and only reprocess it.

### New failures

```
# list failures which doesn't have corresponding issues
python3 view_new.py
```

Output

```
f-id    build   freq    total   first occ.      title
491     #31233  628     1       2023-06-14      <NodeCrash (docker-rp-21,docker-rp-8) docker-rp-21: Redpanda process u
490     #31229  2223    24      2023-06-14      AttributeError("'NoneType' object has no attribute 'account'")
489     #31229  321     1       2023-06-14      TimeoutError()
487     #31184  184     1       2023-06-13      <NodeCrash docker-rp-16: ERROR 2023-06-13 15:22:08,202 [shard 1] asser
484     #31103  185     1       2023-06-12      <NodeCrash docker-rp-13: ERROR 2023-06-12 17:28:55,404 [shard 0] asser
...
202     #23852  326     3       2023-02-23      HTTPError('504 Server Error: Gateway Timeout for url: http://docker-rp
9       #21947  1652    9       2023-01-27      TimeoutError('Redpanda service docker-rp-10 failed to start within 60
40      #20893  183     2       2023-01-10      TimeoutError("Consumer failed to consume up to offsets {TopicPartition
```

Legend

```
f-id       - id of a failure, check `failures/491.json`
build      - buildkite's build, check https://buildkite.com/redpanda/redpanda/builds/31233
freq       - frequency of the fails (number of failures per 1MM)
total      - total number of fails
first occ. - first occurrence of the failure
title      - failure's title (to ignore: python3 view_new.py --notitle)
test       - failing test (to include: python3 view_new.py --test)
```

Sometime a rogue ci build causes a lot of errors which may be ignored (e.g. a responsible PR is identified and rolled back). In this case edit `.ciignore.json` to exclude that build, reset `last-processed-id` to `-1` in `data/builds/manifest.json` and restart `index.py`.

### Come back of old resolved issues

```
# list failures which keep happening after an issue is closed
python3 view_issues.py --type reopen
```

Output

```
f-id    issue   freq    total   last occ.       title
311     #10087  1027    10      2023-05-02      CI Failure (connection refused to admin API) in `EndToEndShadowIndexin
240     #7418   2938    32      2023-05-31      CI Failure (partitions_rebalanced times out) in `ScalingUpTest`.`test_
238     #9459   370     2       2023-06-14      CI Failure target_offset <= _insync_offset in `PartitionBalancerTest.t
...
57      #8919   1146    21      2023-06-14      CI Failure (Assertion `_state && !_state->available()' failed) in `Ran
33      #8220   1101    6       2023-05-04      Disk usage ratio check failing in `PartitionBalancerTest`.`test_full_n
1       #8421   1285    7       2023-06-02      CI Failure (heap-use-after-free) in `AvailabilityTests.test_availabili
```

### Top failing issues

```
python3 view_issues.py --type top
```

Output

```
f-id    issue   freq    total   last occ.       title
464     #11306  191588  41      2023-06-14      CI Failure (Consumed from an unexpected) in `SimpleEndToEndTest.test_c
429     #11044  56807   121     2023-06-15      CI Failure (Timeout - Failed to start) in `MultiTopicAutomaticLeadersh
362     #10849  47368   45      2023-05-18      CI Failure (timeout waiting for `rpk cluster` to list 1 topic) in `Sha
448     #11151  22666   17      2023-06-02      CI Failure (TimeoutError) in `CloudStorageChunkReadTest.test_read_when
224     #10873  16984   49      2023-05-21      CI Failure (Reported cloud storage usage did not match the manifest in
...
329     #10368  51      1       2023-04-22      CI Failure (topic does not exist while deleting topic) in `ShadowIndex
412     #10935  45      1       2023-05-19      CI Failure (Internal Server Error) in `PartitionBalancerTest.test_deco
428     #11410  42      1       2023-05-25      CI Failure (consumers haven't finished) in `CompactionE2EIdempotencyTe
482     #11371  9       1       2023-06-12      CI Failure (Redpanda failed to stop in 30 seconds) in `PartitionMoveIn
```

### First occurrence of a failure

The command is usefull to chase a PR causing the problem.

```
python3 view_issues.py --type first
```

```
f-id    issue   freq    total   first occ.      title
486     #11151  1362    1       2023-06-13      CI Failure (TimeoutError) in `CloudStorageChunkReadTest.test_read_when
485     #11365  666     5       2023-06-12      CI Failure (Timeout waiting for partitions to move) in `NodesDecommiss
482     #11371  9       1       2023-06-12      CI Failure (Redpanda failed to stop in 30 seconds) in `PartitionMoveIn
...
60      #10218  739     4       2022-12-21      CI Failure (ignored exceptional future) in `PartitionBalancerTest.test
80      #10024  2205    24      2022-12-14      CI Failure (TimeoutError in wait_for_partitions_rebalanced) in `Scalin
78      #11062  551     6       2022-12-13      CI Failure (startup failure) in `ScalingUpTest.test_adding_multiple_no
```

### Last occurrence of a failure

```
python3 view_issues.py --type recent
```

```
f-id    issue   freq    total   last occ.       title
485     #11365  925     7       2023-06-15      CI Failure (Timeout waiting for partitions to move) in `NodesDecommiss
429     #11044  61167   132     2023-06-15      CI Failure (Timeout - Failed to start) in `MultiTopicAutomaticLeadersh
490     #11456  2489    27      2023-06-15      CI Failure (`AttributeError: 'NoneType' object has no attribute 'accou
...
305     #10363  628     3       2023-05-04      CI Failure (assertion error: groups not reported after migration) in `
60      #10218  735     4       2023-05-04      CI Failure (ignored exceptional future) in `PartitionBalancerTest.test
329     #10368  51      1       2023-04-22      CI Failure (topic does not exist while deleting topic) in `ShadowIndex
```

### Stale issues

A failure associated with the issues hasn't failed within two months

```
python3 view_issues.py --type stale
```

```
f-id    issue   freq    total   last occ.       title
15      #8496   933     4       2023-04-12      CI Failure (_topic_remote_deleted timeout) in `TopicDeleteCloudStorage
223     #9751   204     4       2023-04-05      CI Failure (timeout + UNKNOWN_TOPIC_OR_PARTITION) in `EndToEndTopicRec
4       #8457   206     5       2023-03-07      CI Failure (Timeout on manifest_has_one_segment) in `AdjacentSegmentMe
```
