FROM python:3-alpine

WORKDIR /home/python

RUN apk add --no-cache zlib-dev build-base python-dev jpeg-dev

ADD requirements.txt /home/python/
RUN pip install --no-cache-dir -r requirements.txt

ADD . /home/python/
RUN python manage.py migrate

STOPSIGNAL SIGINT
ENV DJANGO_SETTINGS_MODULE=get_together.environ_settings
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

