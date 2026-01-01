FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps
RUN pip install --no-cache-dir fastapi uvicorn[standard] tensorflow cryptography

# Copy app
COPY server/ ./server/
COPY model/medical_model.enc /opt/model/medical_model.enc

ENV PYTHONPATH=/app

EXPOSE 8443

ENTRYPOINT ["./server/entrypoint.sh"]
