FROM python:3.6-slim

ENV CELERY_BROKER redis://redis:6379/0
ENV CELERY_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . /queue
WORKDIR /queue

ENTRYPOINT celery worker -A tasks --loglevel=info