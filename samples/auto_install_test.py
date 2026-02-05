# Test script with external dependencies
# This script imports numpy and requests to verify auto-install works
import argparse
import time
import os

# External dependencies that need to be installed
import numpy as np
import requests

print("=" * 50)
print("AUTO-INSTALL TEST SCRIPT")
print("=" * 50)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Test script for auto-install')
parser.add_argument('--epochs', type=int, default=5, help='Number of epochs')
parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
parser.add_argument('--mode', type=str, default='default', help='Training mode')
args = parser.parse_args()

print(f"\nArguments received:")
print(f"  --epochs: {args.epochs}")
print(f"  --batch-size: {args.batch_size}")
print(f"  --mode: {args.mode}")

# Test numpy
print(f"\n✓ NumPy version: {np.__version__}")
arr = np.random.rand(args.batch_size, 10)
print(f"  Generated random array: {arr.shape}")

# Test requests (verify network access)
print(f"\n✓ Requests version: {requests.__version__}")

# Simulate training loop
print(f"\n[Training] Running {args.epochs} epochs...")
for epoch in range(args.epochs):
    print(f"  Epoch {epoch + 1}/{args.epochs} - loss: {2.0 - epoch * 0.3:.4f}")
    time.sleep(1)

# Save results
output_dir = "/workspace/output"
os.makedirs(output_dir, exist_ok=True)

with open(f"{output_dir}/results.txt", "w") as f:
    f.write("Test completed successfully!\n")
    f.write(f"Epochs: {args.epochs}\n")
    f.write(f"Batch size: {args.batch_size}\n")
    f.write(f"Mode: {args.mode}\n")
    f.write(f"NumPy array shape: {arr.shape}\n")

print("\n✓ Results saved to /workspace/output/results.txt")
print("=" * 50)
print("TEST COMPLETE!")
print("=" * 50)
