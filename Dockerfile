FROM python:3.14-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev
COPY src config scripts ./
RUN chmod +x scripts/entrypoint.sh
ENV PYTHONPATH=/app
EXPOSE 8000
ENTRYPOINT ["scripts/entrypoint.sh"]
