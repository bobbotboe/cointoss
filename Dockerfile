# Stage 1: Build React frontend
FROM node:22-alpine AS frontend
WORKDIR /app/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

# Stage 2: Python API + serve static frontend
FROM python:3.13-slim
WORKDIR /app

# Install Python deps
COPY pyproject.toml ./
COPY cointoss/ cointoss/
COPY tests/ tests/
RUN pip install --no-cache-dir .

# Copy built frontend
COPY --from=frontend /app/ui/dist /app/static

# Copy entrypoint
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 3005

ENV COINTOSS_DATABASE_URL=sqlite:///data/cointoss.db

CMD ["./docker-entrypoint.sh"]
