# Cloud Reliability Lab

This is a minimal, local lab for practicing two reliability tasks: making and restoring consistent SQLite backups, and calculating a small service-level objective (SLO) report from request observations. It uses Python's standard library and has no user interface or external service dependency.

This is an **initial, unvalidated version**. Its commands and the exercise below have not been run as part of delivery.

## Requirements

- Python 3.9 or newer
- A local SQLite database for the backup exercise

## Commands

Run these from this directory.

```sh
python3 reliability_lab.py backup application.db backups/application.db
python3 reliability_lab.py restore backups/application.db recovered.db
python3 reliability_lab.py slo-report sample-data/synthetic_requests.csv
```

Set different SLO targets when needed:

```sh
python3 reliability_lab.py slo-report observations.csv \
  --availability-target 99.95 \
  --latency-target-ms 250
```

The backup and restore commands refuse to overwrite an existing destination. Create its parent directory first. A failed copy removes the incomplete destination when possible.

## CSV schema

The input must be UTF-8 CSV with a header and these exact columns:

| Column | Meaning | Example |
| --- | --- | --- |
| `timestamp` | ISO 8601 timestamp; `Z` is accepted | `2026-01-01T12:00:00Z` |
| `status` | Integer HTTP-style status from 100 through 599 | `200` |
| `latency_ms` | Non-negative request duration in milliseconds | `123.4` |

Rows that cannot be parsed are skipped with a warning. An empty file, a header-only file, or a file with no valid rows produces an explicit “unavailable” report instead of dividing by zero.

Availability and latency answer different questions. Availability is the share of all valid requests with status 200–399. Latency is the nearest-rank p95 of successful requests only. A service can meet one target and miss the other, so the report evaluates them separately. Failed requests do not improve or worsen the latency figure; they affect availability.

The included CSV is **synthetic sample data** for learning and demonstration. It is not production evidence.

## Limits

- This lab copies one local SQLite database with SQLite's online backup API.
- It does not schedule backups, encrypt files, upload data, manage retention, verify replicas, or coordinate distributed systems.
- It does not establish disaster recovery readiness or prove cloud recovery. Real recovery needs tested infrastructure, access, dependencies, data reconciliation, recovery-time and recovery-point objectives, and repeated exercises.
- The SLO report is a simple batch calculation. It has no time-window grouping, traffic weighting, error-budget policy, telemetry ingestion, or alerting.
- Small samples can make p95 values misleading. Interpret the sample count with the result.

See [RUNBOOK.md](RUNBOOK.md) for a manual failure and recovery exercise.
