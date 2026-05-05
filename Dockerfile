# Use an official Python 3.11 lightweight image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for SQLite and ChromaDB
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project directory into the container
COPY mcp_project /app/mcp_project

# Set the PYTHONPATH so Python knows where the mcp_project module is
ENV PYTHONPATH=/app

# Expose port 8000 for FastAPI
EXPOSE 8000

# Start the FastAPI server using Uvicorn
CMD ["uvicorn", "mcp_project.main:app", "--host", "0.0.0.0", "--port", "8000"]
