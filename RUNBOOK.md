# Manual Failure and Recovery Exercise

This exercise is a local learning drill. It has **not been run or validated** as part of this initial version. Use disposable data, review every path before running a command, and record actual timings and observations.

## Goal

Demonstrate that an operator can create a consistent SQLite backup and restore it to a separate path after the working copy becomes unavailable. This exercise does not simulate full cloud or distributed-system recovery.

## Preparation

1. Choose a disposable SQLite database named `application.db`.
2. Create a `backups` directory if it does not exist.
3. Record the start time, database owner, expected tables, and a few non-sensitive record counts.
4. Confirm that `backups/application.db` and `recovered.db` do not exist. The CLI will refuse to overwrite them.

## Exercise

1. Create the backup:

   ```sh
   python3 reliability_lab.py backup application.db backups/application.db
   ```

2. Record the completion time, output path, and file size.
3. Simulate loss by making the working database unavailable in a reversible way, such as stopping the disposable application and renaming `application.db`. Do not delete the only copy.
4. Restore to a new path:

   ```sh
   python3 reliability_lab.py restore backups/application.db recovered.db
   ```

5. Point only the disposable application or a read-only inspection session at `recovered.db`.
6. Manually confirm the expected schema, key record counts, and application reads. Record discrepancies.
7. Record recovery duration and compare it with the intended recovery-time objective. Compare the backup timestamp with the failure time to estimate data exposure against the recovery-point objective.

## Rollback and cleanup

Stop the disposable application before switching database paths. Preserve the original, backup, restored copy, notes, and timestamps until the exercise is reviewed. Remove exercise artifacts only after a reviewer confirms they are no longer needed.

## Success criteria

- The backup and restore commands finish without overwriting an existing file.
- The restored database opens and contains the expected schema and records.
- Timings, observed data loss, discrepancies, and operator actions are documented.
- Any gap becomes a tracked follow-up before making broader recovery claims.
