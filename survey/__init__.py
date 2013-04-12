import os
from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)

#Load the application
app.config.from_envvar('SURVEY_APPLICATION_SETTINGS')

#SQLAlchemy Setup
db = SQLAlchemy(app)

#Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

#dynamic images config
application_root_directory = os.path.dirname(os.path.realpath(__file__))
app.config['DYNAMIC_IMAGES_DIRECTORY'] = os.path.join(application_root_directory, 'static/dynamicimages')

import views
import utils

