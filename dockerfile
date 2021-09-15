# syntax=docker/dockerfile:1

FROM python:3.8-alpine
WORKDIR /app
COPY requirements.txt requirements.txt
COPY whois.py whois.py
COPY crontab crontab
copy domains.yml domains.yml
COPY appSettings.yaml appSettings.yaml

RUN pip3 install -r requirements.txt
RUN crontab crontab
CMD ["crond", "-f"]
