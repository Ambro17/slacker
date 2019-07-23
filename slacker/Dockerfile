FROM python:3.6-slim

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV PYTHONUNBUFFERED 1

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . /slacker
WORKDIR /

EXPOSE 3000

CMD ["gunicorn", "-w", "4", "slacker:create_app()", "-b", "0.0.0.0:3000"]
