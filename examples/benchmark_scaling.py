#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USMC Scaling & Concurrency Benchmark.

Measures single-agent write throughput, filtered read latency, composite context
assembly, and multi-agent concurrent write stress with ACID WAL guarantees.

Usage:
    python examples/benchmark_scaling.py [--iterations N] [--concurrent-ops N] [--json]
"""

import argparse
import concurrent.futures
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
from typing import Any, Dict, Optional

# Ensure repository root is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from usmc import USMCClient


def run_benchmark(
    db_path: Optional[Path] = None,
    iterations: int = 150,
    concurrent_ops: int = 30,
    verbose: bool = True
) -> Dict[str, Any]:
    """Runs the USMC performance and scaling benchmark suite.

    Args:
        db_path: Optional custom path to SQLite database. If None, uses a temporary DB.
        iterations: Number of sequential operations to execute for each benchmark phase.
        concurrent_ops: Number of operations each simulated agent executes during concurrency stress.
        verbose: Whether to print human-readable progress to stdout.

    Returns:
        Structured dictionary containing measured throughput and latency metrics.
    """
    is_temp = db_path is None
    temp_dir_obj = None

    if is_temp:
        temp_dir_obj = tempfile.TemporaryDirectory()
        actual_db = Path(temp_dir_obj.name) / "usmc_bench.db"
    else:
        actual_db = Path(db_path)

    try:
        primary_client = USMCClient(db_path=actual_db, agent_id="bench_primary")

        if verbose:
            print("================================================================")
            print(" USMC Performance & Concurrency Scaling Benchmark")
            print("================================================================")
            print(f" Database: {actual_db}")
            print(f" Iterations per phase: {iterations}")
            print(f" Concurrent ops per agent: {concurrent_ops} (4 agents)")
            print("----------------------------------------------------------------")

        # ----------------------------------------------------------------------
        # Phase 1: Sequential Discrete Fact Writes
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        for i in range(iterations):
            key = f"metric_{i % 25}"
            val = f"value_payload_{i}"
            primary_client.add_fact(
                category="project",
                key=key,
                value=val,
                confidence=0.85
            )
        t_fact_write = time.perf_counter() - t0
        fact_write_ops_sec = iterations / t_fact_write if t_fact_write > 0 else 0
        fact_write_ms = (t_fact_write * 1000) / iterations if iterations > 0 else 0

        if verbose:
            print(f" [1/5] Fact Writes       : {iterations:4d} ops in {t_fact_write:6.3f}s "
                  f"({fact_write_ops_sec:6.1f} ops/s, {fact_write_ms:5.2f} ms/op)")

        # ----------------------------------------------------------------------
        # Phase 2: Sequential Working Notes Writes
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        for i in range(iterations):
            shard_tag = f"shard_{i % 5}"
            primary_client.add_working(
                content=f"Working note execution trace {i} search_token_marker_{i % 20}",
                tags=f"bench,{shard_tag}",
                priority=(i % 3)
            )
        t_note_write = time.perf_counter() - t0
        note_write_ops_sec = iterations / t_note_write if t_note_write > 0 else 0
        note_write_ms = (t_note_write * 1000) / iterations if iterations > 0 else 0

        if verbose:
            print(f" [2/5] Note Writes       : {iterations:4d} ops in {t_note_write:6.3f}s "
                  f"({note_write_ops_sec:6.1f} ops/s, {note_write_ms:5.2f} ms/op)")

        # ----------------------------------------------------------------------
        # Phase 3: Filtered Reads (Indexed facts + tag/grep filtered notes)
        # ----------------------------------------------------------------------
        read_queries = max(50, iterations // 2)
        t0 = time.perf_counter()
        for i in range(read_queries):
            primary_client.get_facts(
                category="project",
                min_confidence=0.8
            )
        t_fact_read = time.perf_counter() - t0
        fact_qps = read_queries / t_fact_read if t_fact_read > 0 else 0
        fact_read_ms = (t_fact_read * 1000) / read_queries if read_queries > 0 else 0

        t0 = time.perf_counter()
        for i in range(read_queries):
            primary_client.get_working(
                limit=25,
                tags="shard_2",
                grep="search_token_marker"
            )
        t_note_read = time.perf_counter() - t0
        note_qps = read_queries / t_note_read if t_note_read > 0 else 0
        note_read_ms = (t_note_read * 1000) / read_queries if read_queries > 0 else 0

        if verbose:
            print(f" [3/5] Filtered Queries  : {read_queries:4d} fact queries in {t_fact_read:6.3f}s ({fact_qps:6.1f} QPS, {fact_read_ms:5.2f} ms/q)")
            print(f"                           {read_queries:4d} note queries in {t_note_read:6.3f}s ({note_qps:6.1f} QPS, {note_read_ms:5.2f} ms/q)")

        # ----------------------------------------------------------------------
        # Phase 4: Context Generation (Multi-table join & assembly)
        # ----------------------------------------------------------------------
        ctx_calls = max(20, iterations // 5)
        t0 = time.perf_counter()
        for _ in range(ctx_calls):
            primary_client.generate_context(max_items=10)
        t_ctx = time.perf_counter() - t0
        ctx_qps = ctx_calls / t_ctx if t_ctx > 0 else 0
        ctx_ms = (t_ctx * 1000) / ctx_calls if ctx_calls > 0 else 0

        if verbose:
            print(f" [4/5] Context Assembly  : {ctx_calls:4d} calls in {t_ctx:6.3f}s "
                  f"({ctx_qps:6.1f} calls/s, {ctx_ms:5.2f} ms/call)")

        # ----------------------------------------------------------------------
        # Phase 5: Multi-Agent Concurrency Stress Test (4 agents)
        # ----------------------------------------------------------------------
        agents = ["claude", "codex", "gemini", "kimi"]

        def _worker_task(agent_name: str) -> int:
            worker_client = USMCClient(db_path=actual_db, agent_id=agent_name)
            for j in range(concurrent_ops):
                worker_client.add_fact(
                    category="project",
                    key=f"{agent_name}_status_{j % 10}",
                    value=f"ok_state_{j}",
                    confidence=0.9
                )
                worker_client.add_working(
                    content=f"{agent_name} concurrent trace iteration {j}",
                    tags="concurrent,stress"
                )
            return concurrent_ops * 2

        t0 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = [executor.submit(_worker_task, a) for a in agents]
            results = [f.result() for f in futures]
        t_concurrent = time.perf_counter() - t0

        total_concurrent_ops = sum(results)
        concurrent_ops_sec = total_concurrent_ops / t_concurrent if t_concurrent > 0 else 0
        concurrent_ms = (t_concurrent * 1000) / total_concurrent_ops if total_concurrent_ops > 0 else 0

        if verbose:
            print(f" [5/5] Multi-Agent Stress: {total_concurrent_ops:4d} concurrent ops in {t_concurrent:6.3f}s "
                  f"({concurrent_ops_sec:6.1f} ops/s, {concurrent_ms:5.2f} ms/op across {len(agents)} agents)")

        # ----------------------------------------------------------------------
        # Database Integrity & Table Population Verification
        # ----------------------------------------------------------------------
        conn = sqlite3.connect(str(actual_db), timeout=5.0)
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            integrity_result = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM usmc_facts;")
            total_facts = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM usmc_working;")
            total_notes = cur.fetchone()[0]
        finally:
            conn.close()

        if verbose:
            print("----------------------------------------------------------------")
            print(f" Verification    : PRAGMA integrity_check = '{integrity_result}'")
            print(f" Final Records   : {total_facts} persistent facts, {total_notes} working notes")
            print("================================================================")

        return {
            "status": "PASS" if integrity_result == "ok" else "FAIL",
            "iterations": iterations,
            "concurrent_ops_per_agent": concurrent_ops,
            "agents_tested": agents,
            "metrics": {
                "fact_write_ops_per_sec": round(fact_write_ops_sec, 2),
                "fact_write_ms_per_op": round(fact_write_ms, 2),
                "note_write_ops_per_sec": round(note_write_ops_sec, 2),
                "note_write_ms_per_op": round(note_write_ms, 2),
                "fact_query_qps": round(fact_qps, 2),
                "fact_query_ms": round(fact_read_ms, 2),
                "note_search_qps": round(note_qps, 2),
                "note_search_ms": round(note_read_ms, 2),
                "context_gen_qps": round(ctx_qps, 2),
                "context_gen_ms": round(ctx_ms, 2),
                "concurrent_ops_per_sec": round(concurrent_ops_sec, 2),
                "concurrent_ms_per_op": round(concurrent_ms, 2),
                "integrity_check": integrity_result,
                "total_facts": total_facts,
                "total_notes": total_notes,
            }
        }
    finally:
        if temp_dir_obj is not None:
            # Let garbage collection complete SQLite cleanup before removing temp dir
            import gc
            gc.collect()
            try:
                temp_dir_obj.cleanup()
            except OSError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="USMC Performance & Concurrency Scaling Benchmark")
    parser.add_argument("--iterations", type=int, default=150, help="Number of iterations per sequential phase (default: 150)")
    parser.add_argument("--concurrent-ops", type=int, default=30, help="Concurrent ops per agent (default: 30)")
    parser.add_argument("--db", type=str, default=None, help="Optional database path (default: temporary in-memory/tempfile)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    db_path = Path(args.db) if args.db else None
    verbose = not (args.json or args.quiet)

    results = run_benchmark(
        db_path=db_path,
        iterations=args.iterations,
        concurrent_ops=args.concurrent_ops,
        verbose=verbose
    )

    if args.json:
        print(json.dumps(results, indent=2))

    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
