sudo apt-get -y install python3-pip unzip
if [ "$(pwd)" = "/home/vagrant" ]; then
    VAGRANT=1
    cd /vagrant
    sudo apt-get -y install expect
else
    VAGRANT=0
fi

pwd
PIP="pip3"
rm -fr $PWD/env
$PIP install virtualenv
virtualenv --python=python3 /vagrant/env
$PWD/env/bin/pip install -r requirements.txt

# Create local_settings.py if needed
if [ ! -f $PWD/local_settings.py ]; then
	cp $PWD/local_settings.example $PWD/local_settings.py
fi

# Perform migrations
$PWD/env/bin/python manage.py migrate

# Create superuser (if not already done)
if [ ! -f $PWD/.userCreated ]; then
	if [ $VAGRANT -eq 1 ]; then
    		$PWD/setup/test_user_vagrant.expect
	else
    		$PWD/env/bin/python manage.py createsuperuser
	fi
	touch $PWD/.userCreated
fi

# Start server
if [ "$( ps aux | grep python | grep manage | wc -l)" == "2" ]; then
	for i in $(ps aux | grep python | grep manage | awk '{print $2}'); do
		kill $i
	done
fi

# Load country info
if [ ! -f countryInfo.txt ]; then
	wget http://download.geonames.org/export/dump/countryInfo.txt
	$PWD/env/bin/python manage.py load_countries countryInfo.txt
fi

# Load SPR data
if [ ! -f admin1CodesASCII.txt ]; then
	wget http://download.geonames.org/export/dump/admin1CodesASCII.txt
	$PWD/env/bin/python manage.py load_spr admin1CodesASCII.txt
fi

# Load cities data
# TODO: Let this be variable?
if [ ! -f cities15000.txt ]; then
	wget http://download.geonames.org/export/dump/cities15000.zip
	unzip cities15000.zip
	$PWD/env/bin/python manage.py load_cities cities15000.txt
fi

if [ $VAGRANT -eq 1 ]; then
	nohup $PWD/env/bin/python manage.py runserver 192.168.42.42:8000 > output 2>&1 &
else
	$PWD/env/bin/python manage.py runserver
fi
