FROM python:3-alpine as builder

WORKDIR /home/python

RUN apk add --no-cache zlib-dev build-base python-dev jpeg-dev
RUN pip install virtualenv
RUN virtualenv venv

ADD requirements.txt /home/python/
RUN venv/bin/pip install --no-cache-dir -r requirements.txt
RUN virtualenv --relocatable venv/

ADD . /home/python/
RUN venv/bin/python manage.py migrate

FROM python:3-alpine

WORKDIR /home/python
COPY --from=builder /home/python /home/python

ENTRYPOINT ["venv/bin/python"]
CMD ["manage.py", "runserver", "0.0.0.0:8000"]
