FROM python:3.11-slim

RUN pip install --no-cache-dir \
    --extra-index-url https://test.pypi.org/simple/ \
    vrptw==0.1.6

COPY scripts/docker_entrypoint.py /usr/local/bin/docker_entrypoint.py

ENTRYPOINT ["python", "/usr/local/bin/docker_entrypoint.py"]
