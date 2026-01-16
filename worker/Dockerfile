# worker/Dockerfile
# Instructions for building the worker container.
# The worker polls Redis for batches and processes them.

FROM python:3.11-slim

WORKDIR /app

# Dependencies first (cached layer)
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Shared models module (single source of truth for both API and Worker)
COPY shared/ ./shared/

# Worker code
COPY worker/ .

# The worker runs as a long-running process (not a web server)
# It continuously polls Redis for work
CMD ["python", "main.py"]
