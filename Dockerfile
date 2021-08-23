FROM python:3.7

WORKDIR /app

COPY requirements.txt .

RUN pip install vext
RUN apt update && apt install build-essential libdbus-glib-1-dev libgirepository1.0-dev -y
RUN pip install -r requirements.txt

COPY src .
COPY config.production.yml .

CMD python main.py