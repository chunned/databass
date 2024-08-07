FROM python:3.12-slim

RUN pip3 install gunicorn

COPY . /databass
WORKDIR /databass

RUN pip3 install -r requirements.txt
RUN touch /databass/music.db

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "databass:app"]
