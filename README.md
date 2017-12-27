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
to learn more.

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
