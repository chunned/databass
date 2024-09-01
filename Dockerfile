FROM python:3.12-alpine

COPY ./src /databass
WORKDIR /databass

RUN \
  apk add --no-cache postgresql-libs && \
  apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
  pip3 install gunicorn && \
  pip3 install -r requirements.txt && \
  apk --purge del .build-deps

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "databass:create_app()"]
