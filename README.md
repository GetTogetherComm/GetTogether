# Get Together

[![Build Status](https://travis-ci.org/GetTogetherComm/GetTogether.svg?branch=master)](https://travis-ci.org/GetTogetherComm/GetTogether)

Get Together is an open source event manager for local communities.

Get Together is version *0.8.0*.

Try it free at https://gettogether.community

## Goals
 * Be feature-competitive with Meetup.com
 * Allow multiple instances to share federated event data
 * Provide sustainable, cost-effective hosting for FOSS communites
 * Be developed and maintained by the communities using it

## Getting Started
To start running the service use the following commands:

```
virtualenv --python=python3 ./env
./env/bin/pip install -r requirements.txt
./env/bin/python manage.py migrate
./env/bin/python manage.py createsuperuser
./env/bin/python manage.py runserver
```

### Loading City data

In order to make it easier to create Places and Teams without having to manually
enter records for Country, SPR (State/Province/Region) and City, you can preload
them using data files from http://download.geonames.org/export/dump/

The provided `load_spr` and `load_cities` commands will only load data if the
parent country (or SPR for cities) exists in the database. This lets you choose
whether you want to load every city, only cities for select countries, or only
for select SPRs.

#### Countries

Download the [countryInfo.txt](http://download.geonames.org/export/dump/countryInfo.txt)
file from GeoNames, then run:

`./env/bin/python manage.py load_countries countryInfo.txt`

#### SPR

Download the [admin1CodesASCII.txt](http://download.geonames.org/export/dump/admin1CodesASCII.txt)
file from GeoNames, then run:

`./env/bin/python manage.py load_spr admin1CodesASCII.txt`

#### Cities

You have a few choices for City data files. GeoNames provides data files for
cities with [more than 15,000](http://download.geonames.org/export/dump/cities15000.zip)
residents, cities with [more than 5,000](http://download.geonames.org/export/dump/cities5000.zip)
residents, and cities [with more than 1,000](http://download.geonames.org/export/dump/cities1000.zip)
residents. The smaller the number, the more cities there will be in the data
file (and the longer it will take to import them all).

Download the file you want from the links above. They will be zip files that you
must unzip before using. Then import the cities by running (for your downloaded
file):

`./env/bin/python manage.py load_cities cities15000.txt`

### Using docker
```
docker build -t get_together .
docker run -e "DEBUG_MODE=True" -e "SECRET_KEY=xxxxx" -e "ALLOWED_HOSTS=localhost,127.0.0.1" -d --name get_together -p 8000:8000 get_together
docker exec -it get_together python3 manage.py createsuperuser
```

### Using docker-compose
```
docker-compose up -d
docker-compose exec get_together python3 manage.py createsuperuser
```

You can then connect to the container by going to localhost:8000

## Test Federation
You can import live event data into your "Searchable" table with this command:

`./env/bin/python manage.py import https://gettogether.community/searchables/`


## Getting Involved

To contibute to Get Together, you can file issues here on GitHub, work on
features you want it to have, or contact us on [Gitter](https://gitter.im/GetTogetherComm/Lobby) to learn more.

Currently the project needs:
 * Designers
   * We need a color scheme for the website
   * We need a logo for the project
   * We need user stories and mockups for those pages
 * Front-end developers
   * We need to pick a JS/CSS framework for the front-end
   * We need to Django page templates
   * We need to know what APIs are needed for a dynamic front-end
 * QA Engineers
   * We need Django test cases setup
   * We need fuzz-testing setup with something like model-mommy
   * We want testing automated on github pull requests
 * API/Federation experts
   * We need to decide on using AppStream or rolling our own data/protocol
   * We need to architect what data will be federated and it's use cases
   * We need to support authenticated access to APIs for 3rd party apps
 * Devops
   * We need a way to easily deploy and update GetTogether in production
   * We need an easy way to get a development environment up and running
   * We need to find a hosting service for gettogether.community

If you can help with any of these, please get in touch with me!
