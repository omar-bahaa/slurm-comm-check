#!/usr/bin/env python3
"""Torch distributed communication benchmark for Slurm multi-node GPU jobs."""

from __future__ import annotations

import json
import math
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

import torch
import torch.distributed as dist


def parse_int_list(value: str) -> list[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def summarize_elapsed(samples: list[dict[str, Any]]) -> dict[str, Any]:
    elapsed = [sample["elapsed_s"] for sample in samples if sample.get("elapsed_s") is not None]
    bandwidth = [
        sample["bandwidth_gbps"]
        for sample in samples
        if sample.get("bandwidth_gbps") is not None
    ]
    summary: dict[str, Any] = {
        "ranks_reported": len(samples),
        "ranks_measured": len(elapsed),
        "elapsed_min_s": min(elapsed) if elapsed else None,
        "elapsed_mean_s": sum(elapsed) / len(elapsed) if elapsed else None,
        "elapsed_p50_s": percentile(elapsed, 0.50),
        "elapsed_p95_s": percentile(elapsed, 0.95),
        "elapsed_max_s": max(elapsed) if elapsed else None,
        "bandwidth_mean_gbps": sum(bandwidth) / len(bandwidth) if bandwidth else None,
        "bandwidth_min_gbps": min(bandwidth) if bandwidth else None,
    }
    if elapsed:
        slowest = sorted(
            (sample for sample in samples if sample.get("elapsed_s") is not None),
            key=lambda sample: sample["elapsed_s"],
            reverse=True,
        )[:8]
        summary["slowest_ranks"] = [
            {
                "rank": sample["rank"],
                "local_rank": sample["local_rank"],
                "host": sample["host"],
                "elapsed_s": sample["elapsed_s"],
            }
            for sample in slowest
        ]
    return summary


def run_command(command: list[str], timeout_s: int = 30) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_s,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "elapsed_s": time.perf_counter() - start,
            "output": completed.stdout[-12000:],
        }
    except Exception as exc:  # noqa: BLE001 - health checks must report exact failure.
        return {
            "command": command,
            "returncode": None,
            "elapsed_s": time.perf_counter() - start,
            "error": repr(exc),
        }


def collect_rank_object(obj: dict[str, Any]) -> list[dict[str, Any]] | None:
    gathered: list[dict[str, Any]] | None
    if dist.get_rank() == 0:
        gathered = [None for _ in range(dist.get_world_size())]  # type: ignore[list-item]
    else:
        gathered = None
    dist.gather_object(obj, gathered, dst=0)
    return gathered


def dtype_nbytes(dtype: torch.dtype) -> int:
    return torch.empty((), dtype=dtype).element_size()


class CommBenchmark:
    def __init__(self) -> None:
        self.local_rank = int(os.environ["LOCAL_RANK"])
        self.rank = int(os.environ["RANK"])
        self.world_size = int(os.environ["WORLD_SIZE"])
        self.gpus_per_node = int(os.environ.get("GPUS_PER_NODE", "8"))
        self.node_rank = int(os.environ.get("GROUP_RANK", os.environ.get("NODE_RANK", "0")))
        self.host = socket.gethostname().split(".")[0]
        self.device = torch.device(f"cuda:{self.local_rank}")
        self.dtype = torch.float16
        self.warmup_iters = int(os.environ.get("COMM_WARMUP_ITERS", "2"))
        self.measure_iters = int(os.environ.get("COMM_MEASURE_ITERS", "5"))
        self.timeout_minutes = int(os.environ.get("COMM_TIMEOUT_MINUTES", "20"))
        self.rocm_path = os.environ.get("ROCM_PATH", "/opt/rocm-7.0.0")
        self.sizes_bytes = parse_int_list(
            os.environ.get(
                "COMM_SIZES_BYTES",
                "4,4096,1048576,16777216,67108864",
            )
        )
        self.gather_sizes_bytes = parse_int_list(
            os.environ.get("COMM_GATHER_SIZES_BYTES", "4,4096,1048576")
        )
        self.subgroup_sizes_bytes = parse_int_list(
            os.environ.get("COMM_SUBGROUP_SIZES_BYTES", "4,1048576,16777216")
        )
        self.metrics: list[dict[str, Any]] = []
        self.rank_health: dict[str, Any] = {}

    def log(self, message: str) -> None:
        print(
            f"[host={self.host} rank={self.rank} local_rank={self.local_rank}] {message}",
            flush=True,
        )

    def tensor_for_bytes(self, size_bytes: int) -> torch.Tensor:
        elements = max(1, math.ceil(size_bytes / dtype_nbytes(self.dtype)))
        return torch.ones(elements, device=self.device, dtype=self.dtype)

    def setup(self) -> None:
        torch.cuda.set_device(self.local_rank)
        self.rank_health = {
            "rank": self.rank,
            "local_rank": self.local_rank,
            "node_rank": self.node_rank,
            "host": self.host,
            "python": sys.version,
            "platform": platform.platform(),
            "torch_version": torch.__version__,
            "torch_hip": getattr(torch.version, "hip", None),
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
            "device_name": torch.cuda.get_device_name(self.local_rank),
            "rocm_path": self.rocm_path,
            "rocm_path_exists": Path(self.rocm_path).exists(),
            "rocm_smi": run_command(["rocm-smi"], timeout_s=45),
            "env": {
                "MASTER_ADDR": os.environ.get("MASTER_ADDR"),
                "MASTER_PORT": os.environ.get("MASTER_PORT"),
                "ROCM_PATH": os.environ.get("ROCM_PATH"),
                "NCCL_P2P_DISABLE": os.environ.get("NCCL_P2P_DISABLE"),
                "NCCL_IB_HCA": os.environ.get("NCCL_IB_HCA"),
                "NCCL_SOCKET_IFNAME": os.environ.get("NCCL_SOCKET_IFNAME"),
                "NCCL_CROSS_NIC": os.environ.get("NCCL_CROSS_NIC"),
                "ROCR_VISIBLE_DEVICES": os.environ.get("ROCR_VISIBLE_DEVICES"),
            },
        }

        init_start = time.perf_counter()
        dist.init_process_group(
            backend="nccl",
            timeout=timedelta(minutes=self.timeout_minutes),
        )
        torch.cuda.synchronize()
        init_elapsed = time.perf_counter() - init_start
        self.record_point("init_process_group", init_elapsed, bytes_count=0)

        barrier_start = time.perf_counter()
        dist.barrier(device_ids=[self.local_rank])
        torch.cuda.synchronize()
        self.record_point("first_barrier", time.perf_counter() - barrier_start, bytes_count=0)

    def record_point(
        self,
        name: str,
        elapsed_s: float | None,
        *,
        bytes_count: int,
        scope: str = "global",
        group_name: str = "world",
        measured: bool = True,
    ) -> None:
        bandwidth_gbps = None
        if elapsed_s and bytes_count > 0:
            bandwidth_gbps = (bytes_count * 8.0) / elapsed_s / 1e9
        sample = {
            "op": name,
            "scope": scope,
            "group": group_name,
            "bytes": bytes_count,
            "rank": self.rank,
            "local_rank": self.local_rank,
            "node_rank": self.node_rank,
            "host": self.host,
            "elapsed_s": elapsed_s,
            "bandwidth_gbps": bandwidth_gbps,
            "measured": measured,
        }
        gathered = collect_rank_object(sample)
        if self.rank == 0 and gathered is not None:
            self.metrics.append(
                {
                    "op": name,
                    "scope": scope,
                    "group": group_name,
                    "bytes": bytes_count,
                    "samples": gathered,
                    "summary": summarize_elapsed(gathered),
                }
            )

    def time_callable(self, fn, *, barrier_group=None, global_sync: bool = True) -> float:
        for _ in range(self.warmup_iters):
            fn()
        torch.cuda.synchronize()
        if global_sync:
            dist.barrier(device_ids=[self.local_rank])
        elif barrier_group is not None:
            dist.barrier(group=barrier_group, device_ids=[self.local_rank])
        start = time.perf_counter()
        for _ in range(self.measure_iters):
            fn()
        torch.cuda.synchronize()
        if global_sync:
            dist.barrier(device_ids=[self.local_rank])
        elif barrier_group is not None:
            dist.barrier(group=barrier_group, device_ids=[self.local_rank])
        return (time.perf_counter() - start) / self.measure_iters

    def bench_barrier(self) -> None:
        elapsed = self.time_callable(lambda: dist.barrier(device_ids=[self.local_rank]))
        self.record_point("barrier", elapsed, bytes_count=0)

    def bench_all_reduce(self, size_bytes: int, group=None, scope: str = "global", group_name: str = "world") -> None:
        tensor = self.tensor_for_bytes(size_bytes)

        def run() -> None:
            tensor.fill_(1)
            dist.all_reduce(tensor, group=group)

        elapsed = self.time_callable(run)
        self.record_point("all_reduce", elapsed, bytes_count=tensor.numel() * tensor.element_size(), scope=scope, group_name=group_name)

    def bench_broadcast(self, size_bytes: int) -> None:
        tensor = self.tensor_for_bytes(size_bytes)

        def run() -> None:
            tensor.fill_(float(self.rank + 1))
            dist.broadcast(tensor, src=0)

        elapsed = self.time_callable(run)
        self.record_point("broadcast", elapsed, bytes_count=tensor.numel() * tensor.element_size())

    def bench_all_gather(self, size_bytes: int) -> None:
        tensor = self.tensor_for_bytes(size_bytes)
        gathered = [torch.empty_like(tensor) for _ in range(self.world_size)]

        def run() -> None:
            tensor.fill_(float(self.rank + 1))
            dist.all_gather(gathered, tensor)

        elapsed = self.time_callable(run)
        bytes_count = tensor.numel() * tensor.element_size() * self.world_size
        self.record_point("all_gather", elapsed, bytes_count=bytes_count)

    def bench_reduce_scatter(self, size_bytes: int) -> None:
        output = self.tensor_for_bytes(size_bytes)
        chunks = [torch.ones_like(output) for _ in range(self.world_size)]

        def run() -> None:
            dist.reduce_scatter(output, chunks)

        elapsed = self.time_callable(run)
        bytes_count = output.numel() * output.element_size() * self.world_size
        self.record_point("reduce_scatter", elapsed, bytes_count=bytes_count)

    def bench_ring_p2p(self, size_bytes: int) -> None:
        send = self.tensor_for_bytes(size_bytes)
        recv = torch.empty_like(send)
        next_rank = (self.rank + 1) % self.world_size
        prev_rank = (self.rank - 1) % self.world_size

        def run() -> None:
            ops = [
                dist.P2POp(dist.isend, send, next_rank),
                dist.P2POp(dist.irecv, recv, prev_rank),
            ]
            for request in dist.batch_isend_irecv(ops):
                request.wait()

        elapsed = self.time_callable(run)
        self.record_point("ring_p2p", elapsed, bytes_count=send.numel() * send.element_size())

    def bench_pair_p2p(self, size_bytes: int) -> None:
        send = self.tensor_for_bytes(size_bytes)
        recv = torch.empty_like(send)
        partner = self.rank ^ 1
        if partner >= self.world_size:
            self.record_point(
                "pair_p2p",
                None,
                bytes_count=send.numel() * send.element_size(),
                measured=False,
            )
            return

        def run() -> None:
            ops = [
                dist.P2POp(dist.isend, send, partner),
                dist.P2POp(dist.irecv, recv, partner),
            ]
            for request in dist.batch_isend_irecv(ops):
                request.wait()

        elapsed = self.time_callable(run)
        self.record_point("pair_p2p", elapsed, bytes_count=send.numel() * send.element_size())

    def create_groups(self) -> tuple[dict[str, Any], dict[str, Any]]:
        node_groups = {}
        for node in range(math.ceil(self.world_size / self.gpus_per_node)):
            ranks = list(range(node * self.gpus_per_node, min((node + 1) * self.gpus_per_node, self.world_size)))
            node_groups[f"node_{node}"] = {
                "ranks": ranks,
                "group": dist.new_group(ranks=ranks),
            }

        local_rank_groups = {}
        for local_rank in range(self.gpus_per_node):
            ranks = [
                node * self.gpus_per_node + local_rank
                for node in range(math.ceil(self.world_size / self.gpus_per_node))
                if node * self.gpus_per_node + local_rank < self.world_size
            ]
            local_rank_groups[f"local_rank_{local_rank}"] = {
                "ranks": ranks,
                "group": dist.new_group(ranks=ranks),
            }

        dist.barrier(device_ids=[self.local_rank])
        return node_groups, local_rank_groups

    def bench_group_all_reduce(
        self,
        groups: dict[str, Any],
        *,
        scope: str,
        sizes: list[int],
    ) -> None:
        for group_name, group_info in groups.items():
            in_group = self.rank in group_info["ranks"]
            for size_bytes in sizes:
                dist.barrier(device_ids=[self.local_rank])
                tensor = self.tensor_for_bytes(size_bytes)
                elapsed = None
                if in_group:
                    def run() -> None:
                        tensor.fill_(1)
                        dist.all_reduce(tensor, group=group_info["group"])

                    elapsed = self.time_callable(
                        run,
                        barrier_group=group_info["group"],
                        global_sync=False,
                    )
                dist.barrier(device_ids=[self.local_rank])
                self.record_point(
                    "all_reduce",
                    elapsed,
                    bytes_count=tensor.numel() * tensor.element_size(),
                    scope=scope,
                    group_name=group_name,
                    measured=in_group,
                )

    def run(self) -> None:
        self.setup()
        self.log(
            "benchmark start "
            f"world_size={self.world_size} sizes={self.sizes_bytes} "
            f"gather_sizes={self.gather_sizes_bytes}"
        )

        self.bench_barrier()
        for size_bytes in self.sizes_bytes:
            self.bench_all_reduce(size_bytes)
            self.bench_broadcast(size_bytes)
            self.bench_ring_p2p(size_bytes)
            self.bench_pair_p2p(size_bytes)

        for size_bytes in self.gather_sizes_bytes:
            self.bench_all_gather(size_bytes)
            self.bench_reduce_scatter(size_bytes)

        node_groups, local_rank_groups = self.create_groups()
        self.bench_group_all_reduce(node_groups, scope="node_local", sizes=self.subgroup_sizes_bytes)
        self.bench_group_all_reduce(local_rank_groups, scope="same_local_rank_cross_node", sizes=self.subgroup_sizes_bytes)

        rank_health = collect_rank_object(self.rank_health)
        if self.rank == 0:
            output = {
                "metadata": {
                    "world_size": self.world_size,
                    "gpus_per_node": self.gpus_per_node,
                    "num_nodes": math.ceil(self.world_size / self.gpus_per_node),
                    "master_addr": os.environ.get("MASTER_ADDR"),
                    "master_port": os.environ.get("MASTER_PORT"),
                    "warmup_iters": self.warmup_iters,
                    "measure_iters": self.measure_iters,
                    "sizes_bytes": self.sizes_bytes,
                    "gather_sizes_bytes": self.gather_sizes_bytes,
                    "subgroup_sizes_bytes": self.subgroup_sizes_bytes,
                    "rocm_path": self.rocm_path,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
                "rank_health": rank_health,
                "metrics": self.metrics,
            }
            output_path = Path(os.environ["COMM_OUTPUT_JSON"])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(output, indent=2, sort_keys=True))
            self.log(f"wrote {output_path}")

        dist.barrier(device_ids=[self.local_rank])
        dist.destroy_process_group()
        self.log("benchmark complete")


def main() -> None:
    benchmark = CommBenchmark()
    benchmark.run()


if __name__ == "__main__":
    main()
