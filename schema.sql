CREATE TABLE IF NOT EXISTS payroll (
    record_id integer PRIMARY KEY,
    pay_period date NOT NULL CHECK (EXTRACT(DAY FROM pay_period) = 1),
    department_id integer NOT NULL CHECK (department_id > 0),
    gross_cents integer NOT NULL CHECK (gross_cents >= 0)
);
