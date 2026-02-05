FROM nvcr.io/nvidia/pytorch:25.12-py3

WORKDIR /app

# Install system dependencies if needed (e.g. for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
# Note: torch is already installed in this base image, but we can reinstall if specific version needed
# or let requirements.txt handle other deps. We remove torch from requirements install to avoid conflict/bloat if possible
COPY requirements.txt .
# Install requirements, but avoid reinstalling torch if it's already there and compatible
# Or just install everything. PIP is smart.
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
