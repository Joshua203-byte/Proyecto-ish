#!/usr/bin/env python3
"""
ml_stress_cifar10.py

A practical ML stress test using CIFAR-10:
- Downloads CIFAR-10 via torchvision (source: https://www.cs.toronto.edu/~kriz/cifar.html)
- Exercises: DataLoader, augmentations, GPU/CPU training, mixed precision (optional), logging.
- Reports:
    * data loading time vs compute time
    * images/sec
    * loss trend
    * GPU memory (if CUDA)

Requirements:
  pip install torch torchvision

Typical runs:
  python ml_stress_cifar10.py --device auto --steps 500 --batch-size 256 --workers 8 --amp
  python ml_stress_cifar10.py --device cuda --steps 1000 --batch-size 512 --workers 12 --prefetch 4 --amp

Notes:
- This is not for accuracy; it's for load testing.
- Increase --steps, --batch-size, --workers, and enable --amp to stress GPU.
"""

from __future__ import annotations

import argparse
import os
import random
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader

import torchvision
import torchvision.transforms as T


# -------------------------
# Model (small CNN)
# -------------------------
class SmallCNN(nn.Module):
    def __init__(self, num_classes: int = 10) -> None:
        super().__init__()
        # 32x32 input
        self.conv1 = nn.Conv2d(3, 64, 3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, 3, padding=1)
        self.conv3 = nn.Conv2d(128, 256, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(64)
        self.bn2 = nn.BatchNorm2d(128)
        self.bn3 = nn.BatchNorm2d(256)
        self.pool = nn.MaxPool2d(2, 2)  # 32->16->8->4

        self.fc1 = nn.Linear(256 * 4 * 4, 1024)
        self.fc2 = nn.Linear(1024, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = x.flatten(1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x


# -------------------------
# Timing helpers
# -------------------------
@dataclass
class Meter:
    n: int = 0
    total: float = 0.0

    def add(self, x: float) -> None:
        self.n += 1
        self.total += x

    @property
    def avg(self) -> float:
        return self.total / self.n if self.n else 0.0


def now() -> float:
    return time.perf_counter()


def sync_if_cuda(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize()


def set_seeds(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def pick_device(s: str) -> torch.device:
    s = s.lower()
    if s == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(s)


# -------------------------
# Main stress loop
# -------------------------
def main() -> int:
    p = argparse.ArgumentParser(description="ML stress test using CIFAR-10 + training loop.")
    p.add_argument("--data-dir", default="./data", help="Dataset cache directory")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="Device to use")
    p.add_argument("--steps", type=int, default=500, help="Number of training steps (batches)")
    p.add_argument("--batch-size", type=int, default=256, help="Batch size")
    p.add_argument("--workers", type=int, default=8, help="DataLoader workers")
    p.add_argument("--prefetch", type=int, default=2, help="DataLoader prefetch_factor (per worker)")
    p.add_argument("--pin-memory", action="store_true", help="Pin memory for faster H2D copies")
    p.add_argument("--persistent-workers", action="store_true", help="Keep workers alive across epochs")
    p.add_argument("--amp", action="store_true", help="Use mixed precision (CUDA only)")
    p.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    p.add_argument("--seed", type=int, default=1337, help="Random seed")
    p.add_argument("--print-every", type=int, default=50, help="Print every N steps")
    p.add_argument("--compile", action="store_true", help="torch.compile model (PyTorch 2.x), if supported")
    args = p.parse_args()

    os.makedirs(args.data_dir, exist_ok=True)
    set_seeds(args.seed)

    device = pick_device(args.device)
    use_amp = bool(args.amp and device.type == "cuda")

    print("========================================")
    print("Dataset: CIFAR-10")
    print("Source (official): https://www.cs.toronto.edu/~kriz/cifar.html")
    print(f"Local cache dir: {os.path.abspath(args.data_dir)}")
    print("========================================")
    print(f"Device: {device} | AMP: {use_amp} | torch: {torch.__version__}")
    if device.type == "cuda":
        print(f"CUDA: {torch.version.cuda} | GPU: {torch.cuda.get_device_name(0)}")

    # Augmentations to stress CPU pipeline a bit
    transform = T.Compose(
        [
            T.RandomCrop(32, padding=4),
            T.RandomHorizontalFlip(),
            T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            T.ToTensor(),
            T.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ]
    )

    # Download dataset (automatic)
    train_set = torchvision.datasets.CIFAR10(
        root=args.data_dir, train=True, download=True, transform=transform
    )

    loader = DataLoader(
        train_set,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.workers,
        pin_memory=args.pin_memory,
        persistent_workers=args.persistent_workers if args.workers > 0 else False,
        prefetch_factor=args.prefetch if args.workers > 0 else None,
        drop_last=True,
    )

    model = SmallCNN(num_classes=10).to(device)
    if args.compile:
        # Only do this if torch.compile exists and your build supports it.
        if hasattr(torch, "compile"):
            model = torch.compile(model)  # type: ignore[attr-defined]
            print("torch.compile enabled")
        else:
            print("torch.compile not available in this build; continuing without it")

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    # Meters
    data_time = Meter()
    h2d_time = Meter()
    fwd_bwd_time = Meter()
    step_time = Meter()
    loss_meter = Meter()

    # Warmup: a few steps (stabilize kernels/caching)
    warmup = min(20, args.steps)
    print(f"\nWarmup steps: {warmup}")

    model.train()

    t_start_all = now()
    last_iter_end = now()

    it = iter(loader)

    for step in range(1, args.steps + 1):
        # Measure time waiting for next batch (DataLoader + transforms)
        t0 = now()
        try:
            x_cpu, y_cpu = next(it)
        except StopIteration:
            it = iter(loader)
            x_cpu, y_cpu = next(it)
        t1 = now()
        data_time.add(t1 - t0)

        # H2D transfer time
        t2 = now()
        if device.type == "cuda":
            # non_blocking only helps if pin_memory=True
            x = x_cpu.to(device, non_blocking=args.pin_memory)
            y = y_cpu.to(device, non_blocking=args.pin_memory)
        else:
            x = x_cpu
            y = y_cpu
        sync_if_cuda(device)
        t3 = now()
        h2d_time.add(t3 - t2)

        # Forward/backward/step
        t4 = now()
        opt.zero_grad(set_to_none=True)

        if use_amp:
            with torch.cuda.amp.autocast():
                logits = model(x)
                loss = F.cross_entropy(logits, y)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        else:
            logits = model(x)
            loss = F.cross_entropy(logits, y)
            loss.backward()
            opt.step()

        sync_if_cuda(device)
        t5 = now()
        fwd_bwd_time.add(t5 - t4)

        # Total step time includes data wait + H2D + compute
        t6 = now()
        step_time.add(t6 - last_iter_end)
        last_iter_end = t6

        loss_meter.add(float(loss.item()))

        # Print
        if step % args.print_every == 0 or step in (1, warmup, args.steps):
            img_per_s = (args.batch_size / step_time.avg) if step_time.avg > 0 else 0.0
            print(
                f"step {step:5d}/{args.steps} | "
                f"loss(avg) {loss_meter.avg:.4f} | "
                f"img/s {img_per_s:,.1f} | "
                f"data {data_time.avg*1000:.2f}ms | "
                f"h2d {h2d_time.avg*1000:.2f}ms | "
                f"compute {fwd_bwd_time.avg*1000:.2f}ms | "
                f"step {step_time.avg*1000:.2f}ms"
            )
            if device.type == "cuda":
                mem = torch.cuda.max_memory_allocated() / (1024**2)
                print(f"  GPU max allocated: {mem:.1f} MiB")

        # Optional: drop warmup from averages by resetting meters after warmup
        if step == warmup:
            data_time = Meter()
            h2d_time = Meter()
            fwd_bwd_time = Meter()
            step_time = Meter()
            loss_meter = Meter()
            if device.type == "cuda":
                torch.cuda.reset_peak_memory_stats()
            print("\nWarmup complete. Resetting meters for main measurement...\n")

    t_end_all = now()
    total_s = t_end_all - t_start_all
    # Effective throughput after warmup
    avg_step = step_time.avg
    img_s = (args.batch_size / avg_step) if avg_step > 0 else 0.0

    print("\n=== Final Report (post-warmup averages) ===")
    print(f"Steps measured:       {step_time.n}")
    print(f"Batch size:           {args.batch_size}")
    print(f"Avg step time:        {avg_step*1000:.2f} ms")
    print(f"Throughput:           {img_s:,.1f} images/sec")
    print(f"Avg data wait:        {data_time.avg*1000:.2f} ms")
    print(f"Avg H2D transfer:     {h2d_time.avg*1000:.2f} ms")
    print(f"Avg compute:          {fwd_bwd_time.avg*1000:.2f} ms")
    print(f"Wall time (overall):  {total_s:.2f} s")

    if device.type == "cuda":
        mem = torch.cuda.max_memory_allocated() / (1024**2)
        print(f"GPU max allocated:    {mem:.1f} MiB")

    # Quick diagnosis hints (printed, not interactive)
    print("\nHints:")
    print("- If data wait is large: increase --workers, enable --persistent-workers, maybe reduce heavy augmentations.")
    print("- If H2D is large: use --pin-memory and larger batch sizes, ensure PCIe is healthy.")
    print("- If compute dominates: increase batch size, enable --amp, and/or try --compile.")
    print("- For a harder test: raise --steps and --batch-size until you hit VRAM/throughput limits.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())