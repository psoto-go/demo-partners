# Use an official, lightweight Python base image
FROM python:3.9-slim

# Set environment variables:
# - PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# - PYTHONUNBUFFERED: Ensures logs are flushed immediately to stdout/stderr for Cloud Logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first to leverage Docker layer caching
COPY requirements.txt /app/

# Install dependencies cleanly without caching to keep the image slim
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose the port (informative only; Cloud Run overrides and binds to $PORT dynamically)
EXPOSE 8080

# Execute Uvicorn, dynamically expanding the $PORT environment variable provided by Cloud Run
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
