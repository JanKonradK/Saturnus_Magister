# `docker/` - Containerization

Configuration for running Saturnus_Magister in Docker.

## Files

- **`Dockerfile`**: Defines the application image.
  - Base: `python:3.14-slim` (or `3.14t` for free-threading).
  - Installs dependencies from `pyproject.toml`.
  - Copies source code and credentials.
  - Sets entry point to `src.main`.

- **`docker-compose.yml`**: Orchestrates the services.
  - **`saturnus`**: The main application container.
  - **`postgres`**: Database container (optional, if not using external DB).
  - **Networks**: Connects to `nyx_venatrix_network` to share the database with the Nyx_Venatrix project.

## Usage

### Prerequisites
- Docker and Docker Compose installed.
- `.env` file configured in project root.
- `credentials.json` and `token.pickle` present in project root (for Gmail auth).

### Running

**Option 1: Standalone (with its own DB)**
```bash
docker-compose -f docker/docker-compose.yml up -d
```

**Option 2: Integrated (Shared DB with Nyx_Venatrix)**
1. Ensure Nyx_Venatrix network exists:
   ```bash
   docker network create nyx_venatrix_network
   ```
2. Start the service:
   ```bash
   docker-compose -f docker/docker-compose.yml up saturnus -d
   ```

## Volumes

- `postgres_data`: Persists database data.
- Bind mounts for `token.pickle` and `credentials.json` ensure authentication persists across container restarts.
