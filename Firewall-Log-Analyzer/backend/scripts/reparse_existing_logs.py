"""
Re-parse existing stored logs to backfill newly-added parsed fields.

Use-case:
  You added new fields like destination_ip / source_port to your log schema,
  but old MongoDB documents don't have them. This script re-parses each
  document's raw_log using the existing parser routing logic and updates the
  document with any missing fields.

Safety:
  - Dry-run by default (no DB updates unless you pass --apply)
  - By default only fills fields that are missing/None/empty
  - Batch writes via bulk_write for performance

Run:
  cd backend
  export MONGO_URI="..."
  PYTHONPATH=. python3 scripts/reparse_existing_logs.py --apply

Examples:
  # Show what would change (no writes)
  PYTHONPATH=. python3 scripts/reparse_existing_logs.py

  # Apply changes, process at most 10k docs
  PYTHONPATH=. python3 scripts/reparse_existing_logs.py --apply --limit 10000

  # Overwrite existing values too (not recommended unless you know why)
  PYTHONPATH=. python3 scripts/reparse_existing_logs.py --apply --overwrite
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pymongo import UpdateOne

# Ensure imports work when running as a script (python3 scripts/...)
# Adds backend/ to sys.path so `import app...` resolves.
_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.db.mongo import logs_collection
from app.services.log_parser_service import parse_log_line


FIELDS_TO_BACKFILL = (
    "destination_ip",
    "source_port",
    # These are also frequently missing in old docs; we can safely backfill when absent.
    "destination_port",
    "protocol",
)


def _is_missing_value(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and v.strip() == "":
        return True
    return False


def _build_update(doc: Dict[str, Any], parsed: Dict[str, Any], overwrite: bool) -> Dict[str, Any]:
    """
    Build a $set update doc containing only the fields we want to backfill.
    """
    update: Dict[str, Any] = {}
    for field in FIELDS_TO_BACKFILL:
        if field not in parsed:
            continue

        parsed_val = parsed.get(field)
        if _is_missing_value(parsed_val):
            continue

        if overwrite:
            update[field] = parsed_val
            continue

        # Only fill if missing/None/empty in stored doc
        if field not in doc or _is_missing_value(doc.get(field)):
            update[field] = parsed_val
    return update


def _iter_candidate_docs(limit: Optional[int]) -> Iterable[Dict[str, Any]]:
    """
    Find docs that are most likely to benefit from backfill.
    """
    query = {
        "raw_log": {"$exists": True, "$ne": ""},
        "$or": [
            {"destination_ip": {"$exists": False}},
            {"source_port": {"$exists": False}},
            {"destination_ip": None},
            {"source_port": None},
        ],
    }

    projection = {
        "_id": 1,
        "raw_log": 1,
        "log_source": 1,
        "destination_ip": 1,
        "source_port": 1,
        "destination_port": 1,
        "protocol": 1,
    }

    cursor = logs_collection.find(query, projection=projection).batch_size(1000)
    if limit is not None:
        cursor = cursor.limit(int(limit))
    return cursor


def run_migration(*, apply: bool, overwrite: bool, limit: Optional[int], batch_size: int) -> Dict[str, int]:
    processed = 0
    parsed_ok = 0
    parse_failed = 0
    would_update = 0
    updated = 0

    ops: List[UpdateOne] = []

    for doc in _iter_candidate_docs(limit=limit):
        processed += 1

        raw_log = doc.get("raw_log") or ""
        log_source = doc.get("log_source")

        parsed = parse_log_line(raw_log, log_source)
        if not parsed:
            parse_failed += 1
            continue

        parsed_ok += 1
        update_fields = _build_update(doc, parsed, overwrite=overwrite)
        if not update_fields:
            continue

        would_update += 1
        ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": update_fields}))

        if len(ops) >= batch_size:
            if apply:
                result = logs_collection.bulk_write(ops, ordered=False)
                updated += int(result.modified_count or 0)
            ops = []

    # flush
    if ops:
        if apply:
            result = logs_collection.bulk_write(ops, ordered=False)
            updated += int(result.modified_count or 0)

    return {
        "processed": processed,
        "parsed_ok": parsed_ok,
        "parse_failed": parse_failed,
        "would_update": would_update,
        "updated": updated if apply else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill destination_ip/source_port by re-parsing raw logs")
    parser.add_argument("--apply", action="store_true", help="Apply updates to MongoDB (default: dry-run)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing field values (default: only fill missing)")
    parser.add_argument("--limit", type=int, default=None, help="Max documents to process (default: all candidates)")
    parser.add_argument("--batch-size", type=int, default=1000, help="Bulk write batch size (default: 1000)")
    args = parser.parse_args()

    stats = run_migration(
        apply=bool(args.apply),
        overwrite=bool(args.overwrite),
        limit=args.limit,
        batch_size=int(args.batch_size),
    )

    mode = "APPLY" if args.apply else "DRY_RUN"
    print(f"[{mode}] Completed re-parse migration")
    for k, v in stats.items():
        print(f"- {k}: {v}")

    if not args.apply:
        print("Dry-run only. Re-run with --apply to persist changes.")


if __name__ == "__main__":
    main()


