# Orion GPU Cloud 🌌
**Your Personal AI Research Supercomputer**

Orion Cloud is a **Compute-as-a-Service (CaaS)** platform designed to turn your local GPU workstation into a cloud-like experience. It allows you to submit Python training jobs, manage datasets, and monitor resources via a beautiful, modern web interface.

---

## 🏗️ Architecture

Orion runs as a set of microservices orchestrated by Docker.

```mermaid
graph LR
    User[User / Web Browser] --> Frontend[Frontend (React + Vite)]
    Frontend --> API[Backend API (FastAPI)]
    
    subgraph "Orion Core"
        API --> DB[(PostgreSQL)]
        API --> Cache[(Redis)]
        API --> Storage[Shared Storage (NFS/Volume)]
    end
    
    subgraph "Compute Node (The Worker)"
        Worker[Celery Worker] --> |Listens to| Cache
        Worker --> |Launches| JobContainer[Job Container (Docker)]
        JobContainer --> |Uses| GPU[Physical GPU (NVIDIA)]
        JobContainer --> |Reads/Writes| Storage
    end
```

### The Stack
- **Frontend**: React, TailwindCSS, Glassmorphism UI (Port 3000).
- **Backend**: FastAPI (Python 3.10+), SQLAlchemy, Stripe Integration (Port 8000).
- **Worker**: Celery-based task runner handling Docker orchestration.
- **Database**: PostgreSQL for persistent data (Users, Jobs, Wallet).
- **Infrastructure**: Docker Compose + NVIDIA Container Toolkit.

---

## 🧠 How the Machine Learning Works

This is the core magic of Orion. When you click "Launch Job", here is exactly what happens:

1.  **Upload**: Your Python script (`train.py`) and Dataset are uploaded to the API.
2.  **Storage**: The API saves these files to a strictly isolated directory: `data/jobs/{job_id}/input`.
3.  **Queueing**: The job is added to a Redis queue. The Worker picks it up instantly.
4.  **Isolation (The "Sandboxing")**: 
    - The Worker commands Docker to spin up a **new, temporary container** just for your job.
    - This container is based on deep learning images (e.g., `pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime`).
5.  **GPU Passthrough**: 
    - The specific Docker container is launched with the `--gpus all` flag (via the NVIDIA Runtime).
    - This allows the code inside the container to talk directly to your physical GPU hardware via CUDA drivers, with **zero virtualization overhead**.
6.  **Execution**: 
    - Your script runs: `python /workspace/input/script.py`.
    - Any model checkpoints (`.pt`, `.h5`) you save to `/workspace/output` are preserved.
7.  **Teardown**: Once the script finishes (or errors), the container is destroyed, freeing up the GPU for the next job.

**Why this is cool:** You never have to worry about messing up your host CUDA drivers or Python environments. Every job runs in a pristine "factory-fresh" environment.

---

## ✨ Key Features

### 🖥️ Modern Dashboard
- **New Job**: Drag-and-drop interface for `.py` scripts and datasets.
- **Wallet & Pricing**: Simulates a cloud billing system (e.g., $10 credits).
- **Jobs Overview**: Track status (Queued, Running, Completed, Failed).

### 🛡️ System Tools (Terminal)
Orion includes powerful scripts to manage the host:

- **`./monitor.sh`**: 
    - Displays real-time GPU stats (`nvidia-smi`).
    - Shows System CPU/RAM usage.
    - Useful to check if the GPU is actually crunching numbers.
    
- **`./cleanup.sh`**: 
    - Removes old Docker containers (garbage collection).
    - Prunes dangling images to save disk space.
    - Cleans Python cache files.

---

## 🚀 Getting Started

### Prerequisites
1.  **Linux** (Ubuntu 20.04/22.04 recommended).
2.  **NVIDIA Drivers** installed (`nvidia-smi` works).
3.  **Docker** & **Docker Compose**.
4.  **NVIDIA Container Toolkit** (Vital for GPU access in Docker).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/orion-cloud.git
    cd orion-cloud
    ```

2.  **Start the System:**
    ```bash
    docker compose up -d --build
    ```
    *This will compile the Frontend, build the API, and start the Database/Redis.*

3.  **Access:**
    - **Open your Ngrok URL** (e.g., `https://your-domain.ngrok-free.app`) in your browser.
    - API Documentation: `https://your-domain.ngrok-free.app/docs`.

### Usage

1.  **Top up Wallet**: Go to "Wallet" and buy a pack (Test Mode).
2.  **Submit a Job**:
    - Go to "New Job".
    - Upload a sample script (e.g., `samples/extreme_train.py`).
    - Select GPU Memory and Timeout.
    - Click "Launch".
3.  **Monitor**:
    - Run `./monitor.sh` in your terminal to see the GPU ignite! 🔥

---

## 📁 Project Structure

```
/
├── backend/            # FastAPI Application (User Auth, Job Logic)
├── frontend-react/     # React Application (The UI)
├── worker/             # The "Brain" (Celery Task Executor)
├── data/               # Persistent storage for Database & Job Files
├── samples/            # Example ML scripts for testing
├── restart_services.sh # Quick restart script
├── monitor.sh          # System Status script
└── cleanup.sh          # System Maintenance script
```

---

## 🛠 Troubleshooting

- **"API Connection Failed"**: Ensure backend is running (`docker compose logs -f api`).
- **"GPU Not Found"**: Make sure `nvidia-container-toolkit` is installed on your host system.
- **Frontend changes not showing?**: The frontend is built into a container. If you edit code, run:
  `docker compose up -d --build --no-deps frontend`

---

*Powered by Orion Cloud Engineering*
