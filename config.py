import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

SQLALCHEMY_TRACK_MODIFICATIONS = False

# Connect to the database
DB = 'postgresql'
DATABASE_NAME = 'FSND_projects_01_fyyur'
username = 'skysign'
password = 'fsndproject'
url = '127.0.0.1:5432'
SQLALCHEMY_DATABASE_URI = "{}://{}:{}@{}/{}".format(
    DB, username, password, url, DATABASE_NAME)