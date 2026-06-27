# Backend container — runs the FastAPI app via uvicorn.

# Start from a minimal official Python 3.12 image (small footprint).
FROM python:3.12-slim

# All subsequent commands run inside this directory inside the container.
WORKDIR /app

# Install `uv` (our Python package/env manager) into the container.
RUN pip install --no-cache-dir uv

# Copy ONLY dependency manifests first.
# This is a Docker caching trick: as long as deps don't change, the slow
# install step below is reused from cache, even if app code changes.
COPY pyproject.toml uv.lock ./

# Materialize the locked dependency set into the container.
RUN uv sync --frozen --no-dev

# Now copy the actual application code.
COPY app ./app

# Document the port the app listens on (purely informational).
EXPOSE 8000

# Command Docker runs when the container starts.
# `--host 0.0.0.0` is required so the app is reachable from outside the container.
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
