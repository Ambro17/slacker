FROM python:3.6-slim

ENV CELERY_BROKER redis://redis:6379/0
ENV CELERY_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true

RUN apt-get update && apt-get install -y git

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /queue
WORKDIR /queue

# Install awsadm dependency that was previously cloned
RUN pip install ./awsadm

RUN useradd -m slack_user
USER slack_user

EXPOSE 6379

CMD celery worker -A tasks --loglevel=info
