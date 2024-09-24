FROM python:3.12.3-bookworm

RUN apt-get update && apt-get install -y \
    default-mysql-client \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev

RUN mkdir /usr/src/metrics /data
WORKDIR /usr/src/metrics

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="/usr/src/metrics"
ENV COLUMNS=80

CMD ["python", "/usr/src/metrics/src/main.py"]