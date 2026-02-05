# GPU Benchmark Script - Saves results to output folder
# Tests PyTorch GPU performance on DGX Spark (Blackwell)
import argparse
import time
import os
import json

print("=" * 50)
print("GPU BENCHMARK - DGX Spark Blackwell")
print("=" * 50)

# Parse arguments
parser = argparse.ArgumentParser(description='GPU Benchmark')
parser.add_argument('--steps', type=int, default=100, help='Number of steps')
parser.add_argument('--batch-size', type=int, default=64, help='Batch size')
parser.add_argument('--warmup', type=int, default=10, help='Warmup steps')
args = parser.parse_args()

print(f"\nConfiguration:")
print(f"  Steps: {args.steps}")
print(f"  Batch size: {args.batch_size}")
print(f"  Warmup: {args.warmup}")

# Import PyTorch
try:
    import torch
    print(f"\n✓ PyTorch version: {torch.__version__}")
    
    # Check CUDA availability
    if torch.cuda.is_available():
        device = torch.device("cuda")
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"✓ CUDA available: {gpu_name}")
        print(f"  GPU Memory: {gpu_memory:.1f} GB")
    else:
        device = torch.device("cpu")
        gpu_name = "CPU"
        gpu_memory = 0
        print("⚠ CUDA not available, using CPU")
except ImportError:
    print("❌ PyTorch not installed")
    exit(1)

# Create dummy model and data
print("\n[1/3] Creating model and data...")
model = torch.nn.Sequential(
    torch.nn.Linear(1024, 2048),
    torch.nn.ReLU(),
    torch.nn.Linear(2048, 2048),
    torch.nn.ReLU(),
    torch.nn.Linear(2048, 1024),
).to(device)

optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = torch.nn.MSELoss()

# Warmup
print(f"\n[2/3] Warmup ({args.warmup} steps)...")
for i in range(args.warmup):
    x = torch.randn(args.batch_size, 1024, device=device)
    y = torch.randn(args.batch_size, 1024, device=device)
    
    optimizer.zero_grad()
    output = model(x)
    loss = criterion(output, y)
    loss.backward()
    optimizer.step()

# Benchmark
print(f"\n[3/3] Running benchmark ({args.steps} steps)...")
if device.type == "cuda":
    torch.cuda.synchronize()

start_time = time.time()
step_times = []

for step in range(args.steps):
    step_start = time.time()
    
    x = torch.randn(args.batch_size, 1024, device=device)
    y = torch.randn(args.batch_size, 1024, device=device)
    
    optimizer.zero_grad()
    output = model(x)
    loss = criterion(output, y)
    loss.backward()
    optimizer.step()
    
    if device.type == "cuda":
        torch.cuda.synchronize()
    
    step_time = (time.time() - step_start) * 1000  # ms
    step_times.append(step_time)
    
    if (step + 1) % 20 == 0:
        avg_time = sum(step_times[-20:]) / min(20, len(step_times[-20:]))
        samples_per_sec = args.batch_size / (avg_time / 1000)
        print(f"  Step {step+1:3d}/{args.steps} | Loss: {loss.item():.4f} | {avg_time:.2f} ms/step | {samples_per_sec:.1f} samples/s")

total_time = time.time() - start_time
avg_step_time = sum(step_times) / len(step_times)
throughput = args.batch_size / (avg_step_time / 1000)

# Results
print("\n" + "=" * 50)
print("BENCHMARK RESULTS")
print("=" * 50)
print(f"Device: {gpu_name}")
print(f"Total time: {total_time:.2f} s")
print(f"Avg step time: {avg_step_time:.2f} ms")
print(f"Throughput: {throughput:.1f} samples/s")
print("=" * 50)

# Save results to output folder
output_dir = "/workspace/output"
os.makedirs(output_dir, exist_ok=True)

results = {
    "device": gpu_name,
    "gpu_memory_gb": gpu_memory,
    "pytorch_version": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "steps": args.steps,
    "batch_size": args.batch_size,
    "warmup": args.warmup,
    "total_time_seconds": round(total_time, 2),
    "avg_step_time_ms": round(avg_step_time, 2),
    "throughput_samples_per_second": round(throughput, 1),
    "step_times_ms": [round(t, 2) for t in step_times]
}

# Save JSON results
with open(f"{output_dir}/benchmark_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\n✓ Saved: benchmark_results.json")

# Save human-readable summary
with open(f"{output_dir}/summary.txt", "w") as f:
    f.write("=" * 50 + "\n")
    f.write("GPU BENCHMARK RESULTS\n")
    f.write("=" * 50 + "\n")
    f.write(f"Device: {gpu_name}\n")
    f.write(f"GPU Memory: {gpu_memory:.1f} GB\n")
    f.write(f"PyTorch: {torch.__version__}\n")
    f.write(f"CUDA: {'Yes' if torch.cuda.is_available() else 'No'}\n")
    f.write("\n")
    f.write(f"Steps: {args.steps}\n")
    f.write(f"Batch Size: {args.batch_size}\n")
    f.write(f"Total Time: {total_time:.2f} s\n")
    f.write(f"Avg Step Time: {avg_step_time:.2f} ms\n")
    f.write(f"Throughput: {throughput:.1f} samples/s\n")
    f.write("=" * 50 + "\n")
print(f"✓ Saved: summary.txt")

print("\n✓ Benchmark complete! Results saved to /workspace/output/")
