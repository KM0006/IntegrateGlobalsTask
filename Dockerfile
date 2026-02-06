FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for CSV file
RUN mkdir -p /app/data

# Expose the application port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "main:App", "--host", "0.0.0.0", "--port", "8000"]
