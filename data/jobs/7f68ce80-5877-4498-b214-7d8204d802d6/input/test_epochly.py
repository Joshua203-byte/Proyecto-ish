"""
Simple test script for Epochly.
Prints system info and a simple calculation.
"""
import sys
import platform
import time
import os

print("=" * 50)
print("EPOCHLY TEST SCRIPT - SUCCESS!")
print("=" * 50)
print()

# System info
print("📊 System Information:")
print(f"  - Python version: {sys.version}")
print(f"  - Platform: {platform.platform()}")
print(f"  - Architecture: {platform.machine()}")
print()

# Check if GPU is available
try:
    import torch
    if torch.cuda.is_available():
        print("🚀 GPU Information:")
        print(f"  - GPU Count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  - GPU {i}: {torch.cuda.get_device_name(i)}")
            props = torch.cuda.get_device_properties(i)
            print(f"    Memory: {props.total_memory / 1024**3:.1f} GB")
    else:
        print("⚠️  CUDA not available")
except ImportError:
    print("⚠️  PyTorch not installed")

print()

# Simple calculation
print("🧮 Running simple test...")
result = sum(range(1000000))
print(f"  Sum of 0 to 999999 = {result}")

# Sleep to simulate work
print()
print("⏳ Simulating work (5 seconds)...")
for i in range(5):
    print(f"  Working... {i+1}/5")
    time.sleep(1)

print()
print("✅ TEST COMPLETED SUCCESSFULLY!")
print("=" * 50)

# ========================================
# GENERATE OUTPUT FILES FOR DOWNLOAD TEST
# ========================================
import json
import os

output_dir = "/workspace/output"
os.makedirs(output_dir, exist_ok=True)

# Create results JSON
results = {
    "status": "success",
    "python_version": sys.version,
    "platform": platform.platform(),
    "architecture": platform.machine(),
    "calculation_result": result,
    "message": "Job completed successfully on Epochly!"
}

results_file = os.path.join(output_dir, "results.json")
with open(results_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"📁 Results saved to: {results_file}")

