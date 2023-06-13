
## Configuration

Set CI DB credentials (environment variables):

* `CI_DB_HOST`
* `CI_DB_USER`
* `CI_DB_PWD`

Search for "Redpanda Test Results DB" on wiki

### Dependencies

* `pip3 install sh`
* install [gh](https://cli.github.com/)

## Usage

Use gh to set its credentials

Correlate issues & failures

```
# create dirs
mkdir -p builds failures issues workspace

# fetch the database and store it locally in `builds` as json files
# follow up execution will fetch only the delta
python3 fetch_builds.py

# fetch all ci-issues open and closed and store it locally in `issues`
NO_COLOR=1 python3 fetch_issues.py

# group all test failures by (test name, stacktrace) + trivial key word heuristic
# and store them in `failures`; ideally there is 1:1 mapping between failures and
# issues
python3 process_builds.py

# extract essential info from issues: class, method, creation & modification time,
# state and links to failing builds
python3 process_issues.py

# correlate failures with issues and enrich failure with issue info
python3 process_failures.py

# classify failures into: active, new, should reopen issue, stale failure
python3 analysis.py
```

### New failures

```
# list failures which doesn't have corresponding issues
python3 view_new.py
```

Output

```
485     2023-06-12      1       7288
484     2023-06-12      1       5292
483     2023-06-12      1       5286
480     2023-06-11      2       5307
...
202     2023-02-23      3       8966
142     2023-01-27      9       5329
124     2023-01-10      2       10673
```

Legend

```
485        - id of a failure, check `failures/485.json`
2023-06-12 - first occurrence of a failure
1          - number of failures
7288       - number of passes
```

### Resurrection of closed issue

```
# list failures which keep happening after an issue is closed
python3 view_reopen.py
```

Output

```
164     2023-06-12      6       5326
153     2023-06-12      26      17923
...
311     2023-05-02      10      9518
123     2023-04-15      19      17923
```

Legend

```
164        - id of a failure, check `failures/164.json`
2023-06-12 - last occurance of a failure
6          - number of failures
5326       - number of passes
```

### Top active failures

```
python3 view_active_top.py
```

Output

```
3       87      10582   2023-06-12
429     87      1941    2023-06-13
370     76      7197    2023-06-13
...
476     1       5286    2023-06-10
478     1       5337    2023-06-11
482     1       105253  2023-06-12
```

Legend

```
3          - id of a failure, check `failures/3.json`
87         - number of failures
2023-06-12 - last occurance of a failure
10582      - number of passes
```