FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ src/
COPY credentials.json .

RUN python -c "import sys; print(f'Python {sys.version}')"

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.main"]
