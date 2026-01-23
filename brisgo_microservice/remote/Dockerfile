FROM python:3.11-slim

# Directory di lavoro
WORKDIR /app

# Dipendenze di sistema necessarie per mysqlclient
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice applicativo
COPY . .

# Cloud Run ascolta sempre su 8080
CMD ["gunicorn", "-b", ":8080", "app:app"]
