FROM python:3.6-slim
  
ENV PYTHONUNBUFFERED 1

COPY . /slacker
WORKDIR /slacker

RUN pip install -r requirements.txt

EXPOSE 3000

CMD ["gunicorn", "-w", "4", "application:app", "-b", "0.0.0.0:3000"]

