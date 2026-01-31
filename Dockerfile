FROM apache/airflow:2.8.1
USER root
# Cài đặt các thư viện hệ thống cần thiết (nếu cần compile)
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         build-essential \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

USER airflow
# Copy file requirements và cài đặt
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt