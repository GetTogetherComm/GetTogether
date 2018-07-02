FROM ubuntu:latest
RUN apt-get update && apt-get upgrade -y && apt-get install -y python3 python3-pip
COPY requirements.txt /home/python/requirements.txt
WORKDIR /home/python
RUN pip3 install -r requirements.txt
COPY . /home/python
RUN python3 manage.py migrate

EXPOSE 8000
STOPSIGNAL SIGINT
ENTRYPOINT ["python3", "manage.py"]
CMD ["runserver", "0.0.0.0:8000"]
