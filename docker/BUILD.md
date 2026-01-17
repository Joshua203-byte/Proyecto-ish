# Building and Testing the Standard ML Image

## Prerequisites

- Docker 24.0+
- NVIDIA Driver 525+
- NVIDIA Container Toolkit installed

### Install NVIDIA Container Toolkit (if not already)

```bash
# Add NVIDIA repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker
```

---

## Build the Image

```bash
cd home-gpu-cloud/docker

# Build the standard image (~5-10 minutes, ~8GB)
docker build \
    -t home-gpu-cloud:standard-v1 \
    -f Dockerfile.standard \
    .

# Verify
docker images | grep home-gpu-cloud
```

### Expected Output

```
home-gpu-cloud    standard-v1    abc123def456    5 minutes ago    8.2GB
```

---

## Test GPU Access

### Quick Test

```bash
docker run --rm --gpus all home-gpu-cloud:standard-v1 --help
```

### Full GPU Verification

Create a test script:

```bash
mkdir -p /tmp/test-job/input /tmp/test-job/output

cat > /tmp/test-job/input/test_gpu.py << 'EOF'
#!/usr/bin/env python3
"""GPU Test Script for Home-GPU-Cloud"""

import torch
import sys

print("=" * 60)
print("HOME-GPU-CLOUD GPU TEST")
print("=" * 60)

# Check CUDA
print(f"\nPyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"cuDNN version: {torch.backends.cudnn.version()}")
    print(f"GPU count: {torch.cuda.device_count()}")
    
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"\nGPU {i}: {props.name}")
        print(f"  Memory: {props.total_memory / 1024**3:.1f} GB")
        print(f"  Compute: {props.major}.{props.minor}")
    
    # Simple tensor operation on GPU
    print("\nRunning tensor test...")
    x = torch.randn(1000, 1000, device='cuda')
    y = torch.randn(1000, 1000, device='cuda')
    z = torch.matmul(x, y)
    
    print(f"Matrix multiplication: {x.shape} x {y.shape} = {z.shape}")
    print(f"Result sum: {z.sum().item():.4f}")
    
    # Save result to output
    torch.save(z, '/workspace/output/test_tensor.pt')
    print("\nSaved test tensor to /workspace/output/test_tensor.pt")
    
    print("\n" + "=" * 60)
    print("GPU TEST PASSED!")
    print("=" * 60)
    sys.exit(0)
else:
    print("\n" + "=" * 60)
    print("GPU TEST FAILED - CUDA NOT AVAILABLE")
    print("=" * 60)
    sys.exit(1)
EOF
```

### Run the Test

```bash
docker run --rm --gpus all \
    -v /tmp/test-job/input:/workspace/input:ro \
    -v /tmp/test-job/output:/workspace/output \
    home-gpu-cloud:standard-v1 \
    test_gpu.py
```

### Expected Output

```
[2026-01-17 12:00:00] [INFO] ============================================================
[2026-01-17 12:00:00] [INFO] HOME-GPU-CLOUD JOB WRAPPER
[2026-01-17 12:00:00] [INFO] ============================================================
[2026-01-17 12:00:00] [INFO] Python: 3.10.12 (...)
[2026-01-17 12:00:00] [INFO] Input dir: /workspace/input
[2026-01-17 12:00:00] [INFO] Output dir: /workspace/output
[2026-01-17 12:00:00] [INFO] CUDA available: 1 GPU(s) detected
[2026-01-17 12:00:00] [INFO]   GPU 0: NVIDIA GeForce RTX 3060 (12.0 GB)
...
============================================================
GPU TEST PASSED!
============================================================
[2026-01-17 12:00:01] [INFO] JOB COMPLETED SUCCESSFULLY
```

### Verify Output

```bash
ls -la /tmp/test-job/output/
# Should show: test_tensor.pt and .job_status.json

cat /tmp/test-job/output/.job_status.json
# Should show: {"status": "completed", "exit_code": 0, ...}
```

---

## Test Signal Handling (Kill Switch)

```bash
# Start a long-running job
docker run --rm --gpus all \
    --name test-kill \
    -v /tmp/test-job/input:/workspace/input:ro \
    -v /tmp/test-job/output:/workspace/output \
    home-gpu-cloud:standard-v1 \
    test_gpu.py &

sleep 2

# Send SIGTERM (simulates credit exhaustion)
docker stop test-kill

# Check status
cat /tmp/test-job/output/.job_status.json
# Should show: {"status": "terminated", ...}
```

---

## Push to Registry (Optional)

```bash
# Tag for your registry
docker tag home-gpu-cloud:standard-v1 your-registry.io/home-gpu-cloud:standard-v1

# Push
docker push your-registry.io/home-gpu-cloud:standard-v1
```

---

## Troubleshooting

### "CUDA not available"

```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker runtime
docker info | grep -i runtime

# Test NVIDIA container toolkit
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Image build fails

```bash
# Check disk space (need ~15GB free)
df -h

# Build with verbose output
docker build --progress=plain -t home-gpu-cloud:standard-v1 -f Dockerfile.standard .
```
