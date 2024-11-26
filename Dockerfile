FROM python:3.13.0-alpine3.20

COPY ./src /databass
WORKDIR /databass

RUN \
  apk add --no-cache postgresql-libs && \
  apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
  pip3 install gunicorn && \
  pip3 install -r requirements.txt && \
  apk add --no-cache nodejs npm && \
  apk --purge del .build-deps && \
  npm install -g less && \
  ln -s /usr/local/bin/lessc /usr/bin/lessc

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "databass:create_app()"]
