FROM python:3.12-slim

LABEL maintainer="paulomenon"
LABEL description="Bootable Container AI Demo — Insurance Emergency System"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        supervisor \
        curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY shared/ /app/shared/
COPY services/ /app/services/

RUN pip install --no-cache-dir \
    flask \
    gunicorn \
    requests

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8001 8002 8003 8004

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health && \
        curl -f http://localhost:8002/health && \
        curl -f http://localhost:8003/health && \
        curl -f http://localhost:8004/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
