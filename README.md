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

When you already used the tool and pull new version you should execute `python3 index.py --reindex` once. If
it fails then wipe the whole state out `rm -rf data` and start from scratch `python3 index.py`.

### Duplicates

The tool expects that each failure (a set of test fails with same test name and stacktrace) has an associated
ci-issue. Sometimes different tests may fail for the same reasons so when we're sure about it we may mark
one issue as a duplicate of another.

If an issue #xxx fails for the same reason as #yyy then we may mark #xxx as duplicate by closing and adding
a comment to it (don't forget, it's a code markdown block which includes tripple 0x60 chars):

```
{
    "duplicate": "https://github.com/redpanda-data/redpanda/issues/yyy"
}
```

### Rogue failing build

Sometime a rogue ci build causes a lot of errors which should be ignored (e.g. a responsible PR is identified and
rolled back). In this case edit `.ciignore.json` to exclude that build and restart `python3 index.py --reindex`.

### Commands

#### New failures

```
# list failures which doesn't have corresponding issues
python3 view_new.py | csvcut -c "failure id","build","freq","total","first occ.","test","title" | csvlook -q '"' -d "," | less -S
```

By tuning the csvcut's args you may control which columns to display.

Output

```
| failure id |  build |   freq | total | first occ. | test                                                                             | title                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ---------- | ------ | ------ | ----- | ---------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|        506 | 31,863 |     58 |     1 | 2023-06-23 | SIPartitionMovementTest.test_shadow_indexing                                     | <BadLogLines nodes=docker-rp-19(1) example=ERROR 2023-06-23 18:12:05                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
|        505 | 31,849 |     58 |     1 | 2023-06-23 | SIPartitionMovementTest.test_cross_shard                                         | <BadLogLines nodes=docker-rp-23(1) example=ERROR 2023-06-23 15:06:18                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
...
|         40 | 20,893 |    174 |     2 | 2023-01-10 | TestMirrorMakerService.test_simple_end_to_end                                    | TimeoutError(Consumer failed to consume up to offsets {TopicPartition(topic='topic-hzwsqofjgh'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|         59 | 19,481 |    701 |     4 | 2022-12-05 | PartitionMovementUpgradeTest.test_basic_upgrade                                  | <BadLogLines nodes=docker-rp-15(1) example=ERROR 2022-12-21 23:18:04                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
```

Legend

```
f-id       - id of a failure, check `failures/491.json`
build      - buildkite's build, check https://buildkite.com/redpanda/redpanda/builds/31233
freq       - frequency of the fails (number of failures per 1MM)
total      - total number of fails
first occ. - first occurrence of the failure
title      - failure's title
test       - failing test
```

### Come back of old resolved issues

```
# list failures which keep happening after an issue is closed
python3 view_issues.py --type reopen | csvcut -c "failure id","issue id","freq","total","last occ.","test","title" | csvlook | less -S
```

Output

```
| failure id | issue id |  freq | total |  last occ. | test                                                                    | title                                                                                                                                                                                                                   |
| ---------- | -------- | ----- | ----- | ---------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|        309 |   10,087 |   973 |    10 | 2023-05-02 | EndToEndShadowIndexingTestWithDisruptions.test_write_with_node_failures | CI Failure (connection refused to admin API) in `EndToEndShadowIndexingTestWithDisruptions`.`test_write_with_node_failures`                                                                                             |
|        238 |    7,418 | 2,799 |    32 | 2023-05-31 | ScalingUpTest.test_adding_nodes_to_cluster                              | CI Failure (partitions_rebalanced times out) in `ScalingUpTest`.`test_adding_nodes_to_cluster`                                                                                                                          |
...
|         33 |    8,220 | 1,049 |     6 | 2023-05-04 | PartitionBalancerTest.test_full_nodes                                   | Disk usage ratio check failing in `PartitionBalancerTest`.`test_full_nodes`                                                                                                                                             |
|          1 |    8,421 | 1,224 |     7 | 2023-06-02 | AvailabilityTests.test_availability_when_one_node_failed                | CI Failure (heap-use-after-free) in `AvailabilityTests.test_availability_when_one_node_failed`                                                                                                                          |

```

#### Top failing issues

```
python3 view_issues.py --type top | csvcut -c "failure id","issue id","freq","total","last occ.","test","title" | csvlook | less -S
```

Output

```
| failure id | issue id |   freq | total |  last occ. | test                                                                             | title                                                                                                                                               |
| ---------- | -------- | ------ | ----- | ---------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
|        360 |   10,849 | 37,406 |    45 | 2023-05-18 | ShadowIndexingManyPartitionsTest.test_many_partitions_recovery                   | CI Failure (timeout waiting for `rpk cluster` to list 1 topic) in `ShadowIndexingManyPartitionsTest.test_many_partitions_recovery`                  |
|        446 |   11,151 | 16,949 |    17 | 2023-06-02 | CloudStorageChunkReadTest.test_read_when_segment_size_smaller_than_chunk_size    | CI Failure (TimeoutError) in `CloudStorageChunkReadTest.test_read_when_segment_size_smaller_than_chunk_size`                                        |
...
|        410 |   10,935 |     43 |     1 | 2023-05-19 | PartitionBalancerTest.test_decommission                                          | CI Failure (Internal Server Error) in `PartitionBalancerTest.test_decommission`                                                                     |
|        426 |   11,410 |     39 |     1 | 2023-05-25 | CompactionE2EIdempotencyTest.test_basic_compaction                               | CI Failure (consumers haven't finished) in `CompactionE2EIdempotencyTest.test_basic_compaction`                                                     |
```

#### First occurrence of a failure

The command is usefull to chase a PR causing the problem.

```
python3 view_issues.py --type first | csvcut -c "failure id","issue id","freq","total","first occ.","test","title" | csvlook | less -S
```

```
| failure id | issue id |   freq | total | first occ. | test                                                                             | title                                                                                                                                               |
| ---------- | -------- | ------ | ----- | ---------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
|        499 |   11,592 |    182 |     1 | 2023-06-21 | SchemaRegistryTest.test_restarts                                                 | CI Failure (Storage usage inconsistency) in `SchemaRegistryTest.schema_registry_test`                                                               |
|        498 |   11,449 |    997 |     1 | 2023-06-21 | CloudStorageChunkReadTest.test_read_when_cache_smaller_than_segment_size         | CI Failure (KgoVerifier failed waiting for worker) in `CloudStorageChunkReadTest.test_read_when_cache_smaller_than_segment_size`                    |
...
|         78 |   11,062 |    875 |    10 | 2022-12-13 | ScalingUpTest.test_adding_multiple_nodes_to_the_cluster                          | CI Failure (startup failure) in `ScalingUpTest.test_adding_multiple_nodes_to_the_cluster`                                                           |
|         42 |    8,217 |  7,990 |    91 | 2022-12-03 | ControllerEraseTest.test_erase_controller_log                                    | CI Failure (search victim assert) in `ControllerEraseTest.test_erase_controller_log`                                                                |
```

#### Last occurrence of a failure

```
python3 view_issues.py --type recent | csvcut -c "failure id","issue id","freq","total","last occ.","test","title" | csvlook | less -S
```

```
| failure id | issue id |   freq | total |  last occ. | test                                                                             | title                                                                                                                                               |
| ---------- | -------- | ------ | ----- | ---------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
|         78 |   11,062 |    875 |    10 | 2023-06-23 | ScalingUpTest.test_adding_multiple_nodes_to_the_cluster                          | CI Failure (startup failure) in `ScalingUpTest.test_adding_multiple_nodes_to_the_cluster`                                                           |
|        161 |    8,688 |  1,263 |     7 | 2023-06-23 | ControllerUpgradeTest.test_updating_cluster_when_executing_operations            | CI Failure (Consumer failed to consume up to offsets) in `ControllerUpgradeTest.test_updating_cluster_when_executing_operations`                    |
...
|        303 |   10,363 |    597 |     3 | 2023-05-04 | ConsumerOffsetsRecoveryToolTest.test_consumer_offsets_partition_count_change     | CI Failure (assertion error: groups not reported after migration) in `ConsumerOffsetsRecoveryToolTest.test_consumer_offsets_partition_count_change` |
|        221 |    9,751 |    194 |     4 | 2023-04-05 | EndToEndTopicRecovery.test_restore                                               | CI Failure (timeout + UNKNOWN_TOPIC_OR_PARTITION) in `EndToEndTopicRecovery.test_restore`                                                           |

```

#### Stale issues

A failure associated with the issues hasn't failed within two months

```
python3 view_issues.py --type stale | csvcut -c "failure id","issue id","freq","total","last occ.","test","title" | csvlook | less -S
```

```
| failure id | issue id | freq | total | last occ. | test | title |
| ---------- | -------- | ---- | ----- | --------- | ---- | ----- |
```
