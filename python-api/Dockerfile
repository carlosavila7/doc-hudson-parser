FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH=/app/.venv/bin:$PATH \
    HF_HOME=/app/.cache/huggingface

# Install system dependencies required by some Python packages and imaging libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libgl1 \
    libglib2.0-0 \
    libmagic1 \
    ffmpeg \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Create the Hugging Face cache directory
RUN mkdir -p ${HF_HOME}

# Create the virtual environment
RUN python3 -m venv ${VIRTUAL_ENV}

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt /app/

# Install Python deps into the venv
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ---
# CRITICAL FIX FOR RAPIDOCR MODELS
# This still might be needed if docling uses a separate mechanism for rapidocr
RUN chmod -R a+rw /usr/local/lib/python3.11/site-packages/rapidocr/models/ || true
# ---

# Copy application source
COPY . /app

# Ensure non-root user owns the app directory and all its contents (including venv and cache)
RUN chown -R app:app /app

# Switch to the non-root user
USER app

EXPOSE 8000

# Default command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]