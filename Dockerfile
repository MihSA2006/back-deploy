FROM python:3.12-slim

# Variables utiles
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installer les dépendances système pour dlib/opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git \
    libopenblas-dev liblapack-dev \
    libx11-dev libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Installer Python deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le projet
COPY . .

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Lancer gunicorn avec uvicorn worker (ASGI)
CMD gunicorn i_fidy_back.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --log-file -
