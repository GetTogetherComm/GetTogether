# Get Together

Get Together is an open source event manager for local communities.

## Goals
 * Be feature-competitive with Meetup.com
 * Allow multiple instances to share federated event data
 * Provide sustainable, cost-effective hosting for FOSS communites
 * Be developed and maintained by the communities using it

## Getting Started
To start running the service use the following commands:

`virtualenv --python=python3 ./env`

`./env/bin/pip install -r requirements.txt`

`./env/bin/python manage.py migrate`

`./env/bin/python manage.py createsuperuser`

`./env/bin/python manage.py runserver`

## Test Federation
You can import sample event data into your "Searchable" table with this command:

`./env/bin/python manage.py import http://people.ubuntu.com/~mhall119/searchable_test.json`


## Getting Involved

To contibute to Get Together, you can file issues here on GitHub, work on
features you want it to have, or contact @mhall119 on IRC, Telegram or Twitter
to learn more
