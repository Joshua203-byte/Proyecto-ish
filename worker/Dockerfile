FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI for DinD operations
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY . .

CMD ["celery", "-A", "worker.celery_app", "worker", "-l", "info", "-Q", "gpu_jobs", "-c", "1"]
