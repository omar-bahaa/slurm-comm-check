#!/usr/bin/env python3
"""Summarize structured communication benchmark output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def fmt_seconds(value: float | None) -> str:
    if value is None:
        return "n/a"
    if value < 0.001:
        return f"{value * 1e6:.1f} us"
    if value < 1:
        return f"{value * 1e3:.2f} ms"
    return f"{value:.3f} s"


def fmt_gbps(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f} Gb/s"


def health_failures(
    rank_health: list[dict[str, Any]],
    expected_gpus_per_node: int | None,
) -> list[str]:
    failures = []
    seen_hosts = {}
    for item in rank_health:
        host = item["host"]
        host_info = seen_hosts.setdefault(
            host,
            {
                "rocm_path_exists": item.get("rocm_path_exists"),
                "rocm_smi_returncode": item.get("rocm_smi", {}).get("returncode"),
                "torch_hip": item.get("torch_hip"),
                "device_count": item.get("device_count"),
                "rocm_path": item.get("rocm_path") or item.get("env", {}).get("ROCM_PATH"),
            },
        )
        if host_info["rocm_path_exists"] is not True:
            failures.append(f"{host}: ROCm path missing ({host_info['rocm_path']})")
        if host_info["rocm_smi_returncode"] != 0:
            failures.append(f"{host}: rocm-smi failed rc={host_info['rocm_smi_returncode']}")
        if (
            expected_gpus_per_node is not None
            and (
                host_info["device_count"] is None
                or host_info["device_count"] < expected_gpus_per_node
            )
        ):
            failures.append(
                f"{host}: torch sees {host_info['device_count']} GPUs; "
                f"expected {expected_gpus_per_node}"
            )
    return sorted(set(failures))


def metric_key(metric: dict[str, Any]) -> tuple[str, str, str, int]:
    return (
        metric["scope"],
        metric["group"],
        metric["op"],
        int(metric["bytes"]),
    )


def suspicious_metrics(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    suspicious = []
    for metric in metrics:
        summary = metric["summary"]
        p95 = summary.get("elapsed_p95_s")
        max_s = summary.get("elapsed_max_s")
        bandwidth_min = summary.get("bandwidth_min_gbps")
        size_bytes = int(metric["bytes"])
        op = metric["op"]
        if p95 is None:
            continue
        if size_bytes <= 1_048_576 and p95 > 0.005:
            suspicious.append(metric)
        elif op in {"barrier", "init_process_group", "first_barrier"} and max_s and max_s > 20.0:
            suspicious.append(metric)
        elif size_bytes >= 16_777_216 and p95 > 0.050:
            suspicious.append(metric)
        elif size_bytes >= 1_048_576 and bandwidth_min is not None and bandwidth_min < 5.0:
            suspicious.append(metric)
    return suspicious


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    metrics_path = run_dir / "comm_metrics.json"
    if not metrics_path.exists():
        raise SystemExit(f"missing metrics file: {metrics_path}")

    data = json.loads(metrics_path.read_text())
    metadata = data["metadata"]
    rank_health = data.get("rank_health") or []
    metrics = sorted(data["metrics"], key=metric_key)

    lines = [
        "# Communication Benchmark Summary",
        "",
        f"Run directory: `{run_dir}`",
        f"World size: {metadata['world_size']} ranks",
        f"Nodes: {metadata['num_nodes']}",
        f"GPUs per node: {metadata['gpus_per_node']}",
        f"Master: {metadata['master_addr']}:{metadata['master_port']}",
        f"Warmup iterations: {metadata['warmup_iters']}",
        f"Measurement iterations: {metadata['measure_iters']}",
        "",
        "## Node Health",
        "",
    ]

    failures = health_failures(rank_health, metadata.get("gpus_per_node"))
    if failures:
        lines.extend(f"- FAIL: {failure}" for failure in failures)
    else:
        hosts = sorted({item["host"] for item in rank_health})
        lines.append(
            f"- PASS: ROCm path, `rocm-smi`, and torch device checks passed on {len(hosts)} hosts."
        )

    lines.extend(["", "## Slow Or Failed Metrics", ""])
    suspicious = suspicious_metrics(metrics)
    if suspicious:
        for metric in suspicious[:80]:
            summary = metric["summary"]
            slowest = summary.get("slowest_ranks", [])
            slowest_text = ", ".join(
                f"r{item['rank']}@{item['host']}={fmt_seconds(item['elapsed_s'])}"
                for item in slowest[:4]
            )
            lines.append(
                "- "
                f"{metric['scope']}/{metric['group']}/{metric['op']} "
                f"bytes={metric['bytes']} "
                f"p95={fmt_seconds(summary.get('elapsed_p95_s'))} "
                f"max={fmt_seconds(summary.get('elapsed_max_s'))} "
                f"bw_min={fmt_gbps(summary.get('bandwidth_min_gbps'))} "
                f"slowest=[{slowest_text}]"
            )
    else:
        lines.append("- No metrics crossed the built-in suspicious thresholds.")

    lines.extend(["", "## Metric Table", ""])
    lines.append("| Scope | Group | Op | Bytes | p50 | p95 | max | mean BW | min BW |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|")
    for metric in metrics:
        summary = metric["summary"]
        lines.append(
            "| "
            f"{metric['scope']} | {metric['group']} | {metric['op']} | {metric['bytes']} | "
            f"{fmt_seconds(summary.get('elapsed_p50_s'))} | "
            f"{fmt_seconds(summary.get('elapsed_p95_s'))} | "
            f"{fmt_seconds(summary.get('elapsed_max_s'))} | "
            f"{fmt_gbps(summary.get('bandwidth_mean_gbps'))} | "
            f"{fmt_gbps(summary.get('bandwidth_min_gbps'))} |"
        )

    summary_path = run_dir / "summary.txt"
    summary_path.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
