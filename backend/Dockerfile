# DateNight Show Matcher — backend (FastAPI + SSE, CLI, MCP server)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first (better layer caching). Editable install keeps non-python
# package data (catalog.json) resolvable via __file__ at runtime.
COPY pyproject.toml ./
COPY app ./app
RUN pip install -e .

EXPOSE 8090

# Default: serve the API. The CLI is also available, e.g.
#   docker compose run --rm backend get-show @art_girl
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8090"]
