# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all project files
COPY . /app

# Install system dependencies for PyMuPDF
RUN apt-get update && \
    apt-get install -y libglib2.0-0 libsm6 libxrender1 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir pymupdf numpy tqdm sentence-transformers

# Default command to run the processing script
CMD ["python", "process_collections.py"] 