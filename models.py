from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    display_name = db.Column(db.String(120), nullable=True)
    password = db.Column(db.String(200), nullable=False)  # هش ذخیره می‌کنیم

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='idea')
    bpm = db.Column(db.Float, default=84.0)
    song_key = db.Column(db.String(20), nullable=True)
    mood = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# لیرکس و تایم‌لاین برحسب beat
class Lyrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'))
    version = db.Column(db.Integer, default=1)
    content_raw = db.Column(db.Text, default='')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LyricsLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lyrics_id = db.Column(db.Integer, db.ForeignKey('lyrics.id'))
    line_number = db.Column(db.Integer)
    text = db.Column(db.Text)
    beat = db.Column(db.Float, nullable=True)  # مثال: 8.5

# بند / عضویت / پروژه
class Band(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    passhash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BandMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    band_id = db.Column(db.Integer, db.ForeignKey('band.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role = db.Column(db.String(20), default='member')  # creator/admin/member
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('band_id','user_id', name='_band_user_uc'),)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    band_id = db.Column(db.Integer, db.ForeignKey('band.id'))
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProjectTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'))
    __table_args__ = (db.UniqueConstraint('project_id','track_id', name='_project_track_uc'),)
