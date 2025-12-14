FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY langgraph_app /app/langgraph_app

# Install Python dependencies
RUN pip install --no-cache-dir \
    langgraph \
    langchain \
    langchain-community \
    pydantic \
    pydantic-settings \
    psycopg[binary] \
    redis \
    requests \
    PyPDF2 \
    beautifulsoup4 \
    && rm -rf /root/.cache

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "langgraph_app.worker"]
