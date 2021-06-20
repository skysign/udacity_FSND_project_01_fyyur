#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import os
import sys
import dateutil.parser
import datetime
import logging
from logging import Formatter, FileHandler
logging.basicConfig(level=logging.DEBUG)
import babel

from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    venue_show = db.relationship('Show', backref='venue_show', lazy=True)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    artist_show = db.relationship('Show', backref='artist_show', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'


class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show {self.id} {self.artist_id} {self.venue_id} {self.start_time}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#
def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#
@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    venues = Venue.query.order_by(Venue.id.desc()).all()
    uniques = set()

    for venue in venues:
        uniques.add((venue.city, venue.state));

    areas = []
    for unique in uniques:
        areas.append({
            "city": unique[0],
            "state": unique[1],
            "venues": []
        })

    num_shows = 0

    for venue in venues:
        for area in areas:
            if area['city'] == venue.city and area['state'] == venue.state:
                area['venues'].append({
                    'id': venue.id,
                    'name': venue.name,
                    'num_upcoming_shows': num_shows
                })

    return  render_template('pages/venues.html', areas=areas);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    name = request.form.get('search_term')
    venues = Venue.query.filter(Venue.name.ilike('%'+name+'%')).all()
    response = {
        "count": len(venues),
        "data": venues
    }

    return  render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.filter(Venue.id == venue_id).first()
    venue.genres = venue.genres.replace('{', '')
    venue.genres = venue.genres.replace('}', '')
    venue.genres = list(venue.genres.split(','))

    datas = Show.query.join("artist_show").\
        join("venue_show"). \
        add_columns(Artist.name, Artist.image_link, Venue.id). \
        filter(Venue.id == venue_id). \
        filter(Show.start_time >= datetime.now()).all()

    upcoming_shows = []
    for item in datas:
        upcoming_shows.append({
            'artist_id': item[0].artist_id,
            'artist_name': item[1],
            'artist_image_link': item[2],
            'start_time': format_datetime(str(item[0].start_time))
        })

    venue.upcoming_shows_count = len(upcoming_shows)
    venue.upcoming_shows = upcoming_shows

    datas = Show.query.join("artist_show").\
        join("venue_show"). \
        add_columns(Artist.name, Artist.image_link, Venue.id). \
        filter(Venue.id == venue_id). \
        filter(Show.start_time < datetime.now()).all()

    past_shows = []
    for item in datas:
        past_shows.append({
            'artist_id': item[0].artist_id,
            'artist_name': item[1],
            'artist_image_link': item[2],
            'start_time': format_datetime(str(item[0].start_time))
        })

    venue.past_shows_count = len(past_shows)
    venue.past_shows = past_shows

    return render_template('pages/show_venue.html', venue=venue)


#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        venue = Venue(
            name  = request.form['name'],
            city  = request.form['city'],
            state = request.form['state'],
            address = request.form['address'],
            phone   = request.form['phone'],
            genres  = request.form['genres'],
            facebook_link = request.form['facebook_link'],
            image_link    = request.form['image_link'],
            website_link  = request.form['website_link'],
            seeking_talent= True if request.form.get('seeking_talent') == 'y' else False,
            seeking_description = request.form['seeking_description']
        )
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        db.session.rollback()
    finally:
        db.session.close()
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.order_by(Artist.id.desc()).all()
  return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    name = request.form.get('search_term')
    artists = Artist.query.filter(Artist.name.ilike('%' + name + '%')).all()
    response = {
        "count": len(artists),
        "data": artists
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter(Artist.id == artist_id).first()
  artist.genres = artist.genres.replace('{', '')
  artist.genres = artist.genres.replace('}', '')
  artist.genres = list(artist.genres.split(','))

  datas = Show.query.join(Venue).\
      add_columns(Venue.name, Venue.image_link).\
      filter(Show.artist_id == artist_id).\
      filter(Show.start_time >= datetime.now()).all()

  upcoming_shows = []
  for item in datas:
      upcoming_shows.append({
          'venue_id': item[0].venue_id,
          'venue_name': item[1],
          'venue_image_link': item[2],
          'start_time': format_datetime(str(item[0].start_time))
      })

  artist.upcoming_shows_count = len(upcoming_shows)
  artist.upcoming_shows = upcoming_shows

  datas = Show.query.join(Venue, Show.venue_id == Venue.id).\
      add_columns(Venue.name, Venue.image_link).\
      filter(Show.artist_id == artist_id).\
      filter(Show.start_time < datetime.now()).all()

  past_shows = []
  for item in datas:
      past_shows.append({
          'venue_id': item[0].venue_id,
          'venue_name': item[1],
          'venue_image_link': item[2],
          'start_time': format_datetime(str(item[0].start_time))
      })

  artist.past_shows_count   = len(past_shows)
  artist.past_shows = past_shows

  return render_template('pages/show_artist.html', artist=artist)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter(Artist.id == artist_id).first()
  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    if form.validate():
        try:
            artist = {
                "name": request.form['name'],
                "city": request.form['city'],
                "state": request.form['state'],
                "phone": request.form['phone'],
                "genres": request.form.getlist('genres'),
                "facebook_link": request.form['facebook_link'],
                "image_link": request.form['image_link'],
                "website_link": request.form['website_link'],
                "seeking_venue": True if request.form.get('seeking_venue') == 'y' else False,
                "seeking_description": request.form['seeking_description']}
            Artist.query.filter_by(id=artist_id).update(artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] + ' was successfully updated!')
        except:
            db.session.rollback()
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
        finally:
            db.session.close()
    else:
        for error in form.errors:
            flash(form.errors[error][0])
        return redirect(url_for('edit_artist', artist_id=artist_id))

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter(Venue.id == venue_id).first()
  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)

    if form.validate():
        try:
            venue = {
                "name": request.form['name'],
                "city": request.form['city'],
                "state": request.form['state'],
                "phone": request.form['phone'],
                "genres": request.form.getlist('genres'),
                "facebook_link": request.form['facebook_link'],
                "image_link": request.form['image_link'],
                "website_link": request.form['website_link'],
                "seeking_talent": True if request.form.get('seeking_talent') == 'y' else False,
                "seeking_description": request.form['seeking_description']}
            Venue.query.filter_by(id=venue_id).update(venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully updated!')
        except:
            db.session.rollback()
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
        finally:
            db.session.close()
    else:
        for error in form.errors:
            flash(form.errors[error][0])
        return redirect(url_for('edit_venue', venue_id=venue_id))

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)

    if form.validate():
        try:
            artist = Artist(
                name  = request.form['name'],
                city  = request.form['city'],
                state = request.form['state'],
                phone = request.form['phone'],
                genres= request.form.getlist('genres'),
                image_link    = request.form['image_link'],
                facebook_link = request.form['facebook_link'],
                seeking_venue = True if request.form.get('seeking_venue') == 'y' else False,
                website_link  = request.form['website_link'],
                seeking_description = request.form['seeking_description'])
            db.session.add(artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] + ' was successfully listed!')

            return render_template('pages/home.html')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        finally:
            db.session.close()
    else:
        for error in form.errors:
            flash(form.errors[error][0])

    return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
  shows = []
  datas = Show.query.join("artist_show").join("venue_show").order_by(Show.start_time.desc()).all()
  for item in datas:
    shows.append({
      "venue_id": item.venue_id,
      "venue_name": item.venue_show.name,
      "artist_id": item.artist_id,
      "artist_name": item.artist_show.name,
      "artist_image_link": item.artist_show.image_link,
      "start_time": format_datetime(str(item.start_time))
    })

  return render_template('pages/shows.html', shows=shows)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    if form.validate():
        try:
            show = Show(
                artist_id = request.form['artist_id'],
                venue_id  = request.form['venue_id'],
                start_time= request.form['start_time'])
            db.session.add(show)
            db.session.commit()
            flash('Show was successfully listed!')
            return render_template('pages/home.html')
        except:
            db.session.rollback()
            flash('An error occurred. Show could not be listed.')
        finally:
            db.session.close()
    else:
        print(sys.exc_info())
        for error in form.errors:
            flash(form.errors[error][0])

    return render_template('forms/new_show.html', form=form)


@app.errorhandler(400)
def not_found_error(error):
    return render_template('errors/400.html', number=400), 400

@app.errorhandler(401)
def not_found_error(error):
    return render_template('errors/401.html', number=401), 401

@app.errorhandler(403)
def not_found_error(error):
    return render_template('errors/403.html', number=403), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', number=404), 404

@app.errorhandler(405)
def not_found_error(error):
    return render_template('errors/405.html', number=405), 405

@app.errorhandler(409)
def not_found_error(error):
    return render_template('errors/409.html', number=409), 409

@app.errorhandler(422)
def not_found_error(error):
    return render_template('errors/422.html', number=422), 422

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html', number=500), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9010))
    app.run(host='0.0.0.0', port=port)
