FROM python:3.12-slim-bookworm
WORKDIR /app
COPY pyproject.toml README.md requirements.lock .env.example ./
COPY red_blue_field ./red_blue_field
COPY schemas ./schemas
COPY scenarios/catalog.json ./scenarios/catalog.json
RUN --mount=type=secret,id=system_ca,required=false \
    if [ -f /run/secrets/system_ca ]; then export PIP_CERT=/run/secrets/system_ca; fi; \
    pip install --no-cache-dir -r requirements.lock && pip install --no-cache-dir --no-deps . \
    && chmod -R a+rX /app /usr/local/lib/python3.12/site-packages/red_blue_field \
    && useradd --uid 10000 --create-home lab \
    && mkdir /data && chown lab:lab /data
USER 10000:10000
ENV RBF_DATA_DIR=/data PYTHONDONTWRITEBYTECODE=1
EXPOSE 8080
CMD ["rbf", "serve", "--host", "0.0.0.0", "--port", "8080"]
