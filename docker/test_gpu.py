#!/usr/bin/env python3
"""
Quick GPU test script for Home-GPU-Cloud.
This verifies that PyTorch can access CUDA.
"""

import torch
import sys
from pathlib import Path

print("=" * 60)
print("HOME-GPU-CLOUD GPU VERIFICATION")
print("=" * 60)

# Check PyTorch and CUDA
print(f"\nPyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU count: {torch.cuda.device_count()}")
    
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"\nGPU {i}: {props.name}")
        print(f"  Total Memory: {props.total_memory / 1024**3:.1f} GB")
        print(f"  Compute Capability: {props.major}.{props.minor}")
    
    # Run a simple GPU operation
    print("\n" + "-" * 60)
    print("Running matrix multiplication test...")
    
    x = torch.randn(2048, 2048, device='cuda')
    y = torch.randn(2048, 2048, device='cuda')
    
    # Warm up
    _ = torch.matmul(x, y)
    torch.cuda.synchronize()
    
    # Timed run
    import time
    start = time.perf_counter()
    for _ in range(10):
        z = torch.matmul(x, y)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    
    gflops = (2 * 2048**3 * 10) / elapsed / 1e9
    print(f"Matrix: 2048x2048, 10 iterations")
    print(f"Time: {elapsed*1000:.1f} ms")
    print(f"Performance: {gflops:.1f} GFLOPS")
    
    # Save result
    output_dir = Path("/workspace/output")
    if output_dir.exists():
        result = {
            "pytorch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "gpu_name": torch.cuda.get_device_name(0),
            "gflops": gflops,
            "status": "success"
        }
        import json
        with open(output_dir / "gpu_test_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to {output_dir / 'gpu_test_result.json'}")
    
    print("\n" + "=" * 60)
    print("✓ GPU TEST PASSED!")
    print("=" * 60)
    sys.exit(0)

else:
    print("\n" + "=" * 60)
    print("✗ GPU TEST FAILED - CUDA NOT AVAILABLE")
    print("Check: nvidia-smi, NVIDIA Container Toolkit")
    print("=" * 60)
    sys.exit(1)
