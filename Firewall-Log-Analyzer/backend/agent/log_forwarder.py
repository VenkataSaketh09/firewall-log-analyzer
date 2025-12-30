#!/usr/bin/env python3
"""
Remote log forwarding agent for Firewall Log Analyzer.

Tails one or more local log files and forwards raw log lines to the central
HTTP ingestion endpoint: POST /api/logs/ingest

Designed to be run on many VMs.
"""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests


@dataclass(frozen=True)
class SourceConfig:
    file_path: str
    log_source: str


def _open_for_follow(path: str):
    f = open(path, "r", encoding="utf-8", errors="replace")
    f.seek(0, os.SEEK_END)
    return f


def follow_file(path: str, poll_seconds: float = 0.5) -> Iterable[str]:
    """
    Tail a file like `tail -F` (handles truncation and rotation best-effort).
    """
    f = _open_for_follow(path)
    try:
        last_inode = os.fstat(f.fileno()).st_ino
        while True:
            line = f.readline()
            if line:
                yield line.rstrip("\n")
                continue

            # No data; detect rotation/truncation
            try:
                st = os.stat(path)
                if st.st_ino != last_inode:
                    f.close()
                    f = _open_for_follow(path)
                    last_inode = os.fstat(f.fileno()).st_ino
                else:
                    # Truncation: file shrunk, restart from beginning
                    if st.st_size < f.tell():
                        f.seek(0)
            except FileNotFoundError:
                # During rotation, file may temporarily disappear
                pass

            time.sleep(poll_seconds)
    finally:
        try:
            f.close()
        except Exception:
            pass


def post_batch(
    session: requests.Session,
    endpoint: str,
    api_key: str,
    log_source: str,
    lines: List[str],
    timeout_seconds: int = 10,
) -> None:
    resp = session.post(
        endpoint.rstrip("/"),
        json={"logs": lines, "log_source": log_source},
        headers={"X-API-Key": api_key},
        timeout=timeout_seconds,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")


def run_source(
    cfg: SourceConfig,
    endpoint: str,
    api_key: str,
    batch_size: int,
    flush_seconds: float,
    max_backoff_seconds: float = 30.0,
):
    session = requests.Session()
    buf: List[str] = []
    last_flush = time.time()
    backoff = 1.0

    print(f"[forwarder] following {cfg.file_path} as log_source={cfg.log_source}")

    for line in follow_file(cfg.file_path):
        buf.append(line)
        now = time.time()

        should_flush = len(buf) >= batch_size or (buf and (now - last_flush) >= flush_seconds)
        if not should_flush:
            continue

        while True:
            try:
                post_batch(session, endpoint, api_key, cfg.log_source, buf)
                buf.clear()
                last_flush = time.time()
                backoff = 1.0
                break
            except Exception as e:
                # retry with backoff
                print(f"[forwarder] send failed ({cfg.log_source}): {e}; retrying in {backoff:.1f}s")
                time.sleep(backoff)
                backoff = min(backoff * 2.0, max_backoff_seconds)


def parse_sources(args: argparse.Namespace) -> List[SourceConfig]:
    out: List[SourceConfig] = []
    for spec in args.source:
        # format: /path/to/file:log_source
        if ":" not in spec:
            raise ValueError(f"Invalid --source '{spec}'. Expected /path/to/file:log_source")
        path, log_source = spec.split(":", 1)
        if not path:
            raise ValueError(f"Invalid --source '{spec}': empty path")
        if not log_source:
            raise ValueError(f"Invalid --source '{spec}': empty log_source")
        out.append(SourceConfig(file_path=path, log_source=log_source))
    return out


def main():
    parser = argparse.ArgumentParser(description="Firewall Log Analyzer - Remote Log Forwarding Agent")
    parser.add_argument(
        "--endpoint",
        default=os.getenv("FLA_INGEST_URL", "http://localhost:8000/api/logs/ingest"),
        help="Ingestion endpoint URL (env: FLA_INGEST_URL)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("FLA_API_KEY"),
        help="API key for ingestion (env: FLA_API_KEY)",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Log source mapping: /path/to/file:log_source (repeatable). Example: /var/log/auth.log:auth.log",
    )
    parser.add_argument("--batch-size", type=int, default=200, help="Max lines per request")
    parser.add_argument("--flush-seconds", type=float, default=2.0, help="Flush interval even if batch not full")

    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Missing --api-key (or env FLA_API_KEY)")

    sources = parse_sources(args)
    if not sources:
        # sensible defaults for Ubuntu/Debian
        sources = [
            SourceConfig("/var/log/auth.log", "auth.log"),
            SourceConfig("/var/log/ufw.log", "ufw.log"),
        ]

    # One process per file is simplest; use os.fork-less approach via threads.
    import threading

    threads = []
    for cfg in sources:
        t = threading.Thread(
            target=run_source,
            args=(cfg, args.endpoint, args.api_key, args.batch_size, args.flush_seconds),
            daemon=True,
        )
        t.start()
        threads.append(t)

    print(f"[forwarder] started {len(threads)} source thread(s); posting to {args.endpoint}")
    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()


