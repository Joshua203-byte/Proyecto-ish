#!/usr/bin/env python3
"""
Simple GPU/CPU Test Script for Home-GPU-Cloud
No external model downloads required - perfect for testing the system.
"""
import subprocess
import sys

# Install only torch and numpy (fast, no HuggingFace)
subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "numpy", "-q"])

import torch
import time

print("=" * 50)
print("🚀 GPU Cloud Simple Test")
print("=" * 50)
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Matrix multiplication benchmark
print("\n📊 Running matrix multiplication benchmark...")
size = 2000
A = torch.randn(size, size, device=device)
B = torch.randn(size, size, device=device)

start = time.time()
iterations = 10
for i in range(iterations):
    C = torch.matmul(A, B)
if device == "cuda":
    torch.cuda.synchronize()
elapsed = time.time() - start

print(f"Matrix size: {size}x{size}")
print(f"{iterations} iterations in: {elapsed:.2f} seconds")
print(f"Average per iteration: {elapsed/iterations*1000:.1f} ms")

# Save results
with open("/workspace/output/result.txt", "w") as f:
    f.write("=" * 40 + "\n")
    f.write("GPU Cloud Test Results\n")
    f.write("=" * 40 + "\n")
    f.write(f"PyTorch: {torch.__version__}\n")
    f.write(f"Device: {device}\n")
    f.write(f"Matrix size: {size}x{size}\n")
    f.write(f"Iterations: {iterations}\n")
    f.write(f"Total time: {elapsed:.2f}s\n")
    f.write(f"Avg per iteration: {elapsed/iterations*1000:.1f}ms\n")
    f.write("Status: SUCCESS\n")

print("\n✅ TEST COMPLETED SUCCESSFULLY!")
print("📁 Results saved to /workspace/output/result.txt")
