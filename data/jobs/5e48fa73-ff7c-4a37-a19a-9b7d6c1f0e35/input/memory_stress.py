# Memory Stress Test - Large Data Processing
# This script uses significant memory and CPU
import time
import random
import os

print("=" * 60)
print("MEMORY STRESS TEST - LARGE DATA PROCESSING")
print("=" * 60)

# Allocate large arrays
print("\n[1/4] Allocating memory...")
large_data = []
for i in range(5):
    chunk = [random.random() for _ in range(2_000_000)]
    large_data.append(chunk)
    print(f"  Allocated chunk {i+1}/5 (~16MB)")
    time.sleep(1)

print(f"  ✓ Total data: {len(large_data) * 2_000_000:,} elements (~80MB)")

# Process data in batches
print("\n[2/4] Processing data batches...")
for batch_idx, batch in enumerate(large_data):
    start = time.time()
    
    # Simulate processing
    processed = [x ** 2 + x for x in batch[:500_000]]
    mean_val = sum(processed) / len(processed)
    
    elapsed = time.time() - start
    print(f"  Batch {batch_idx+1}/5 | Mean: {mean_val:.6f} | Time: {elapsed:.2f}s")
    time.sleep(3)

# Aggregation
print("\n[3/4] Aggregating results...")
for i in range(10):
    print(f"  Aggregation step {i+1}/10...")
    time.sleep(2)

# Save output
print("\n[4/4] Saving results...")
output_dir = "/workspace/output"
os.makedirs(output_dir, exist_ok=True)

with open(f"{output_dir}/stress_test_results.txt", "w") as f:
    f.write("Memory Stress Test Complete\n")
    f.write(f"Total data processed: {len(large_data) * 2_000_000:,} elements\n")
    f.write(f"Peak memory usage: ~80MB\n")
    f.write("Status: SUCCESS\n")

print("\n" + "=" * 60)
print("STRESS TEST COMPLETE!")
print("=" * 60)
