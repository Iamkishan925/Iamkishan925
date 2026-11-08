FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY pari ./pari
RUN pip install --no-cache-dir . && useradd --create-home pari
USER pari
EXPOSE 8000
# Only reachable on the internal Docker network; Caddy is the single public entry point.
CMD ["uvicorn", "pari.main:app", "--host", "0.0.0.0", "--port", "8000"]
