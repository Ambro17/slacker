FROM python:3.6-slim

ENV PYTHONUNBUFFERED 1
ENV PORT=3000

RUN apt-get update && apt-get install -qq -y build-essential --no-install-recommends

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /slacker
WORKDIR /

RUN useradd -m slack_user
USER slack_user

EXPOSE 3000

CMD gunicorn -w 4 "slacker.app:create_app()" -b 0.0.0.0:$PORT
