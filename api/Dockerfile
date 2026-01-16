# api/Dockerfile
# Instructions for building the API container.
# Docker reads this file top-to-bottom and caches each step.
# Put things that change rarely (dependencies) before things that change often (code).

# ============================================================
# BASE IMAGE
# ============================================================
# Start from official Python image. "slim" = smaller size, has what we need.
# Always pin a specific version for reproducibility.
FROM python:3.11-slim

# ============================================================
# WORKING DIRECTORY
# ============================================================
# All subsequent commands run from this directory.
# Creates the directory if it doesn't exist.
WORKDIR /app

# ============================================================
# DEPENDENCIES (cached layer)
# ============================================================
# Copy requirements first, install dependencies.
# This layer is cached - only rebuilds if requirements.txt changes.
# This is a common pattern to speed up builds.
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# SHARED CODE
# ============================================================
# Copy shared models module (used by both API and Worker)
# This ensures API and Worker use identical model definitions.
COPY shared/ ./shared/

# ============================================================
# APPLICATION CODE
# ============================================================
# Copy the rest of the API code.
# This layer rebuilds every time code changes, but dependencies are cached.
COPY api/ .

# ============================================================
# PORT
# ============================================================
# Document which port the app listens on.
# This is informational - you still need to map it in docker-compose.
EXPOSE 8000

# ============================================================
# STARTUP COMMAND
# ============================================================
# Run uvicorn (ASGI server) with our FastAPI app.
# --host 0.0.0.0 = accept connections from outside the container
# --port 8000 = listen on port 8000
# --reload = auto-restart when code changes (dev only, remove in production)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
