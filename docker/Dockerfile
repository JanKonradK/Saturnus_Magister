FROM python:3.14-slim

# Enable free-threading by using the 3.14t build
# For explicit free-threading, build from source with --disable-gil
# or use: python:3.14t when available on Docker Hub

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ src/
COPY credentials.json .

RUN python -c "import sys; print(f'Python {sys.version}')"

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.main"]
