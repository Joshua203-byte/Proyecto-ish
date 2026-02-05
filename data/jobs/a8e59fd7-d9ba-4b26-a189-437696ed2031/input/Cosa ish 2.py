#!/usr/bin/env python3
"""
dgx_bench.py - GPU training benchmark for NVIDIA systems (DGX, etc.)

Modes:
  - synthetic: maximize compute throughput (no dataloader/disk bottleneck)
  - cifar10: real training workload (downloads CIFAR-10)

Supports:
  - single GPU / multi-GPU (DDP via torchrun)
  - fp32 / fp16 / bf16 mixed precision
  - optional torch.compile
  - NVML power/utilization sampling when available

Examples:
  Single GPU, synthetic:
    python dgx_bench.py --mode synthetic --batch-size 512 --steps 500 --precision fp16

  Single GPU, CIFAR-10:
    python dgx_bench.py --mode cifar10 --epochs 5 --batch-size 256 --precision fp16

  Multi-GPU (8 GPUs), synthetic:
    torchrun --nproc_per_node=8 dgx_bench.py --mode synthetic --batch-size 512 --steps 500 --precision fp16 --ddp

  Multi-GPU (8 GPUs), CIFAR-10:
    torchrun --nproc_per_node=8 dgx_bench.py --mode cifar10 --epochs 5 --batch-size 256 --precision fp16 --ddp
"""

import os
import time
import math
import argparse
from dataclasses import dataclass
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.optim as optim

# Optional imports (only needed for CIFAR-10 mode)
try:
    import torchvision
    import torchvision.transforms as T
except Exception:
    torchvision = None

# Optional NVML for power/utilization
try:
    import pynvml
    _HAS_NVML = True
except Exception:
    _HAS_NVML = False


@dataclass
class NvmlStats:
    gpu_util: float
    mem_util: float
    power_w: float
    temp_c: float


class NvmlMonitor:
    def __init__(self, local_rank: int = 0):
        self.local_rank = local_rank
        self.enabled = False
        self.handle = None
        if _HAS_NVML:
            try:
                pynvml.nvmlInit()
                self.handle = pynvml.nvmlDeviceGetHandleByIndex(local_rank)
                self.enabled = True
            except Exception:
                self.enabled = False

    def sample(self) -> Optional[NvmlStats]:
        if not self.enabled:
            return None
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
            mem = util.memory
            gpu = util.gpu
            power_mw = pynvml.nvmlDeviceGetPowerUsage(self.handle)  # milliwatts
            temp = pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)
            return NvmlStats(
                gpu_util=float(gpu),
                mem_util=float(mem),
                power_w=float(power_mw) / 1000.0,
                temp_c=float(temp),
            )
        except Exception:
            return None

    def shutdown(self):
        if self.enabled:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass


def is_ddp_enabled(args) -> bool:
    return args.ddp and int(os.environ.get("WORLD_SIZE", "1")) > 1


def ddp_setup() -> Tuple[int, int, int]:
    """
    Returns (rank, local_rank, world_size).
    Assumes torchrun sets env vars: RANK, LOCAL_RANK, WORLD_SIZE.
    """
    rank = int(os.environ.get("RANK", "0"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    world_size = int(os.environ.get("WORLD_SIZE", "1"))

    if world_size > 1:
        torch.distributed.init_process_group(backend="nccl")
        torch.cuda.set_device(local_rank)

    return rank, local_rank, world_size


def ddp_cleanup(world_size: int):
    if world_size > 1:
        try:
            torch.distributed.destroy_process_group()
        except Exception:
            pass


def get_device(local_rank: int) -> torch.device:
    if torch.cuda.is_available():
        return torch.device(f"cuda:{local_rank}")
    return torch.device("cpu")


def get_autocast_dtype(precision: str) -> Optional[torch.dtype]:
    precision = precision.lower()
    if precision == "fp16":
        return torch.float16
    if precision == "bf16":
        return torch.bfloat16
    if precision == "fp32":
        return None
    raise ValueError("precision must be one of: fp32, fp16, bf16")


def build_model(num_classes: int = 10) -> nn.Module:
    # ResNet-18 is a nice, stable baseline benchmark
    if torchvision is None:
        # Minimal fallback model if torchvision isn't installed
        return nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(128, num_classes),
        )

    model = torchvision.models.resnet18(num_classes=num_classes)
    return model


def make_cifar10_loader(batch_size: int, workers: int, ddp: bool, rank: int, world_size: int):
    if torchvision is None:
        raise RuntimeError("torchvision is required for --mode cifar10. Install torchvision or use --mode synthetic.")

    transform = T.Compose([
        T.RandomCrop(32, padding=4),
        T.RandomHorizontalFlip(),
        T.ToTensor(),
    ])
    dataset = torchvision.datasets.CIFAR10(root="./data", train=True, download=True, transform=transform)

    sampler = None
    if ddp:
        sampler = torch.utils.data.distributed.DistributedSampler(dataset, num_replicas=world_size, rank=rank, shuffle=True)

    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=(sampler is None),
        sampler=sampler,
        num_workers=workers,
        pin_memory=True,
        persistent_workers=(workers > 0),
        drop_last=True,
    )
    return loader, sampler


def synthetic_batch(batch_size: int, device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
    # Mimics CIFAR-10 shape to keep model realistic
    x = torch.randn(batch_size, 3, 32, 32, device=device)
    y = torch.randint(0, 10, (batch_size,), device=device)
    return x, y


@torch.no_grad()
def warmup_cuda():
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def reduce_scalar_ddp(value: float, device: torch.device, world_size: int) -> float:
    if world_size <= 1:
        return value
    t = torch.tensor([value], device=device, dtype=torch.float64)
    torch.distributed.all_reduce(t, op=torch.distributed.ReduceOp.SUM)
    t /= world_size
    return float(t.item())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["synthetic", "cifar10"], default="synthetic",
                        help="synthetic = max compute; cifar10 = real training workload")
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=2, help="used for cifar10 mode")
    parser.add_argument("--steps", type=int, default=500, help="used for synthetic mode")
    parser.add_argument("--workers", type=int, default=8, help="dataloader workers for cifar10")
    parser.add_argument("--precision", choices=["fp32", "fp16", "bf16"], default="fp16")
    parser.add_argument("--lr", type=float, default=0.1)
    parser.add_argument("--compile", action="store_true", help="use torch.compile (PyTorch 2.x)")
    parser.add_argument("--ddp", action="store_true", help="enable DistributedDataParallel when launched with torchrun")
    parser.add_argument("--log-every", type=int, default=50)
    parser.add_argument("--warmup-steps", type=int, default=50, help="steps ignored in timing (warmup)")
    args = parser.parse_args()

    rank, local_rank, world_size = ddp_setup()
    ddp = is_ddp_enabled(args)
    device = get_device(local_rank)

    # Some knobs that can matter on NVIDIA systems:
    torch.backends.cudnn.benchmark = True
    torch.set_float32_matmul_precision("high")  # helps on Ampere+ for fp32 matmul

    model = build_model(num_classes=10).to(device)

    if args.compile:
        try:
            model = torch.compile(model)  # PyTorch 2.x
        except Exception as e:
            if rank == 0:
                print(f"[WARN] torch.compile failed: {e}")

    if ddp:
        model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[local_rank], output_device=local_rank)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=0.9, weight_decay=5e-4)

    autocast_dtype = get_autocast_dtype(args.precision)
    use_amp = autocast_dtype is not None and device.type == "cuda"

    scaler = torch.cuda.amp.GradScaler(enabled=(use_amp and autocast_dtype == torch.float16))

    # Data
    loader = None
    sampler = None
    if args.mode == "cifar10":
        loader, sampler = make_cifar10_loader(args.batch_size, args.workers, ddp, rank, world_size)

    # NVML monitor (per local GPU)
    nvml = NvmlMonitor(local_rank=local_rank)

    # Timing
    total_steps = args.steps if args.mode == "synthetic" else (args.epochs * len(loader))
    warmup_steps = min(args.warmup_steps, max(0, total_steps // 5))

    if rank == 0:
        print("=== DGX / CUDA Training Benchmark ===")
        print(f"Mode: {args.mode}")
        print(f"World size: {world_size} (DDP: {ddp})")
        print(f"Device: {device}")
        print(f"Batch size (per process): {args.batch_size}")
        print(f"Precision: {args.precision} (AMP: {use_amp})")
        print(f"torch.compile: {args.compile}")
        print(f"Warmup steps: {warmup_steps}")
        print("=====================================")

    model.train()
    warmup_cuda()

    # Main loop
    step_times = []
    imgs_per_sec_samples = []
    nvml_samples = []

    step_idx = 0
    start_all = time.perf_counter()

    def run_step(x, y):
        optimizer.zero_grad(set_to_none=True)
        if use_amp:
            with torch.autocast(device_type="cuda", dtype=autocast_dtype):
                logits = model(x)
                loss = criterion(logits, y)
            if scaler.is_enabled():
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                loss.backward()
                optimizer.step()
        else:
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
        return float(loss.detach().item())

    if args.mode == "synthetic":
        # generate on GPU to avoid CPU bottlenecks
        for step_idx in range(total_steps):
            x, y = synthetic_batch(args.batch_size, device)

            t0 = time.perf_counter()
            _ = run_step(x, y)
            if device.type == "cuda":
                torch.cuda.synchronize()
            t1 = time.perf_counter()

            dt = t1 - t0

            if step_idx >= warmup_steps:
                step_times.append(dt)
                imgs_per_sec_samples.append(args.batch_size / dt)
                s = nvml.sample()
                if s is not None:
                    nvml_samples.append(s)

            if (step_idx + 1) % args.log_every == 0 and rank == 0:
                if step_idx >= warmup_steps and len(step_times) > 0:
                    avg_dt = sum(step_times[-args.log_every:]) / min(args.log_every, len(step_times))
                    ips = args.batch_size / avg_dt
                    print(f"[step {step_idx+1}/{total_steps}] avg_step={avg_dt*1000:.2f} ms  imgs/s={ips:.1f}")

    else:
        # CIFAR-10 mode
        for epoch in range(args.epochs):
            if ddp and sampler is not None:
                sampler.set_epoch(epoch)

            for batch in loader:
                step_idx += 1
                x, y = batch
                x = x.to(device, non_blocking=True)
                y = y.to(device, non_blocking=True)

                t0 = time.perf_counter()
                _ = run_step(x, y)
                if device.type == "cuda":
                    torch.cuda.synchronize()
                t1 = time.perf_counter()

                dt = t1 - t0

                if step_idx > warmup_steps:
                    step_times.append(dt)
                    imgs_per_sec_samples.append(args.batch_size / dt)
                    s = nvml.sample()
                    if s is not None:
                        nvml_samples.append(s)

                if (step_idx % args.log_every == 0) and rank == 0:
                    if len(step_times) > 0:
                        avg_dt = sum(step_times[-args.log_every:]) / min(args.log_every, len(step_times))
                        ips = args.batch_size / avg_dt
                        print(f"[epoch {epoch+1}/{args.epochs} step {step_idx}] avg_step={avg_dt*1000:.2f} ms  imgs/s={ips:.1f}")

        total_steps = step_idx

    end_all = time.perf_counter()
    elapsed_all = end_all - start_all

    # Aggregate per-rank stats (DDP: average across ranks)
    if len(step_times) == 0:
        avg_step = float("nan")
        avg_ips = float("nan")
    else:
        avg_step = sum(step_times) / len(step_times)
        avg_ips = sum(imgs_per_sec_samples) / len(imgs_per_sec_samples)

    avg_step = reduce_scalar_ddp(avg_step, device, world_size)
    avg_ips = reduce_scalar_ddp(avg_ips, device, world_size)

    # Effective global throughput
    global_ips = avg_ips * world_size

    if rank == 0:
        print("\n=== Results ===")
        print(f"Total wall time (including warmup/overhead): {elapsed_all:.2f} s")
        print(f"Avg step time (timed region): {avg_step*1000:.2f} ms")
        print(f"Avg throughput per process: {avg_ips:.1f} images/s")
        print(f"Avg throughput global: {global_ips:.1f} images/s (world_size={world_size})")

        if len(nvml_samples) > 0:
            # Report simple averages from local_rank=0 only (rank 0 corresponds to one process)
            # On multi-node runs you’d want a fancier gather; for single node this is usually enough.
            avg_gpu = sum(s.gpu_util for s in nvml_samples) / len(nvml_samples)
            avg_mem = sum(s.mem_util for s in nvml_samples) / len(nvml_samples)
            avg_pwr = sum(s.power_w for s in nvml_samples) / len(nvml_samples)
            avg_tmp = sum(s.temp_c for s in nvml_samples) / len(nvml_samples)
            print("\nNVML (local GPU) averages over timed region:")
            print(f"  GPU util: {avg_gpu:.1f}%")
            print(f"  MEM util: {avg_mem:.1f}%")
            print(f"  Power:    {avg_pwr:.1f} W")
            print(f"  Temp:     {avg_tmp:.1f} °C")
        else:
            print("\nNVML stats: not available (install pynvml or ensure NVML accessible).")

    nvml.shutdown()
    ddp_cleanup(world_size)


if __name__ == "__main__":
    main()
