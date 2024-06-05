FROM python:3.12.3-bookworm

RUN apt-get update

RUN mkdir /usr/src/metrics /data
WORKDIR /usr/src/metrics

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="/usr/src/metrics"
ENV COLUMNS=80

CMD python /usr/src/metrics/src/main.py
