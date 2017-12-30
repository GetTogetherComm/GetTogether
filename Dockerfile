FROM ubuntu:latest
EXPOSE 8000
RUN apt-get update && apt-get upgrade -y && apt-get install -y python3 python3-pip
COPY . /home/python
WORKDIR /home/python
RUN pip3 install -r requirements.txt
RUN python3 manage.py migrate
RUN python3 manage.py createsuperuser
ENTRYPOINT python3 manage.py runserver 0.0.0.0:8000
