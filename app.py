import os
import sys
from flask import Flask
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask import redirect
from sqlalchemy import func
from sqlalchemy import exc
from sqlalchemy import select, update, delete, values
from sqlalchemy import text
from flask_restful import Resource, Api
from application import config
from application.config import LocalDevelopmentConfig, MailConfig
from application.database import db
from flask_cors import CORS
import datetime
from flask_mail import Mail

app = None
api = None

def create_app():
	app = Flask(__name__, template_folder="templates")
	if os.getenv('ENV', 'development') == 'production':
		raise Exception("Currently no production config is setup.")
	else:
		print("Starting Local Development")
		app.config.from_object(LocalDevelopmentConfig)
	db.init_app(app)
	api = Api(app)
	app.app_context().push()
	mail = Mail(app)
	app.config.from_object(MailConfig)
	mail = Mail(app)
	return app, api, mail

app, api, mail = create_app()
CORS(app)

#Import all the controllers so they are loaded
from application.controllers import *

#Add all restful controllers
from application.api import ShowAPI, VenueAPI
api.add_resource(ShowAPI, "/api/show", "/api/show/<int:show_id>")
api.add_resource(VenueAPI, "/api/venue", "/api/venue/<int:venue_id>")

if __name__ == '__main__':
	#Run the flask app
	app.run(debug = True)