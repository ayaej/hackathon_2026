FROM apache/airflow:2.10.5

USER root

# Installation des dependances systeme pour opencv, tesseract, ghostscript
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copie des requirements du projet
COPY requirements.txt /tmp/requirements.txt

# Installation des dependances Python avec les bonnes options
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /tmp/requirements.txt
