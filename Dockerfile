FROM python:3.7-alpine
  
COPY . /slacker
WORKDIR /slacker

RUN apk update && apk add g++ make gcc libxslt libxslt-dev libxml2 libxml2-dev
RUN pip install -r requirements.txt

CMD sh
