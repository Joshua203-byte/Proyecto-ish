#!/usr/bin/env python3
"""
Heavy GPU Matrix Multiplication Test
Tests GPU performance with large matrix operations
Expected runtime: 2-5 minutes depending on GPU
"""
import torch
import time
import json
from pathlib import Path

print("=" * 60)
print("🔥 HEAVY GPU MATRIX MULTIPLICATION TEST")
print("=" * 60)

# Check GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\nDevice: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# Test parameters - HEAVY workload
MATRIX_SIZE = 8192  # Large matrices
ITERATIONS = 50
WARMUP = 5

print(f"\nMatrix size: {MATRIX_SIZE}x{MATRIX_SIZE}")
print(f"Iterations: {ITERATIONS}")
print(f"Warmup: {WARMUP}")

# Allocate matrices
print("\n📊 Allocating matrices...")
A = torch.randn(MATRIX_SIZE, MATRIX_SIZE, device=device, dtype=torch.float32)
B = torch.randn(MATRIX_SIZE, MATRIX_SIZE, device=device, dtype=torch.float32)
memory_used = torch.cuda.memory_allocated() / 1024**3
print(f"GPU Memory used: {memory_used:.2f} GB")

# Warmup
print("\n🔄 Warming up GPU...")
for i in range(WARMUP):
    C = torch.matmul(A, B)
    torch.cuda.synchronize()
    print(f"  Warmup {i+1}/{WARMUP}")

# Benchmark
print("\n⚡ Running benchmark...")
times = []
for i in range(ITERATIONS):
    start = time.perf_counter()
    C = torch.matmul(A, B)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    times.append(elapsed)
    
    # Progress update every 10 iterations
    if (i + 1) % 10 == 0:
        avg_time = sum(times[-10:]) / 10
        tflops = (2 * MATRIX_SIZE**3) / avg_time / 1e12
        print(f"  Iteration {i+1}/{ITERATIONS} - Avg: {avg_time*1000:.1f}ms - {tflops:.2f} TFLOPS")

# Results
avg_time = sum(times) / len(times)
min_time = min(times)
max_time = max(times)
tflops = (2 * MATRIX_SIZE**3) / avg_time / 1e12

print("\n" + "=" * 60)
print("📈 RESULTS")
print("=" * 60)
print(f"Average time: {avg_time*1000:.2f} ms")
print(f"Min time: {min_time*1000:.2f} ms")
print(f"Max time: {max_time*1000:.2f} ms")
print(f"Performance: {tflops:.2f} TFLOPS")
print(f"GPU Memory Peak: {torch.cuda.max_memory_allocated() / 1024**3:.2f} GB")

# Save results
results = {
    "test": "matrix_multiplication",
    "matrix_size": MATRIX_SIZE,
    "iterations": ITERATIONS,
    "avg_time_ms": avg_time * 1000,
    "min_time_ms": min_time * 1000,
    "max_time_ms": max_time * 1000,
    "tflops": tflops,
    "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
    "memory_peak_gb": torch.cuda.max_memory_allocated() / 1024**3
}

output_path = Path("/tmp/gpu_test_results.json")
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\n💾 Results saved to: {output_path}")

print("\n✅ TEST COMPLETE!")
