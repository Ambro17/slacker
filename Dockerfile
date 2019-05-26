FROM python:3.7-alpine
  
ENV PYTHONUNBUFFERED 1

COPY . /slacker
WORKDIR /slacker

RUN apk update && apk add g++ make gcc libxslt libxslt-dev libxml2 libxml2-dev
RUN pip install -r requirements.txt

EXPOSE 3000

CMD ["gunicorn", "-w", "4", "application:app", "-b", "0.0.0.0:3000"]

