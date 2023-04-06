from application.database import db

class Booking(db.Model):
	__tablename__ = 'booking'
	booking_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
	number_of_seats = db.Column(db.Integer, nullable = False)
	timestamp = db.Column(db.String)
	user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
	show_id = db.Column(db.Integer, db.ForeignKey("show.show_id"), nullable=False)
	seat_id = db.Column(db.String, nullable=False)

class User(db.Model):
	__tablename__ = 'user'
	user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
	user_type = db.Column(db.String, nullable = False)
	name = db.Column(db.String, nullable=False)
	username = db.Column(db.String, nullable=False, unique=True)
	password = db.Column(db.String, nullable=False)
	email = db.Column(db.String, nullable=False, unique=True)
	phone = db.Column(db.Integer, nullable=False, unique=True)
	city = db.Column(db.String, db.ForeignKey("city.name"))

class City(db.Model):
	__tablename__ = 'city'
	name = db.Column(db.String, nullable = False, unique=True, primary_key=True)
	state = db.Column(db.String, nullable=False)

class Movie(db.Model):
	__tablename__ = 'movie'
	movie_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
	title = db.Column(db.String, nullable = False)
	description = db.Column(db.String, nullable=False)
	duration = db.Column(db.String, nullable=False)
	language = db.Column(db.String)
	release_date = db.Column(db.String)
	genre = db.Column(db.String, nullable=False)
	poster = db.Column(db.String, nullable=False)
	rating = db.Column(db.String)

class Show(db.Model):
	__tablename__ = 'show'
	show_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
	date = db.Column(db.String, nullable = False)
	price = db.Column(db.Integer, nullable=False)
	start_time = db.Column(db.String, nullable = False)
	end_time = db.Column(db.String, nullable=False)
	venue_id = db.Column(db.Integer, db.ForeignKey("venue.venue_id"), nullable=False)
	movie_id = db.Column(db.Integer, db.ForeignKey("movie.movie_id"), nullable=False)

class Venue(db.Model):
	__tablename__ = 'venue'
	venue_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
	name = db.Column(db.String, nullable = False)
	capacity = db.Column(db.Integer, nullable=False)
	city = db.Column(db.Integer, db.ForeignKey("city.name"), nullable = False)
	image = db.Column(db.String)