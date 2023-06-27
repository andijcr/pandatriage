## Configuration

Configure the CI database credentials (environment variables):

* `CI_DB_HOST`
* `CI_DB_USER`
* `CI_DB_PWD`

Refer to the wiki for information on "Redpanda Test Results DB."

### Dependencies

Install [gh](https://cli.github.com/) CLI for GitHub and execute it to set up its credentials.

Next, choose between a virtual environment (`venv`) or a global installation for Python modules, with `venv` recommended.

#### Virtual Environment (venv)

Using `venv` is the easiest way to set up the dependencies independently of the rest of your system.

Perform a one-time setup (the last line of output should indicate `venv setup OK`):

```bash
python3 -m venv venv && source venv/bin/activate && pip3 install -r requirements.txt && echo "venv setup OK"
```

When you return to use `pandatriage` in a new terminal, you need to activate the virtual environment:

```bash
source venv/bin/activate
```

#### Global Installation

* `pip3 install -r requirements.txt`

## Usage

Execute `python3 index.py` to download "Redpanda Test Results DB" & ci-issues, group test failures by a pair of test name and its stacktrace parts, correlate issues with failures using ci links. The first run takes approximately 30 minutes as it downloads full data. Subsequent runs will only fetch the delta.

To reset index's state execute `rm -rf data` and then start from scratch with `python3 index.py`.

### Duplicates

`pandatriage` expects that each failure (a set of test failures with the same test name and stack trace) has an associated CI issue. Sometimes, different tests may fail for the same reason. In such cases, we can mark one issue as a duplicate of another.

To mark issue #xxx as a duplicate of #yyy, close issue #xxx and add a comment (remember to use a code markdown block with triple backticks):

```
{
    "duplicate": "https://github.com/redpanda-data/redpanda/issues/yyy"
}
```

### Bad Build

Sometimes, a transient change in the environment, such as misconfiguration or accidental merging of a wrong branch, can cause multiple tests to fail. Instead of opening an issue for each failed test, we can ignore a build that causes numerous errors (e.g., when a responsible pull request is identified and rolled back). In such cases, edit `.ciignore.json` to exclude that build and restart `python3 index.py --reindex`.

### Misformatted Issues

The directory `data/misformatted-open-issues` contains misformatted open issues marked with `ci-failure`. If a `ci-failure` pertains to a unit test (ducktape's ci-issue format is not applicable), add the `rpunit` label to ignore it. If an issue should be ignored for any other reason, add the `ci-ignore` label.

### Commands

#### New Failures

```
# List failures that do not have corresponding issues
python3 view_new.py | csvcut -c "failure id","build","freq","total","first occ.","test","title" | csvlook -I -q '"' -d "," | less -S
```

The `csvkit` package (with `csvcut` and `csvlook` commands) is used to select columns from the output of `view_new.py` (which is in CSV format) and display them in a formatted manner.

Output:

```
| failure id |  build |   freq | total | first occ. | test                                                                             | title                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ---------- | ------ | ------ | ----- | ---------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|        506 |  31863 |     58 |     1 | 2023-06-23 | SIPartitionMovementTest.test_shadow_indexing                                     | <BadLogLines nodes=docker-rp-19(1) example=ERROR 2023-06-23 18:12:05                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
|        505 |  31849 |     58 |     1 | 2023-06-23 | SIPartitionMovementTest.test_cross_shard                                         | <BadLogLines nodes=docker-rp-23(1) example=ERROR 2023-06-23 15:06:18                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
...
|         40 |  20893 |    174 |     2 | 2023-01-10 | TestMirrorMakerService.test_simple_end_to_end                                    | TimeoutError(Consumer failed to consume up to offsets {TopicPartition(topic='topic-hzwsqofjgh'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|         59 |  19481 |    701 |     4 | 2022-12-05 | PartitionMovementUpgradeTest.test_basic_upgrade                                  | <BadLogLines nodes=docker-rp-15(1) example=ERROR 2022-12-21 23:18:04                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
```

Legend:

```
failure id  - ID of the failure (check `failures/491.json`)
build       - Buildkite's build (check [buildkite.com/redpanda/redpanda/builds/31233](https://buildkite.com/redpanda/redpanda/builds/31233))
freq        - Frequency of the failures (number of failures per 1 million)
total       - Total number of failures
first occ.  - First occurrence of the failure
title       - Title of the failure
test        - Failing test
```

#### New Occurrences of Closed Issues

List failures that keep happening after an issue is closed.

```
python3 view_issues.py --type reopen | csvcut -c "failure id","issue id","freq","total","last occ.","test","title" | csvlook -I | less -S
```

Output:

```
| failure id | issue id |  freq | total |  last occ. | test                                                                    | title                                                                                                                                                                                                                   |
| ---------- | -------- | ----- | ----- | ---------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|        309 |    10087 |   973 |    10 | 2023-05-02 | EndToEndShadowIndexingTestWithDisruptions.test_write_with_node_failures | CI Failure (connection refused to admin API) in `EndToEndShadowIndexingTestWithDisruptions`.`test_write_with_node_failures`                                                                                             |
|        238 |     7418 |  2799 |    32 | 2023-05-31 | ScalingUpTest.test_adding_nodes_to_cluster                              | CI Failure (partitions_rebalanced times out) in `ScalingUpTest`.`test_adding_nodes_to_cluster`                                                                                                                          |
...
|         33 |     8220 |  1049 |     6 | 2023-05-04 | PartitionBalancerTest.test_full_nodes                                   | Disk usage ratio check failing in `PartitionBalancerTest`.`test_full_nodes`                                                                                                                                             |
|          1 |     8421 |  1224 |     7 | 2023-06-02 | AvailabilityTests.test_availability_when_one_node_failed                | CI Failure (heap-use-after-free) in `AvailabilityTests.test_availability_when_one_node_failed`                                                                                                                          |
```

#### Top Failing Issues

```
python3 view_issues.py --type top | csvcut -c "failure id","issue id","freq","total","last occ.","test","title" | csvlook -I | less -S
```

Output:

```
| failure id | issue id |   freq | total |  last occ. | test                                                                             | title                                                                                                                                               |
| ---------- | -------- | ------ | ----- | ---------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
|        360 |    10849 |  37406 |    45 | 2023-05-18 | ShadowIndexingManyPartitionsTest.test_many_partitions_recovery                   | CI Failure (timeout waiting for `rpk cluster` to list 1 topic) in `ShadowIndexingManyPartitionsTest.test_many_partitions_recovery`                  |
|        446 |    11151 |  16949 |    17 | 2023-06-02 | CloudStorageChunkReadTest.test_read_when_segment_size_smaller_than_chunk_size    | CI Failure (TimeoutError) in `CloudStorageChunkReadTest.test_read_when_segment_size_smaller_than_chunk_size`                                        |
...
|        410 |    10935 |     43 |     1 | 2023-05-19 | PartitionBalancerTest.test_decommission                                          | CI Failure (Internal Server Error) in `PartitionBalancerTest.test_decommission`                                                                     |
|        426 |    11410 |     39 |     1 | 2023-05-25 | CompactionE2EIdempotencyTest.test_basic_compaction                               | CI Failure (consumers haven't finished) in `CompactionE2EIdempotencyTest.test_basic_compaction`                                                     |
```

#### First Occurrence of a Failure

This command is useful to chase a PR causing the problem.

```
python3 view_issues.py --type first | csvcut -c "failure id","issue id","freq","total","first occ.","test","title" | csvlook -I | less -S
```

Output:

```
| failure id | issue id |   freq | total | first occ. | test                                                                             | title                                                                                                                                               |
| ---------- | -------- | ------ | ----- | ---------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
|        499 |    11592 |    182 |     1 | 2023-06-21 | SchemaRegistryTest.test_restarts                                                 | CI Failure (Storage usage inconsistency) in `SchemaRegistryTest.schema_registry_test`                                                               |
|        498 |    11449 |    997 |     1 | 2023-06-21 | CloudStorageChunkReadTest.test_read_when_cache_smaller_than_segment_size         | CI Failure (KgoVerifier failed waiting for worker) in `CloudStorageChunkReadTest.test_read_when_cache_smaller_than_segment_size`                    |
...
|         78 |    11062 |    875 |    10 | 2022-12-13 | ScalingUpTest.test_adding_multiple_nodes_to_the_cluster                          | CI Failure (startup failure) in `ScalingUpTest.test_adding_multiple_nodes_to_the_cluster`                                                           |
|         42 |     8217 |   7990 |    91 | 2022-12-03 | ControllerEraseTest.test_erase_controller_log                                    | CI Failure (search victim assert) in `ControllerEraseTest.test_erase_controller_log`                                                                |
```

These results show the first occurrence of each failure, along with the associated issue and test information.

#### Last Occurrence of a Failure

```
python3 view_issues.py --type recent | csvcut -c "failure id","issue id","freq","total","last occ.","test","title" | csvlook -I | less -S
```

Output:

```
| failure id | issue id |   freq | total |  last occ. | test                                                                             | title                                                                                                                                               |
| ---------- | -------- | ------ | ----- | ---------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
|         78 |    11062 |    875 |    10 | 2023-06-23 | ScalingUpTest.test_adding_multiple_nodes_to_the_cluster                          | CI Failure (startup failure) in `ScalingUpTest.test_adding_multiple_nodes_to_the_cluster`                                                           |
|        161 |     8688 |   1263 |     7 | 2023-06-23 | ControllerUpgradeTest.test_updating_cluster_when_executing_operations            | CI Failure (Consumer failed to consume up to offsets) in `ControllerUpgradeTest.test_updating_cluster_when_executing_operations`                    |
...
|        303 |    10363 |    597 |     3 | 2023-05-04 | ConsumerOffsetsRecoveryToolTest.test_consumer_offsets_partition_count_change     | CI Failure (assertion error: groups not reported after migration) in `ConsumerOffsetsRecoveryToolTest.test_consumer_offsets_partition_count_change` |
|        221 |     9751 |    194 |     4 | 2023-04-05 | EndToEndTopicRecovery.test_restore                                               | CI Failure (timeout + UNKNOWN_TOPIC_OR_PARTITION) in `EndToEndTopicRecovery.test_restore`                                                           |
```

#### Stale Issues

A failure associated with the issues hasn't occurred within two months.

```
python3 view_issues.py --type stale | csvcut -c "failure id","issue id","freq","total","last occ.","test","title" | csvlook -I | less -S
```

Output:

```
| failure id | issue id | freq | total | last occ. | test | title |
| ---------- | -------- | ---- | ----- | --------- | ---- | ----- |
```
