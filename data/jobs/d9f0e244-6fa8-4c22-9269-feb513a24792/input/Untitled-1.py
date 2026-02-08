#!/usr/bin/env python3
"""
epochly_bench.py

Async HTTP benchmark for a URL (default: https://www.epochly.co).
Measures latency distributions and throughput under concurrency.

Requirements:
  pip install aiohttp

Examples:
  python epochly_bench.py
  python epochly_bench.py --url https://www.epochly.co --concurrency 50 --requests 2000
  python epochly_bench.py --method HEAD --requests 1000 --concurrency 100
  python epochly_bench.py --url https://www.epochly.co/some/path --requests 5000 --concurrency 200 --timeout 10
"""

from __future__ import annotations

import argparse
import asyncio
import math
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

import aiohttp


@dataclass
class Result:
    ok: bool
    status: int
    elapsed_s: float
    bytes_read: int
    error: Optional[str] = None


def percentile(sorted_vals: List[float], p: float) -> float:
    """p in [0,100]. Uses linear interpolation between closest ranks."""
    if not sorted_vals:
        return float("nan")
    if p <= 0:
        return sorted_vals[0]
    if p >= 100:
        return sorted_vals[-1]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


def format_ms(s: float) -> str:
    return f"{s * 1000:.2f} ms"


def human_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    for u in units:
        if f < 1024.0 or u == units[-1]:
            return f"{f:.2f} {u}" if u != "B" else f"{int(f)} {u}"
        f /= 1024.0
    return f"{n} B"


async def fetch_one(
    session: aiohttp.ClientSession,
    url: str,
    method: str,
    timeout_s: float,
    max_bytes: int,
    allow_redirects: bool,
    headers: Dict[str, str],
) -> Result:
    t0 = time.perf_counter()
    bytes_read = 0
    status = 0
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_s)
        async with session.request(
            method=method,
            url=url,
            timeout=timeout,
            allow_redirects=allow_redirects,
            headers=headers,
        ) as resp:
            status = resp.status

            # Read up to max_bytes (or all if max_bytes == 0)
            if method.upper() != "HEAD":
                if max_bytes == 0:
                    body = await resp.read()
                    bytes_read = len(body)
                else:
                    # Stream chunks until reaching max_bytes
                    async for chunk in resp.content.iter_chunked(64 * 1024):
                        bytes_read += len(chunk)
                        if bytes_read >= max_bytes:
                            break

            t1 = time.perf_counter()
            ok = 200 <= status < 400
            return Result(ok=ok, status=status, elapsed_s=(t1 - t0), bytes_read=bytes_read)
    except asyncio.TimeoutError:
        t1 = time.perf_counter()
        return Result(ok=False, status=status, elapsed_s=(t1 - t0), bytes_read=bytes_read, error="timeout")
    except aiohttp.ClientError as e:
        t1 = time.perf_counter()
        return Result(ok=False, status=status, elapsed_s=(t1 - t0), bytes_read=bytes_read, error=f"client_error: {e}")
    except Exception as e:
        t1 = time.perf_counter()
        return Result(ok=False, status=status, elapsed_s=(t1 - t0), bytes_read=bytes_read, error=f"error: {e}")


async def worker(
    wid: int,
    session: aiohttp.ClientSession,
    url: str,
    method: str,
    timeout_s: float,
    max_bytes: int,
    allow_redirects: bool,
    headers: Dict[str, str],
    queue: asyncio.Queue,
    results: List[Result],
):
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            return
        res = await fetch_one(session, url, method, timeout_s, max_bytes, allow_redirects, headers)
        results.append(res)
        queue.task_done()


def print_histogram(lat_ms: List[float]) -> None:
    if not lat_ms:
        return
    # 10 buckets between min and p99 (avoid extreme outliers)
    vals = sorted(lat_ms)
    lo = vals[0]
    hi = percentile(vals, 99.0)
    if hi <= lo:
        hi = vals[-1]
    if hi <= lo:
        return

    buckets = 10
    step = (hi - lo) / buckets
    counts = [0] * buckets
    for v in lat_ms:
        if v < lo:
            idx = 0
        elif v >= hi:
            idx = buckets - 1
        else:
            idx = int((v - lo) / step)
            idx = min(max(idx, 0), buckets - 1)
        counts[idx] += 1

    maxc = max(counts) or 1
    print("\nLatency histogram (ms):")
    for i, c in enumerate(counts):
        a = lo + i * step
        b = lo + (i + 1) * step
        bar_len = int((c / maxc) * 40)
        bar = "#" * bar_len
        print(f"  {a:8.1f} - {b:8.1f} | {bar} ({c})")


def summarize(results: List[Result], total_time_s: float) -> None:
    total = len(results)
    ok = sum(1 for r in results if r.ok)
    errs = total - ok

    status_counts: Dict[int, int] = {}
    err_types: Dict[str, int] = {}
    total_bytes = 0

    latencies = []
    for r in results:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
        if r.error:
            err_types[r.error] = err_types.get(r.error, 0) + 1
        total_bytes += r.bytes_read
        latencies.append(r.elapsed_s)

    l_sorted = sorted(latencies)
    avg = statistics.fmean(l_sorted) if l_sorted else float("nan")
    med = percentile(l_sorted, 50.0)
    p95 = percentile(l_sorted, 95.0)
    p99 = percentile(l_sorted, 99.0)
    mn = l_sorted[0] if l_sorted else float("nan")
    mx = l_sorted[-1] if l_sorted else float("nan")

    rps = (total / total_time_s) if total_time_s > 0 else float("nan")
    ok_rps = (ok / total_time_s) if total_time_s > 0 else float("nan")
    mbps = (total_bytes * 8 / 1_000_000 / total_time_s) if total_time_s > 0 else float("nan")

    print("\n=== Summary ===")
    print(f"Requests:        {total}")
    print(f"OK (2xx/3xx):    {ok}")
    print(f"Errors:          {errs}")
    print(f"Total time:      {total_time_s:.3f} s")
    print(f"Throughput:      {rps:.2f} req/s (OK: {ok_rps:.2f} req/s)")
    print(f"Downloaded:      {human_bytes(total_bytes)} total, {mbps:.2f} Mbit/s")

    print("\nLatency:")
    print(f"  min: {format_ms(mn)}")
    print(f"  avg: {format_ms(avg)}")
    print(f"  med: {format_ms(med)}")
    print(f"  p95: {format_ms(p95)}")
    print(f"  p99: {format_ms(p99)}")
    print(f"  max: {format_ms(mx)}")

    # Status distribution
    print("\nHTTP status counts (top):")
    for st, c in sorted(status_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]:
        print(f"  {st}: {c}")

    if err_types:
        print("\nError types:")
        for e, c in sorted(err_types.items(), key=lambda kv: -kv[1]):
            print(f"  {e}: {c}")

    # Histogram in ms
    lat_ms = [x * 1000 for x in l_sorted]
    print_histogram(lat_ms)


async def run_bench(args: argparse.Namespace) -> int:
    url = args.url
    method = args.method.upper()

    # Default headers that resemble a browser (often avoids simplistic blocks)
    headers: Dict[str, str] = {}
    if not args.no_default_headers:
        headers.update(
            {
                "User-Agent": "Mozilla/5.0 (benchmark; aiohttp) epochly_bench/1.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }
        )
    for kv in args.header:
        if ":" not in kv:
            print(f"Invalid header '{kv}'. Use 'Key: Value'.", file=sys.stderr)
            return 2
        k, v = kv.split(":", 1)
        headers[k.strip()] = v.strip()

    conn = aiohttp.TCPConnector(limit=0, ssl=args.verify_ssl)
    results: List[Result] = []

    async with aiohttp.ClientSession(connector=conn) as session:
        # Optional warmup
        if args.warmup > 0:
            for _ in range(args.warmup):
                _ = await fetch_one(
                    session, url, method, args.timeout, args.max_bytes, args.redirects, headers
                )

        queue: asyncio.Queue = asyncio.Queue()
        for _ in range(args.requests):
            queue.put_nowait(1)
        for _ in range(args.concurrency):
            queue.put_nowait(None)

        workers = [
            asyncio.create_task(
                worker(
                    i,
                    session,
                    url,
                    method,
                    args.timeout,
                    args.max_bytes,
                    args.redirects,
                    headers,
                    queue,
                    results,
                )
            )
            for i in range(args.concurrency)
        ]

        t0 = time.perf_counter()
        await queue.join()
        t1 = time.perf_counter()

        for w in workers:
            await w

    summarize(results, total_time_s=(t1 - t0))
    # Exit non-zero if too many errors
    err_rate = (sum(1 for r in results if not r.ok) / len(results)) if results else 0.0
    if err_rate > args.fail_error_rate:
        print(f"\nFailing: error rate {err_rate:.2%} > {args.fail_error_rate:.2%}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Benchmark a URL (latency + throughput).")
    p.add_argument("--url", default="https://www.epochly.co", help="Target URL")
    p.add_argument("--method", default="GET", choices=["GET", "HEAD"], help="HTTP method")
    p.add_argument("--requests", type=int, default=500, help="Total requests to send")
    p.add_argument("--concurrency", type=int, default=50, help="Number of concurrent workers")
    p.add_argument("--timeout", type=float, default=15.0, help="Per-request timeout (seconds)")
    p.add_argument("--warmup", type=int, default=20, help="Warmup requests (not counted)")
    p.add_argument("--max-bytes", type=int, default=0, help="Read up to N bytes per response (0 = read all)")
    p.add_argument("--redirects", action="store_true", help="Follow redirects")
    p.add_argument("--verify-ssl", action="store_true", help="Verify SSL certificates (default: off for speed)")
    p.add_argument("--no-default-headers", action="store_true", help="Do not send default browser-like headers")
    p.add_argument("--header", action="append", default=[], help="Extra header 'Key: Value' (repeatable)")
    p.add_argument(
        "--fail-error-rate",
        type=float,
        default=0.05,
        help="Exit 1 if error rate exceeds this fraction (default 0.05)",
    )
    args = p.parse_args()

    if args.concurrency <= 0 or args.requests <= 0:
        print("concurrency and requests must be > 0", file=sys.stderr)
        return 2

    try:
        return asyncio.run(run_bench(args))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())