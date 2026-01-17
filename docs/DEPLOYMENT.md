# Deployment Guide

## Prerequisites

### All Nodes
- Ubuntu 22.04 LTS (recommended)
- Docker 24.0+
- Python 3.11+

### Nodo C (GPU Worker)
- NVIDIA GPU with CUDA support
- NVIDIA Driver 525+
- NVIDIA Container Toolkit

---

## Step 1: NFS Setup

### Nodo B (NAS)

```bash
# SSH into NAS machine
sudo ./scripts/setup_nfs_server.sh

# Verify
sudo exportfs -v
```

### Nodo C (Worker)

```bash
# Set NAS IP
export NFS_SERVER_IP=192.168.1.100

# Run setup
sudo ./scripts/setup_nfs_client.sh

# Verify mount
ls -la /mnt/home-gpu-cloud
```

---

## Step 2: Controller (Nodo A)

```bash
cd home-gpu-cloud

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Start services
docker-compose up -d

# Initialize database
python scripts/init_db.py

# Check API
curl http://localhost:8000/health
```

---

## Step 3: Worker (Nodo C)

```bash
cd home-gpu-cloud/worker

# Copy environment file
cp ../.env.example .env

# Edit with controller IP
nano .env
# Set: REDIS_URL=redis://192.168.1.50:6379/0
# Set: BACKEND_URL=http://192.168.1.50:8000

# Test GPU
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.1-base nvidia-smi

# Start worker
docker-compose -f ../docker-compose.worker.yml up -d

# Check logs
docker logs -f homegpu-worker
```

---

## Verification

1. **Create user**: `POST /api/v1/auth/register`
2. **Add credits**: `POST /api/v1/wallet/topup`
3. **Submit job**: `POST /api/v1/jobs/`
4. **Monitor**: Check worker logs
5. **Get results**: `GET /api/v1/jobs/{id}/outputs`
