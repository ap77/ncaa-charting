FROM python:3.11-slim

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything
COPY backend/app ./app
COPY data ./data
COPY models ./models
COPY frontend/dist ./frontend/dist

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
