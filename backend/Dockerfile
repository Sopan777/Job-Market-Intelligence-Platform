FROM python:3.11-slim

WORKDIR /app

# System deps for easyocr / pymupdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# craft-text-detector must be installed --no-deps to avoid its numpy==1.21.2 pin
# which is incompatible with Python 3.10+
RUN pip install --no-cache-dir --no-deps craft-text-detector

# Download spaCy model at build time
RUN python -m spacy download en_core_web_sm

COPY . .

# Point DATA_DIR at the bundled parquet files inside the image
ENV DATA_DIR=/app/data/processed

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
