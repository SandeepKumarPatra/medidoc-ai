FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PyTorch, OpenCV/RapidOCR, and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Optimize Python execution and configure Hugging Face model cache
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/root/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/root/.cache/huggingface

# Install Python dependencies first for optimal Docker layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend application, synthetic dataset, and operational scripts
COPY backend/ /app/backend/
COPY data/ /app/data/
COPY scripts/ /app/scripts/

EXPOSE 8000

# Start FastAPI application with Uvicorn
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
