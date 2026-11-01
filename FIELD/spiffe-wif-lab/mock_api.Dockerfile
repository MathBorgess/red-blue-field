FROM python:3.12-slim-bookworm

WORKDIR /lab
COPY requirements.lock /lab/requirements.lock
RUN pip install --no-cache-dir -r /lab/requirements.lock
COPY red_blue_field /lab/red_blue_field
COPY FIELD/spiffe-wif-lab/mock_api.py /lab/mock_api.py

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8080
CMD ["python", "/lab/mock_api.py"]
