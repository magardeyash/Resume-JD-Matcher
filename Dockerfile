# ==========================================
# Stage 1: Build React Frontend
# ==========================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Production Python Backend
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Copy built React frontend distribution from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure backend imports work cleanly
ENV PYTHONPATH=/app/backend

WORKDIR /app/backend

EXPOSE 8000

# Run database migrations and launch Uvicorn on assigned port
CMD ["sh", "-c", "alembic -c /app/alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
