# Payroll Pipeline Performance Lab

An end-to-end PostgreSQL and Python demo that loads one million synthetic payroll records and compares query plans for a monthly department report.

## Run locally

Use Docker Compose and Python 3.10 or later in a fresh environment.

```sh
docker compose up -d
docker compose exec db pg_isready -U payroll -d payroll
python -m pip install -r requirements.txt
python benchmark.py
```

Run the readiness check until PostgreSQL accepts connections. On subsequent runs the load skips existing record IDs. The script checks that the baseline and indexed reports return identical counts and totals.

## Read the plans

The report filters one pay period and groups payroll amounts by department. The covering index leads with the period, adds the grouping column, and includes the amount needed to compute the total.

Compare scan type, execution time, buffer activity, and any heap fetches. PostgreSQL chooses the plan. Cache state, table visibility, and hardware affect the measurements. The index also consumes storage and adds work to writes when installed on a live table.

The benchmark rolls back its index changes and retains the synthetic records for repeat runs. Use `docker compose down` to stop the local database.

## Benchmark results

Measured on PostgreSQL 17.4 on Windows with 1,000,000 synthetic payroll records.

| Run | Baseline | With covering index |
| --- | ---: | ---: |
| Initial load | 42.04 ms | 8.17 ms |
| Repeat run | 39.10 ms | 8.46 ms |

PostgreSQL switched from a parallel sequential scan to a bitmap index scan
followed by a bitmap heap scan. Both plans returned identical counts and
payroll totals for all 29 departments. The repeat run inserted zero new rows.

Times are from `EXPLAIN ANALYZE` for the report query. They exclude data loading
and index creation and will vary by environment.
