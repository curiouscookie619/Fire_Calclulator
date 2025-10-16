# Lightweight Python image
FROM python:3.11-slim

# Avoid prompts & set working dir
ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1     PORT=8501

WORKDIR /app

# System deps (optional but useful for fonts/locales)
RUN apt-get update && apt-get install -y --no-install-recommends \ 
    fonts-dejavu-core     && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

# Expose the port Streamlit listens on
EXPOSE 8501

# Run the app (respect $PORT from PaaS)
CMD ["/bin/bash", "app_entry.sh"]
