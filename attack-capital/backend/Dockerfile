FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create data directory for SQLite
RUN mkdir -p data

# Expose the port
EXPOSE 8000

# Run the application
CMD ["python", "simple_server.py"]