FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

COPY . .

# Install with uv to respect lock file
RUN uv sync --frozen --no-dev

ENTRYPOINT ["python", "scripts/docker_entrypoint.py"]
