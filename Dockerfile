FROM node:22-bookworm-slim AS frontend-build

WORKDIR /workspace/frontend
COPY frontend/package.json ./
RUN npm install --ignore-scripts
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

WORKDIR /app/backend

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /workspace/frontend/dist /app/frontend/dist
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN mkdir -p /app/backend/artifacts /app/models_saved \
    && chown -R app:app /app

USER app
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]