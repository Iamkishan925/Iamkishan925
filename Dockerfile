FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY mk_pari ./mk_pari
RUN pip install --no-cache-dir . && useradd -m pari
USER pari

EXPOSE 8000
CMD ["uvicorn", "mk_pari.app:app", "--host", "0.0.0.0", "--port", "8000"]
