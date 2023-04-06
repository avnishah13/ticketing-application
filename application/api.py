from flask_restful import Resource
from flask_restful import fields, marshal_with
from flask_restful import reqparse

import datetime
from datetime import timedelta
import re
import sys

from application.database import db
from application.models import User, City, Venue, Show, Booking, Movie
from application.validation import NotFoundError, Error

output_fields_show = {
	"show_id" : fields.Integer,
	"date" : fields.String,
	"price" : fields.Integer,
	"start_time" : fields.String,
	"end_time" : fields.String,
	"venue_id" : fields.Integer,
	"movie_id" : fields.Integer
}

output_fields_venue = {
	"venue_id" : fields.Integer,
	"name" : fields.String,
	"capacity" : fields.Integer,
	"city" : fields.String,
	"image" : fields.String
}

create_show_parser = reqparse.RequestParser()
create_show_parser.add_argument('date')
create_show_parser.add_argument('price')
create_show_parser.add_argument('start_time')
create_show_parser.add_argument('end_time')
create_show_parser.add_argument('venue_id')
create_show_parser.add_argument('movie_id')

update_show_parser = reqparse.RequestParser()
update_show_parser.add_argument('date')
update_show_parser.add_argument('price')
update_show_parser.add_argument('start_time')
update_show_parser.add_argument('end_time')
update_show_parser.add_argument('venue_id')
update_show_parser.add_argument('movie_id')

create_venue_parser = reqparse.RequestParser()
create_venue_parser.add_argument('name')
create_venue_parser.add_argument('capacity')
create_venue_parser.add_argument('city')
create_venue_parser.add_argument('image')

update_venue_parser = reqparse.RequestParser()
update_venue_parser.add_argument('name')
update_venue_parser.add_argument('capacity')
update_venue_parser.add_argument('city')
update_venue_parser.add_argument('image')

class ShowAPI(Resource):
	@marshal_with(output_fields_show)
	def get(self, show_id):
		#Get the username
		print("In ShowAPI GET Method", show_id)

		#Get the Show from database based on show_id
		show = Show.query.get(show_id)

		if show:
			#Return a valid show JSON
			return {"show_id":show.show_id, "date":show.date, "price":show.price, "start_time":show.start_time, "end_time":show.end_time, "venue_id":show.venue_id, "movie_id":show.movie_id}
		else:
			#Return 404 error
			raise NotFoundError(status_code=404, error_message="Show not found")

	@marshal_with(output_fields_show)
	def put(self, show_id):
		args = update_show_parser.parse_args()
		date = args.get("date", None)
		price = args.get("price", None)
		start_time = args.get("start_time", None)
		venue_id = args.get("venue_id", None)
		movie_id = args.get("movie_id", None)

		if date is None:
			raise Error(status_code=400, error_code="SHOW001", error_message="Date is required")

		if price is None:
			raise Error(status_code=400, error_code="SHOW002", error_message="Price is required")

		if start_time is None:
			raise Error(status_code=400, error_code="SHOW003", error_message="Start Time is required")

		if venue_id is None:
			raise Error(status_code=400, error_code="SHOW004", error_message="Venue ID is required")

		if movie_id is None:
			raise Error(status_code=400, error_code="SHOW005", error_message="Movie ID is required")

		#Check if show exists
		show = Show.query.get(show_id)

		if show is None:
			#Return 404 error
			raise NotFoundError(status_code=404, error_message="Show not found")

		#Check if movie exists
		movie = Movie.query.get(movie_id)

		if movie is None:
			#Return 404 error
			raise NotFoundError(status_code=404, error_message="Movie not found")

		#Check if venue exists
		venue = Venue.query.get(venue_id)

		if venue is None:
			#Return 404 error
			raise NotFoundError(status_code=404, error_message="Venue not found")

		#Get start time in correct datetime format
		start_time = datetime.time(int(start_time[:2]), int(start_time[3:5]), 00)

		#Get duration based on movie_id
		duration = db.session.query(Movie).with_entities(Movie.duration).filter(Movie.movie_id==movie_id)
		duration = duration.first()[0]

		#Get the hours and minutes variables from the duration
		x = re.findall(r"\d", duration)

		hours = int(x[0])
		minutes = int(x[1]+x[2])

		#Get the year, month, day variables from the date variable extracted from the form
		split_date = date.split("-")
		year, month, day = int(split_date[0]), int(split_date[1]), int(split_date[2])

		#Add the duration of the movie to the start time to get the end time
		end_time = (datetime.datetime.combine(datetime.date(year, month, day),start_time) + timedelta(minutes=minutes, hours=hours)).time()
		end_day_and_time = (datetime.datetime.combine(datetime.date(year, month, day),start_time) + timedelta(minutes=minutes, hours=hours))

		#Get the start day and time and compare with current date to check if the date hasn't passed yet.
		start_day_and_time = datetime.datetime.strptime(date, "%Y-%m-%d").strftime('%Y-%m-%d')

		if start_day_and_time < datetime.datetime.now().strftime('%Y-%m-%d'):
			raise Error(status_code=400, error_code="SHOW006", error_message="Invalid Date")

		#Get start and end date and time
		start_day_and_time = str(date +" "+ args.get("start_time", None))
		start_day_and_time = datetime.datetime.strptime(start_day_and_time, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")

		end_day_and_time = datetime.datetime.strftime(end_day_and_time, "%Y-%m-%d %H:%M:%S")

		#Iterate through the table to get all the start and end times
		database_start_day_and_time = db.session.query(Show).with_entities(Show.date, Show.start_time, Show.show_id).filter(Show.date==date, Show.venue_id==venue_id)
		database_end_day_and_time = db.session.query(Show).with_entities(Show.date, Show.end_time, Show.show_id).filter(Show.date==date, Show.venue_id==venue_id)

		#Change the date if time is beyond 12am
		if database_start_day_and_time.first() and database_end_day_and_time.first():
			for x in database_start_day_and_time:
				for y in database_end_day_and_time:
					if x[2] == y[2]:
						if x[0][0:7] == y[0][0:7]:
							if y[1][:2] == '00' or y[1][:2] == '01' or y[1][:2] == '02':
								y = (y[0][:8] + str(int(y[0][8:]) + 1).zfill(2), y[1], y[2])

						#If times overlap, return error.
						if show_id != x[2] and end_day_and_time >= (x[0] + " " + x[1]) and (y[0] + " " + y[1]) >= start_day_and_time:
							raise Error(status_code=400, error_code="SHOW007", error_message="Time clash with other shows")

		show.date = date
		show.price = price
		show.start_time = args.get("start_time", None)
		show.end_time = str(end_time)
		show.venue_id = venue_id
		show.movie_id = movie_id
		db.session.add(show)
		db.session.commit()
		
		return show

	def delete(self, show_id):
		#Check if course exists
		show = Show.query.get(show_id)

		if show is None:
			#Return 404 error
			raise NotFoundError(status_code=404, error_message="Show not found")

		#Delete from bookings table
		bookings = Booking.query.filter(Booking.show_id==show_id).delete()
		
		#Delete from show table
		show = Show.query.filter(Show.show_id==show_id).delete()

		db.session.commit()

		return "Successfully Deleted", 200

	@marshal_with(output_fields_show)
	def post(self):
		args = create_show_parser.parse_args()
		date = args.get("date", None)
		price = args.get("price", None)
		start_time = args.get("start_time", None)
		venue_id = args.get("venue_id", None)
		movie_id = args.get("movie_id", None)

		if date is None:
			raise Error(status_code=400, error_code="SHOW001", error_message="Date is required")

		if price is None:
			raise Error(status_code=400, error_code="SHOW002", error_message="Price is required")

		if start_time is None:
			raise Error(status_code=400, error_code="SHOW003", error_message="Start Time is required")

		if venue_id is None:
			raise Error(status_code=400, error_code="SHOW005", error_message="Venue ID is required")

		if movie_id is None:
			raise Error(status_code=400, error_code="SHOW006", error_message="Movie ID is required")

		#Check if movie exists
		movie = Movie.query.get(movie_id)

		if movie is None:
			#Return 404 error
			raise NotFoundError(status_code=404, error_message="Movie not found")

		#Check if venue exists
		venue = Venue.query.get(venue_id)

		if venue is None:
			#Return 404 error
			raise NotFoundError(status_code=404, error_message="Venue not found")

		#Get start time in correct datetime format
		start_time = datetime.time(int(start_time[:2]), int(start_time[3:5]), 00)

		#Get duration based on movie_id
		duration = db.session.query(Movie).with_entities(Movie.duration).filter(Movie.movie_id==movie_id)
		duration = duration.first()[0]

		#Get the hours and minutes variables from the duration
		x = re.findall(r"\d", duration)

		hours = int(x[0])
		minutes = int(x[1]+x[2])

		#Get the year, month, day variables from the date variable extracted from the form
		split_date = date.split("-")
		year, month, day = int(split_date[0]), int(split_date[1]), int(split_date[2])

		#Add the duration of the movie to the start time to get the end time
		end_time = (datetime.datetime.combine(datetime.date(year, month, day),start_time) + timedelta(minutes=minutes, hours=hours)).time()
		end_day_and_time = (datetime.datetime.combine(datetime.date(year, month, day),start_time) + timedelta(minutes=minutes, hours=hours))

		#Get the start day and time and compare with current date to check if the date hasn't passed yet.
		start_day_and_time = datetime.datetime.strptime(date, "%Y-%m-%d").strftime('%Y-%m-%d')

		if start_day_and_time < datetime.datetime.now().strftime('%Y-%m-%d'):
			raise Error(status_code=400, error_code="SHOW006", error_message="Invalid Date")

		#Get start and end date and time
		start_day_and_time = str(date +" "+ args.get("start_time", None))
		start_day_and_time = datetime.datetime.strptime(start_day_and_time, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")

		end_day_and_time = datetime.datetime.strftime(end_day_and_time, "%Y-%m-%d %H:%M:%S")

		#Iterate through the table to get all the start and end times
		database_start_day_and_time = db.session.query(Show).with_entities(Show.date, Show.start_time, Show.show_id).filter(Show.date==date, Show.venue_id==venue_id)
		database_end_day_and_time = db.session.query(Show).with_entities(Show.date, Show.end_time, Show.show_id).filter(Show.date==date, Show.venue_id==venue_id)

		#Change the date if time is beyond 12am
		if database_start_day_and_time.first() and database_end_day_and_time.first():
			for x in database_start_day_and_time:
				for y in database_end_day_and_time:
					if x[2] == y[2]:
						if x[0][0:7] == y[0][0:7]:
							if y[1][:2] == '00' or y[1][:2] == '01' or y[1][:2] == '02':
								y = (y[0][:8] + str(int(y[0][8:]) + 1).zfill(2), y[1], y[2])

						#If times overlap, return error.
						if end_day_and_time >= (x[0] + " " + x[1]) and (y[0] + " " + y[1]) >= start_day_and_time:
							raise Error(status_code=400, error_code="SHOW007", error_message="Time clash with other shows")

		new_show = Show(date=date, price=price, start_time=args.get("start_time", None), end_time=str(end_time), venue_id=venue_id, movie_id=movie_id)
		db.session.add(new_show)
		db.session.commit()
		return new_show, 201

class VenueAPI(Resource):
	@marshal_with(output_fields_venue)
	def get(self, venue_id):
		#Get the username
		print("In VenueAPI GET Method", venue_id)

		#Get the Student from database based on course_id
		venue = Venue.query.get(venue_id)

		if venue:
			#Return a valid venue JSON
			return {"name":venue.name, "capacity":venue.capacity, "city":venue.city, "image":venue.image}
		else:
			#Return 404 error
			raise NotFoundError(status_code=404, error_message="Venue not found")

	@marshal_with(output_fields_venue)
	def put(self, venue_id):
		args = update_venue_parser.parse_args()
		name = args.get("name", None)
		capacity = args.get("capacity", None)
		city = args.get("city", None)
		image = args.get("image", None)

		if name is None:
			raise Error(status_code=400, error_code="VENUE001", error_message="Venue Name required")

		if capacity is None:
			raise Error(status_code=400, error_code="VENUE002", error_message="Capacity is required")

		if city is None:
			raise Error(status_code=400, error_code="VENUE003", error_message="City is required")

		if image is None:
			raise Error(status_code=400, error_code="VENUE004", error_message="Image Link is required")

		#Check if venue exists
		venue = Venue.query.get(venue_id)

		if venue is None:
			#Return 404 error
			raise NotFoundError(status_code=404, error_message="Venue not found")

		venue.name = name
		venue.capacity = capacity
		venue.city = city
		venue.image = image
		db.session.add(venue)
		db.session.commit()

		return venue

	def delete(self, venue_id):
		#Check if student exists
		venue = Venue.query.get(venue_id)

		if venue is None:
			#Return 404 error
			raise NotFoundError(status_code=404, error_message="Venue not found")

		#Delete from bookings table
		shows = Show.query.filter(Show.venue_id==venue_id)

		for show in shows:
			bookings = Booking.query.filter(Booking.show_id==show.show_id).delete()

		#Delete from show table
		show = Show.query.filter(Show.venue_id==venue_id).delete()
		
		#Delete from venue table
		venue = Venue.query.filter(Venue.venue_id==venue_id).delete()

		db.session.commit()

		return "Successfully Deleted", 200

	@marshal_with(output_fields_venue)
	def post(self):
		args = create_venue_parser.parse_args()
		name = args.get("name", None)
		capacity = args.get("capacity", None)
		city = args.get("city", None)
		image = args.get("image", None)

		if name is None:
			raise Error(status_code=400, error_code="VENUE001", error_message="Venue Name required")

		if capacity is None:
			raise Error(status_code=400, error_code="VENUE002", error_message="Capacity is required")

		if city is None:
			raise Error(status_code=400, error_code="VENUE003", error_message="City is required")

		if image is None:
			raise Error(status_code=400, error_code="VENUE004", error_message="Image Link is required")

		new_venue = Venue(name=name, capacity=capacity, city=city, image=image)
		db.session.add(new_venue)
		db.session.commit()
		return new_venue, 201