"""Load synthetic payroll records and compare PostgreSQL query plans."""

import os
from pathlib import Path

import psycopg

DSN = os.getenv("PAYROLL_DSN", "postgresql://payroll:payroll@localhost:55432/payroll")
PERIOD = "2025-12-01"
REPORT = """
SELECT department_id, count(*), sum(gross_cents)
FROM payroll
WHERE pay_period = %s::date
GROUP BY department_id
ORDER BY department_id
"""
LOAD = """
INSERT INTO payroll (record_id, pay_period, department_id, gross_cents)
SELECT id, (DATE '2020-01-01' + (id % 72) * INTERVAL '1 month')::date,
       1 + id % 29, 200000 + id % 900000
FROM generate_series(1, 1000000) AS records(id)
ON CONFLICT (record_id) DO NOTHING
"""


def explain(connection, label):
    print(f"\n{label}")
    plan = connection.execute("EXPLAIN (ANALYZE, BUFFERS) " + REPORT, (PERIOD,))
    for (line,) in plan:
        print(line)


def main():
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8-sig")
    with psycopg.connect(DSN) as connection:
        connection.execute(schema)
        inserted = connection.execute(LOAD).rowcount
        connection.execute("ANALYZE payroll")
        print(f"Inserted {inserted:,} synthetic payroll records.")

        # Roll back the benchmark's index changes after collecting both plans.
        connection.execute("SAVEPOINT benchmark")
        connection.execute("DROP INDEX IF EXISTS payroll_period_department_idx")
        baseline = connection.execute(REPORT, (PERIOD,)).fetchall()
        explain(connection, "Baseline")
        connection.execute("""
            CREATE INDEX payroll_period_department_idx
            ON payroll (pay_period, department_id) INCLUDE (gross_cents)
        """)
        indexed = connection.execute(REPORT, (PERIOD,)).fetchall()
        explain(connection, "With covering index")
        if baseline != indexed:
            raise RuntimeError("The report results changed after indexing.")
        print(f"Verified matching totals for {len(indexed)} departments.")
        connection.execute("ROLLBACK TO SAVEPOINT benchmark")


if __name__ == "__main__":
    main()
