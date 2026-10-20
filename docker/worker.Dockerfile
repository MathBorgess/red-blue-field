FROM python:3.12-slim-bookworm
RUN --mount=type=secret,id=system_ca,required=false \
    if [ -f /run/secrets/system_ca ]; then export SSL_CERT_FILE=/run/secrets/system_ca; fi; \
    apt-get update && apt-get install -y --no-install-recommends nmap sqlmap curl openssl iproute2 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home worker
COPY --chmod=0644 red_blue_field/worker.py /app/worker.py
RUN chmod 0755 /app
USER 10001:10001
ENV RBF_DISPOSABLE_CONTAINER=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
EXPOSE 8080
CMD ["python", "worker.py"]
