FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Initialize data stores
RUN python main.py init

# Expose port
EXPOSE 8080

# Run the agent
CMD ["python", "-m", "bedrock_agentcore.runtime", "src/agentcore_runtime.py"]
