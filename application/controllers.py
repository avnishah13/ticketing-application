from flask import Flask, request, url_for, flash
from flask import render_template, redirect
from flask import current_app as app
from application.models import User, City, Venue, Show, Booking, Movie
from flask import redirect
from application.database import db
from sqlalchemy import func
from sqlalchemy import exc
from sqlalchemy import select, update, delete, values
from sqlalchemy import text
import datetime
from datetime import timedelta
import re
from flask_mail import Mail, Message
from app import mail
from operator import itemgetter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import numpy as np
import seaborn as sns

@app.route("/", methods=["GET"])
def home():
	return render_template("login_select.html")

@app.route("/user", methods=["GET", "POST"])
def user_login():
	if request.method == "GET":
		return render_template("user_login.html")
	elif request.method == "POST":
		form_username = request.form["username"]
		username = db.session.query(User).with_entities(User.username).filter(User.username==form_username)
		
		form_password = request.form["password"]
		password = db.session.query(User).with_entities(User.password).filter(User.username==form_username)

		if username.first():
			global global_user_id
			global_user_id = db.session.query(User).with_entities(User.user_id).filter(User.username==form_username)
			global_user_id = global_user_id.first()[0]

			password = password.first()[0]
			if password==form_password:
				return redirect(url_for('user_home', user_id=global_user_id))

		else:
			return render_template("user_unavailable.html")


@app.route("/user/new", methods=["GET", "POST"])
def user_signup():
	if request.method == "GET":
		cities = City.query.all()
		return render_template("user_signup.html", cities=cities)
	elif request.method == "POST":
		try:
			user = User(user_type='user', name=request.form["name"], username=request.form["username"], password=request.form["password"], email=request.form["email"], phone=request.form["phone"], city=request.form["city"])
			
			db.session.add(user)
			db.session.commit()

			global global_user_id
			global_user_id = db.session.query(User).with_entities(User.user_id).filter(User.username==request.form["username"])
			global_user_id = global_user_id.first()[0]

			return redirect(url_for('user_home', user_id=global_user_id))

		except exc.IntegrityError as e:
			db.session.rollback()
			return render_template("unique_violation.html")

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
	if request.method == "GET":
		return render_template("admin_login.html")

	elif request.method == "POST":
		form_username = request.form["username"]
		username = db.session.query(User).with_entities(User.username).filter(User.username==form_username, User.user_type=='admin')
		
		form_password = request.form["password"]
		password = db.session.query(User).with_entities(User.password).filter(User.username==form_username, User.user_type=='admin')

		if username.first():
			password = password.first()[0]
			if password==form_password:
				return redirect("/admin/home")

		else:
			return render_template("admin_unavailable.html")

@app.route("/admin/home", methods=["GET"])
def admin_home():
	if request.method == "GET":
		total = 0
		bestselling = []
		popular_venue = []
		dist = {}
		dict1 = {}

		#Total Sales
		bookings = Booking.query.join(Show).add_columns(Booking.show_id, Show.price, Booking.seat_id).filter(Booking.show_id == Show.show_id)

		for booking in bookings:
			seats = (booking.seat_id).split(", ")
			seats = len(seats)
			total += booking.price * seats

		#Sales Distribution and Bestselling Movie
		movies = db.session.query(Movie, Booking, Show).add_columns(Movie.title, Show.price, Booking.seat_id).filter(Booking.show_id == Show.show_id, Show.movie_id==Movie.movie_id).all()

		for movie in movies:
			bestselling.append(movie.title)
			seats = (booking.seat_id).split(", ")
			seats = len(seats)

			if movie.title in dist:
				dist[movie.title] += booking.price * seats
			else:
				dist[movie.title] = booking.price * seats

		bestselling = max(bestselling,key=bestselling.count)

		labels = list(dist.keys())
		values = list(dist.values())

		plt.pie(values, labels=labels, colors=sns.color_palette('pastel'))
		plt.title("Sales Distribution")
		plt.savefig("C:/Ticket Show Application/static/images/pie.png")
		plt.close()

		#Total Users
		users = User.query.filter(User.user_type=="user").count()

		#Bestselling Venue
		venues = db.session.query(Venue, Booking, Show).add_columns(Venue.name, Show.price, Booking.seat_id).filter(Booking.show_id == Show.show_id, Show.venue_id==Venue.venue_id).all()

		for venue in venues:
			popular_venue.append(venue.name)
			seats = (booking.seat_id).split(", ")
			seats = len(seats)

			if venue.name in dict1:
				dict1[venue.name] += booking.price * seats
			else:
				dict1[venue.name] = booking.price * seats

		popular_venue = max(popular_venue,key=popular_venue.count)

		labels = list(dict1.keys())
		values = list(dict1.values())

		plt.bar(labels, values, color=sns.color_palette('pastel'))
		plt.title("Best Selling Venues")
		plt.xticks(rotation=10)
		plt.savefig("C:/Ticket Show Application/static/images/bar.png")
		plt.close()

		return render_template("admin_home.html", total=total, bestselling=bestselling, users=users, popular_venue=popular_venue, dist=dist)

@app.route("/admin/venue", methods=["GET"])
def venue_management():
	if request.method == "GET":
		venues = Venue.query.all()
		return render_template("venue_management.html", venues=venues)

@app.route("/admin/venue/create", methods=["GET", "POST"])
def create_venue():
	if request.method == "GET":
		cities = City.query.all()
		return render_template("create_venue.html", cities=cities)

	elif request.method == "POST":
		venue = Venue(name=request.form["name"], capacity=request.form["capacity"], city=request.form["city"], image=request.form["image"])
			
		db.session.add(venue)
		db.session.commit()

		return redirect("/admin/venue")

@app.route("/admin/venue/<int:venue_id>/edit", methods=["GET", "POST"])
def edit_venue(venue_id):
	if request.method == "GET":
		venue = Venue.query.get(venue_id)
		cities = City.query.all()

		return render_template("edit_venue.html", venue=venue, cities=cities)

	elif request.method == "POST":
		u = update(Venue)
		u = u.values({"name":request.form["name"], "capacity":request.form["capacity"], "city":request.form["city"], "image":request.form["image"]})
		u = u.where(Venue.venue_id == venue_id)
		db.session.execute(u)

		db.session.commit()

		return redirect("/admin/venue")

@app.route("/admin/venue/<int:venue_id>/remove", methods=["GET", "POST"])
def remove_venue(venue_id):
	if request.method == "GET":
		venue = Venue.query.get(venue_id)
		return render_template("remove_venue.html", venue=venue)

	elif request.method == "POST":
		#Delete from venue table
		venue = Venue.query.filter(Venue.venue_id==venue_id).delete()

		#Delete from bookings table
		shows = Show.query.filter(Show.venue_id==venue_id)

		for show in shows:
			bookings = Booking.query.filter(Booking.show_id==show.show_id).delete()

		#Delete from show table
		show = Show.query.filter(Show.venue_id==venue_id).delete()
		
		db.session.commit()
		return redirect("/admin/venue")

@app.route("/admin/show", methods=["GET"])
def show_management():
	if request.method == "GET":
		venues = Venue.query.all()
		shows = Show.query.all()
		movies = Movie.query.all()
		return render_template("show_management.html", shows=shows, movies = movies, venues=venues, datetime=datetime)

@app.route("/admin/show/create", methods=["GET", "POST"])
def add_show():
	venues = Venue.query.all()
	movies = Movie.query.all()

	if request.method == "GET":
		return render_template("add_show.html", venues=venues, movies=movies)

	elif request.method == "POST":
		#Get movie_id based on movie title
		movie_id = db.session.query(Movie).with_entities(Movie.movie_id).filter(Movie.title==request.form.get("movie"))
		movie_id = movie_id.first()[0]

		#Get venue_id based on venue name
		venue_id = db.session.query(Venue).with_entities(Venue.venue_id).filter(Venue.name==request.form.get("venue"))
		venue_id = venue_id.first()[0]

		#Get start time in correct datetime format
		start_time_split = request.form["start_time"]
		start_time_split = start_time_split.split(":")
		start_time = datetime.time(int(start_time_split[0]), int(start_time_split[1]), 00)

		#Get duration based on movie_id
		duration = db.session.query(Movie).with_entities(Movie.duration).filter(Movie.movie_id==movie_id)
		duration = duration.first()[0]

		#Get the hours and minutes variables from the duration
		x = re.findall(r"\d", duration)

		hours = int(x[0])
		minutes = int(x[1]+x[2])

		#Get the year, month, day variables from the date variable extracted from the form
		date = request.form["date"].split("-")
		year, month, day = int(date[0]), int(date[1]), int(date[2])

		#Add the duration of the movie to the start time to get the end time
		end_time = (datetime.datetime.combine(datetime.date(year, month, day),start_time) + timedelta(minutes=minutes, hours=hours)).time()
		end_day_and_time = (datetime.datetime.combine(datetime.date(year, month, day),start_time) + timedelta(minutes=minutes, hours=hours))

		#Get the start day and time and compare with current date to check if the date hasn't passed yet.
		start_day_and_time = datetime.datetime.strptime(request.form["date"], "%Y-%m-%d").strftime('%Y-%m-%d')

		if start_day_and_time < datetime.datetime.now().strftime('%Y-%m-%d'):
			return render_template("invalid_date.html")

		#Get start and end date and time
		start_day_and_time = str(request.form["date"] +" "+ request.form["start_time"])
		start_day_and_time = datetime.datetime.strptime(start_day_and_time, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")

		end_day_and_time = datetime.datetime.strftime(end_day_and_time, "%Y-%m-%d %H:%M:%S")

		#Iterate through the table to get all the start and end times
		database_start_day_and_time = db.session.query(Show).with_entities(Show.date, Show.start_time, Show.show_id).filter(Show.date==request.form.get("date"), Show.venue_id==venue_id)
		database_end_day_and_time = db.session.query(Show).with_entities(Show.date, Show.end_time, Show.show_id).filter(Show.date==request.form.get("date"), Show.venue_id==venue_id)

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
							return render_template("invalid_date.html")
					else:
						show = Show(date=request.form["date"], price=request.form["price"], start_time=str(start_time), end_time=str(end_time), venue_id=venue_id, movie_id=movie_id)
						db.session.add(show)
						db.session.commit()

						return redirect("/admin/show")

		else:
			show = Show(date=request.form["date"], price=request.form["price"], start_time=str(start_time), end_time=str(end_time), venue_id=venue_id, movie_id=movie_id)
			db.session.add(show)
			db.session.commit()

			return redirect("/admin/show")

@app.route("/admin/show/<int:show_id>/remove", methods=["GET", "POST"])
def remove_show(show_id):
	if request.method == "GET":
		show = Show.query.get(show_id)
		return render_template("remove_show.html", show=show)

	elif request.method == "POST":
		show = Show.query.filter(Show.show_id==show_id).delete()
		
		db.session.commit()
		return redirect("/admin/show")

@app.route("/admin/show/<int:show_id>/edit", methods=["GET", "POST"])
def edit_show(show_id):
	if request.method == "GET":
		venues = Venue.query.all()
		show = Show.query.get(show_id)
		movies = Movie.query.all()

		return render_template("edit_show.html", show=show, venues=venues, movies=movies)

	elif request.method == "POST":
		#Get movie_id based on movie title
		show = Show.query.get(show_id)

		movie_id = db.session.query(Movie).with_entities(Movie.movie_id).filter(Movie.title==request.form.get("movie"))
		movie_id = movie_id.first()[0]

		#Get venue_id based on venue name
		venue_id = db.session.query(Venue).with_entities(Venue.venue_id).filter(Venue.name==request.form.get("venue"))
		venue_id = venue_id.first()[0]

		#Get start time in correct datetime format
		start_time_split = request.form["start_time"]
		start_time_split = start_time_split.split(":")
		start_time = datetime.time(int(start_time_split[0]), int(start_time_split[1]), 00)

		#Get duration based on movie_id
		duration = db.session.query(Movie).with_entities(Movie.duration).filter(Movie.movie_id==movie_id)
		duration = duration.first()[0]

		#Get the hours and minutes variables from the duration
		x = re.findall(r"\d", duration)

		hours = int(x[0])
		minutes = int(x[1]+x[2])

		#Get the year, month, day variables from the date variable extracted from the form
		date = request.form["date"].split("-")
		year, month, day = int(date[0]), int(date[1]), int(date[2])

		#Add the duration of the movie to the start time to get the end time
		end_time = (datetime.datetime.combine(datetime.date(year, month, day),start_time) + timedelta(minutes=minutes, hours=hours)).time()
		end_day_and_time = (datetime.datetime.combine(datetime.date(year, month, day),start_time) + timedelta(minutes=minutes, hours=hours))

		#Get the start day and time and compare with current date to check if the date hasn't passed yet.
		start_day_and_time = datetime.datetime.strptime(request.form["date"], "%Y-%m-%d").strftime('%Y-%m-%d')

		if start_day_and_time < datetime.datetime.now().strftime('%Y-%m-%d'):
			return render_template("invalid_date.html", show=show)

		#Get start and end date and time
		start_day_and_time = str(request.form["date"] +" "+ request.form["start_time"])
		start_day_and_time = datetime.datetime.strptime(start_day_and_time, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")

		end_day_and_time = datetime.datetime.strftime(end_day_and_time, "%Y-%m-%d %H:%M:%S")

		#Iterate through the table to get all the start and end times
		database_start_day_and_time = db.session.query(Show).with_entities(Show.date, Show.start_time, Show.show_id).filter(Show.date==request.form.get("date"), Show.venue_id==venue_id)
		database_end_day_and_time = db.session.query(Show).with_entities(Show.date, Show.end_time, Show.show_id).filter(Show.date==request.form.get("date"), Show.venue_id==venue_id)

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
							return render_template("invalid_date.html", show=show)
						else:
							u = update(Show)
							u = u.values({"date":request.form["date"], "price":request.form["price"], "start_time":str(start_time), "end_time":str(end_time), "venue_id":venue_id, "movie_id":movie_id})
							u = u.where(Show.show_id == show_id)
							db.session.execute(u)
							db.session.commit()

							return redirect("/admin/show")

		else:
			u = update(Show)
			u = u.values({"date":request.form["date"], "price":request.form["price"], "start_time":str(start_time), "end_time":str(end_time), "venue_id":venue_id, "movie_id":movie_id})
			u = u.where(Show.show_id == show_id)
			db.session.execute(u)
			db.session.commit()

			return redirect("/admin/show")

@app.route("/admin/movie/create", methods=["GET", "POST"])
def add_movie():
	if request.method == "GET":
		return render_template("add_movie.html")

	elif request.method == "POST":
		hours = request.form["hours"]
		minutes = request.form["minutes"]

		duration = hours + "h " + minutes + "m"

		genre = request.form.getlist('genre')
		genre = ', '.join(genre)

		movie = Movie(title=request.form["title"], description=request.form["description"], duration=duration, language=request.form["language"], release_date=request.form["release_date"], genre=genre, poster=request.form["poster"], rating=request.form["rating"])
			
		db.session.add(movie)
		db.session.commit()

		return redirect("/admin/show")

@app.route("/user/<user_id>/home", methods=["GET"])
def user_home(user_id):
	if request.method == "GET":
		cities = City.query.all()
		movies = Movie.query.all()
		venues = Venue.query.all()

		return render_template("user_home.html", cities=cities, movies=movies, venues=venues, user_id=user_id, message=request.args.get('message'))

@app.route("/user/<user_id>/movie/<movie_id>")
def movie_details(movie_id, user_id):
	if request.method == "GET":
		movie = Movie.query.get(movie_id)
		genre = movie.genre.split()

		recs = Movie.query.all()

		return render_template("movie_details.html", movie=movie, user_id=user_id, recs=recs, genre=genre, set=set, len=len)

@app.route("/user/<user_id>/movie/<movie_id>/book")
def show_select(movie_id, user_id):
	if request.method == "GET":
		shows = Show.query.all()
		venues = Venue.query.all()
		movie = Movie.query.get(movie_id)
		user = User.query.get(user_id)

		list1 = []

		venue_ids = db.session.query(Venue).with_entities(Venue.venue_id).filter(Venue.city==user.city)

		for venue_id in venue_ids:
			dates = db.session.query(Show).with_entities(Show.date).filter(Show.movie_id==movie_id, Show.venue_id == venue_id[0])
			for date in dates:
				list1.append(date[0])

		if list1:
			for date in list1:
				if (datetime.date.today() + timedelta(days=7)).strftime('%Y-%m-%d') > datetime.datetime.strptime(date,"%Y-%m-%d").strftime('%Y-%m-%d') > datetime.datetime.now().strftime('%Y-%m-%d'):
					return render_template("show_select.html", movie=movie, shows=shows, venues=venues, user=user, datetime=datetime, timedelta=timedelta)

		return render_template("shows_unavailable.html", user_id=user_id)

@app.route("/user/<user_id>/movie/<movie_id>/book/<show_id>", methods=["GET", "POST"])
def book_seats(movie_id, user_id, show_id):
	if request.method == "GET":
		show = Show.query.get(show_id)

		venue = db.session.query(Venue).filter(Venue.venue_id==show.venue_id)
		venue = venue.first()

		seats = db.session.query(Booking).with_entities(Booking.seat_id).filter(Booking.show_id==show_id).all()

		seat_list = []

		for seat in seats:
			list = seat[0].split(", ")
			for i in list:
				i = str(ord(i[0])-64) + "_" + str(i[1:])
				seat_list.append(i)

		capacity = db.session.query(Venue).with_entities(Venue.capacity).filter(Venue.venue_id==show.venue_id)
		capacity = capacity.first()[0]

		if len(seat_list) == capacity:
			return render_template("show_full.html", user_id=user_id, movie_id=movie_id)

		return render_template("book_seats.html", show=show, venue=venue, user_id=user_id, movie_id=movie_id, seat_list=seat_list, str=str)

	if request.method == "POST":
		seats = request.form.getlist('seats')
		show = Show.query.get(show_id)
		user = db.session.query(User).filter(User.user_id==user_id)
		user = user.first()

		movie = db.session.query(Movie).filter(Movie.movie_id==movie_id)
		movie = movie.first()

		venue = db.session.query(Venue).filter(Venue.venue_id==show.venue_id)
		venue = venue.first()

		booking = db.session.query(Booking).order_by(Booking.booking_id.desc())
		booking = booking.first()

		if len(seats) == 0:
			return render_template("no_seats_selected.html", user_id=user_id, movie_id=movie_id, show=show)

		for i,j in enumerate(seats):
			k = (chr(ord('@')+int(j[0])))
			seats[i] = str(k) + j[2:]

		seat_id = ', '.join(seats)

		number_of_seats=len(seats)
		timestamp=str(datetime.datetime.now())

		booking = Booking(number_of_seats=len(seats), timestamp=str(datetime.datetime.now()), user_id=user_id, show_id=show_id, seat_id=seat_id)

		return redirect(url_for("booking_confirmation", user_id=user_id, movie_id=movie_id, show_id=show_id, number_of_seats=number_of_seats, timestamp=timestamp, seat_id=seat_id))

@app.route("/user/<user_id>/movie/<movie_id>/book/<show_id>/confirm", methods=["GET", "POST"])
def booking_confirmation(user_id, movie_id, show_id):
	if request.method == "GET":
		show=Show.query.get(show_id)
		movie = Movie.query.get(movie_id)
		venue=Venue.query.get(show.venue_id)

		number_of_seats=request.args.get('number_of_seats')
		return render_template("booking_confirmation.html", user_id=user_id, booking=request.args.get('booking'), show=show, movie=movie, venue=venue, number_of_seats=number_of_seats, timestamp=request.args.get('timestamp'), seat_id=request.args.get('seat_id'), total=int(number_of_seats)*int(show.price))

	if request.method == "POST":
		user = db.session.query(User).filter(User.user_id==user_id)
		user = user.first()

		show=Show.query.get(show_id)
		movie = Movie.query.get(movie_id)
		venue=Venue.query.get(show.venue_id)

		booking = Booking(number_of_seats=request.form['quantity'], timestamp=request.form['timestamp'], user_id=user_id, show_id=show_id, seat_id=request.form['seat_id'])
		db.session.add(booking)
		db.session.commit()

		msg = Message('Booking Successful!', sender = '21f1001736@ds.study.iitm.ac.in', recipients = [user.email])
		msg.body = '''
Dear {0},
This email is to confirm that your movie ticket has been successfully booked for {1} at {2} on {3} at {4}.

Your booking details are as follows:
Movie: {5}
Cinema: {6}
Date: {7}
Time: {8}
Seats: {9}
Ticket price: {10}

Please arrive at the cinema at least 15 minutes before the showtime to avoid any last-minute rush. Kindly present this email at the ticket counter to collect your physical ticket.

If you have any questions or concerns, please do not hesitate to contact us. We hope you enjoy the movie!

Thank you for choosing us.

Best regards,
Ticketable
		'''.format(user.name, movie.title, venue.name, show.date, show.start_time, movie.title, venue.name, show.date, show.start_time, booking.seat_id, show.price)
		mail.send(msg)

		return redirect(url_for("user_home", user_id=user_id, message="True"))

@app.route("/user/<user_id>/profile", methods=["GET", "POST"])
def user_profile(user_id):
	if request.method == "GET":
		list1 = []

		user = User.query.get(user_id)
		bookings = db.session.query(Booking).filter(Booking.user_id==user_id)

		for booking in bookings:
			show = db.session.query(Show).filter(Show.show_id==booking.show_id).first()
			movie = db.session.query(Movie).filter(Movie.movie_id==show.movie_id).first()
			venue = db.session.query(Venue).filter(Venue.venue_id==show.venue_id).first()

			list1.append([movie.title, venue.name, show.start_time + "-" + show.end_time, show.date])

		list1 = sorted(list1, key=itemgetter(3))

		return render_template("user_profile.html", user=user, list1=list1, user_id=user_id, datetime=datetime)

	elif request.method == "POST":
		rating = request.form.get("rating")

		movie_rating = db.session.query(Movie).with_entities(Movie.rating).filter(Movie.title == request.form["movie_title"]).first()[0]
		
		if movie_rating:
			u = update(Movie)
			u = u.values({"rating":(int(rating)+movie_rating)/2})
			u = u.where(Movie.title == request.form["movie_title"])

		else:
			u = update(Movie)
			u = u.values({"rating":rating})
			u = u.where(Movie.title == request.form["movie_title"])

		db.session.execute(u)
		db.session.commit()

		return redirect(request.url)

@app.route("/user/<user_id>/profile/edit", methods=["GET", "POST"])
def profile_edit(user_id):
	if request.method == "GET":
		user = User.query.get(user_id)
		cities = City.query.all()
		return render_template("edit_profile.html", user=user, cities=cities)

	elif request.method == "POST":
		u = update(User)
		u = u.values({"name":request.form["name"], "password":request.form["password"], "email":request.form["email"], "phone":request.form["phone"], "city":request.form["city"]})
		u = u.where(User.user_id == user_id)
		db.session.execute(u)

		db.session.commit()

		return redirect(url_for("user_profile", user_id=user_id))

@app.route("/user/<user_id>/search", methods=["POST"])
def search(user_id):
	if request.method == "POST":
		search = request.form["search"]

		movies = Movie.query.all()
		venues = Venue.query.all()
		user = User.query.get(user_id)

		if search:
			for movie in movies:
				if search.lower() in (movie.title).lower():
					movies = Movie.query.all()
					break
				else:
					movies = None

			for venue in venues:
				if search.lower() in (venue.name).lower():
					venues = Venue.query.all()
					break
				else:
					venues = None
		else:
			movies = None
			venues = None

		if not movies and not venues:
			return render_template("no_results.html", user_id=user_id)

		return render_template("search.html", user_id=user_id, search=search, movies=movies, venues=venues, user=user)

@app.route("/user/<user_id>/venue/<venue_id>", methods=["GET", "POST"])
def venue_details(user_id, venue_id):
	if request.method == "GET":
		venue = Venue.query.get(venue_id)
		shows = Show.query.all()
		movies = Movie.query.all()
		user = User.query.get(user_id)

		dates = db.session.query(Show).with_entities(Show.date).filter(Show.venue_id==venue_id)

		if dates:
			for date in dates:
				if (datetime.date.today() + timedelta(days=7)).strftime('%Y-%m-%d') > datetime.datetime.strptime(date[0],"%Y-%m-%d").strftime('%Y-%m-%d') > datetime.datetime.now().strftime('%Y-%m-%d'):
					return render_template("venue_details.html", movies=movies, shows=shows, venue=venue, user=user, datetime=datetime, timedelta=timedelta)

		return render_template("venue_details.html", venue=venue, user=user)

@app.route("/user/<user_id>/search/<search>/filter/venues", methods=["GET", "POST"])
def search_venues(user_id, search):
	if request.method == "GET":

		venues = Venue.query.all()
		user = User.query.get(user_id)
		cities = City.query.all()

		if search:
			for venue in venues:
				if search.lower() in (venue.name).lower():
					venues = Venue.query.all()
					break
				else:
					venues = None
		else:
			venues = None

		if not venues:
			return render_template("no_results.html", user_id=user_id)

		return render_template("search_venues.html", user_id=user_id, search=search, venues=venues, user=user, cities=cities)

	if request.method == "POST":
		venues = Venue.query.all()
		user = User.query.get(user_id)
		cities = City.query.all()

		location=request.form["city"]

		if search:
			for venue in venues:
				if search.lower() in (venue.name).lower():
					if venue.city == location:
						venues = Venue.query.all()
						break
					else:
						venues = None
				else:
					venues = None
		else:
			venues = None

		if not venues:
			return render_template("no_results.html", user_id=user_id)

		return render_template("search_venues.html", user_id=user_id, search=search, venues=venues, user=user, cities=cities)

@app.route("/user/<user_id>/search/<search>/filter/movies", methods=["GET", "POST"])
def search_movies(user_id, search=search):
	if request.method == "GET":
		movies = Movie.query.all()
		user = User.query.get(user_id)

		if search:
			for movie in movies:
				if search.lower() in (movie.title).lower():
					movies = Movie.query.all()
					break
				else:
					movies = None

		else:
			movies = None

		if not movies:
			return render_template("no_results.html", user_id=user_id)

		return render_template("search_movies.html", user_id=user_id, search=search, movies=movies, user=user)

	if request.method == "POST":
		movies = Movie.query.all()
		user = User.query.get(user_id)
		rating = request.form['rating_filter']

		if search:
			for movie in movies:
				if search.lower() in (movie.title).lower():
					if movie.rating != '':
						if movie.rating >= int(rating):
							movies = Movie.query.all()
							break
						else:
							movies = None
					else:
						movies = None
				else:
					movies = None
		else:
			movies = None

		if not movies:
			return render_template("no_results.html", user_id=user_id)

		return render_template("search_movies.html", user_id=user_id, search=search, movies=movies, user=user, rating=rating, float=float)