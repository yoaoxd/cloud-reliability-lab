#!/usr/bin/env python3
"""Small, local reliability exercises using only the Python standard library."""

from __future__ import annotations

import argparse
import csv
import math
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def unused_path(path: str) -> Path:
    candidate = Path(path).expanduser()
    if candidate.exists():
        raise ValueError(f"refusing to overwrite existing path: {candidate}")
    if not candidate.parent.exists():
        raise ValueError(f"parent directory does not exist: {candidate.parent}")
    return candidate


def existing_file(path: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_file():
        raise ValueError(f"file does not exist: {candidate}")
    return candidate


def copy_database(source: Path, destination: Path) -> None:
    source_uri = f"file:{source.resolve()}?mode=ro"
    try:
        with sqlite3.connect(source_uri, uri=True) as source_db:
            source_db.execute("PRAGMA schema_version").fetchone()
            with sqlite3.connect(destination) as destination_db:
                source_db.backup(destination_db)
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def backup(args: argparse.Namespace) -> int:
    source = existing_file(args.database)
    destination = unused_path(args.output)
    copy_database(source, destination)
    print(f"Backup created: {destination}")
    return 0


def restore(args: argparse.Namespace) -> int:
    source = existing_file(args.backup)
    destination = unused_path(args.database)
    copy_database(source, destination)
    print(f"Database restored: {destination}")
    return 0


def parse_timestamp(value: str) -> None:
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def percentile_nearest_rank(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def slo_report(args: argparse.Namespace) -> int:
    csv_path = existing_file(args.csv_file)
    total = 0
    available = 0
    successful_latencies: list[float] = []
    invalid_rows = 0

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"timestamp", "status", "latency_ms"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

        for row_number, row in enumerate(reader, start=2):
            try:
                parse_timestamp(row["timestamp"])
                status = int(row["status"])
                latency = float(row["latency_ms"])
                if not 100 <= status <= 599 or latency < 0 or not math.isfinite(latency):
                    raise ValueError
            except (TypeError, ValueError):
                invalid_rows += 1
                print(f"Warning: skipped invalid row {row_number}", file=sys.stderr)
                continue

            total += 1
            if 200 <= status <= 399:
                available += 1
                successful_latencies.append(latency)

    print("SLO report")
    print(f"Valid requests: {total}")
    print(f"Invalid rows skipped: {invalid_rows}")
    if total == 0:
        print("Availability: unavailable (no valid requests)")
        print("Latency: unavailable (no successful requests)")
        return 0

    availability = available / total * 100
    print(f"Availability: {availability:.3f}% ({available}/{total})")
    print(f"Availability target: {args.availability_target:.3f}% — {'PASS' if availability >= args.availability_target else 'FAIL'}")

    if not successful_latencies:
        print("Latency: unavailable (no successful requests)")
        print("Latency target: NOT EVALUATED")
        return 0

    p95 = percentile_nearest_rank(successful_latencies, 0.95)
    print(f"Successful-request p95 latency: {p95:.2f} ms ({len(successful_latencies)} samples)")
    print(f"Latency target: <= {args.latency_target_ms:.2f} ms — {'PASS' if p95 <= args.latency_target_ms else 'FAIL'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    backup_parser = commands.add_parser("backup", help="create a consistent SQLite backup")
    backup_parser.add_argument("database", help="existing SQLite database")
    backup_parser.add_argument("output", help="new backup path")
    backup_parser.set_defaults(function=backup)

    restore_parser = commands.add_parser("restore", help="restore a backup to a new SQLite database")
    restore_parser.add_argument("backup", help="existing SQLite backup")
    restore_parser.add_argument("database", help="new database path")
    restore_parser.set_defaults(function=restore)

    report_parser = commands.add_parser("slo-report", help="report availability and latency from CSV")
    report_parser.add_argument("csv_file", help="request observations CSV")
    report_parser.add_argument("--availability-target", type=float, default=99.9, help="target percentage (default: 99.9)")
    report_parser.add_argument("--latency-target-ms", type=float, default=300.0, help="p95 target in milliseconds (default: 300)")
    report_parser.set_defaults(function=slo_report)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    availability_target = getattr(args, "availability_target", 0.0)
    latency_target = getattr(args, "latency_target_ms", 0.0)
    if not math.isfinite(availability_target) or not 0 <= availability_target <= 100:
        parser.error("--availability-target must be between 0 and 100")
    if not math.isfinite(latency_target) or latency_target < 0:
        parser.error("--latency-target-ms must be non-negative")
    try:
        return args.function(args)
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
