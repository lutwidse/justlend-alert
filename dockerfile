FROM python:3.9.7-slim-buster
ENV ENV_JUSTALERT_ADDR=${ENV_JUSTALERT_ADDR}
ENV ENV_JUSTALERT_TOKEN=${ENV_JUSTALERT_TOKEN}
WORKDIR /justlend_alert
COPY . /justlend_alert
RUN pip install -r requirements.txt
CMD [ "python", "./main.py" ]