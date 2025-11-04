import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Track, Lyrics, LyricsLine, Band, BandMembership, Project, ProjectTrack

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///musicmvp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only')

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- Helpers ----------
def _user_memberships(uid):
    return db.session.query(Band, BandMembership)\
        .join(BandMembership, Band.id == BandMembership.band_id)\
        .filter(BandMembership.user_id == uid).all()

def _current_membership(band_id, uid):
    return BandMembership.query.filter_by(band_id=band_id, user_id=uid).first()

@app.context_processor
def inject_globals():
    b = None
    mems = []
    if current_user.is_authenticated:
        mems = _user_memberships(current_user.id)
        if 'band_id' in session:
            b = Band.query.get(session['band_id'])
    return dict(current_band=b, memberships=mems)

# ---------- Auth ----------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        uname = (request.form.get('username') or '').strip()
        dname = (request.form.get('display_name') or '').strip()
        pw    = (request.form.get('password') or '').strip()
        if not uname or not pw:
            return render_template('register.html', error='نام کاربری و رمز اجباری است.')
        if User.query.filter_by(username=uname).first():
            return render_template('register.html', error='این نام کاربری قبلاً استفاده شده.')
        u = User(username=uname, display_name=dname, password=generate_password_hash(pw))
        db.session.add(u); db.session.commit()
        login_user(u)
        return redirect(url_for('select_band'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        uname = (request.form.get('username') or '').strip()
        pw    = (request.form.get('password') or '').strip()
        u = User.query.filter_by(username=uname).first()
        if u and (check_password_hash(u.password, pw) or u.password == pw):
            login_user(u)
            return redirect(url_for('select_band'))
        return render_template('login.html', error='نام کاربری یا رمز اشتباه است')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('band_id', None)
    logout_user()
    return redirect(url_for('login'))

# ---------- Bands ----------
@app.route('/band/select', methods=['GET','POST'])
@login_required
def select_band():
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip()

        if action == 'switch':
            band_id = int(request.form['band_id'])
            m = _current_membership(band_id, current_user.id)
            if m:
                session['band_id'] = band_id
                return redirect(url_for('dashboard'))
            return render_template('select_band.html', error='عضو این بند نیستی.', memberships=_user_memberships(current_user.id))

        elif action == 'create':
            name = (request.form.get('new_band_name') or '').strip()
            pw   = (request.form.get('new_band_password') or '').strip()
            if not name or not pw:
                return render_template('select_band.html', error='نام و پسورد بند الزامی است.', memberships=_user_memberships(current_user.id))
            if Band.query.filter_by(name=name).first():
                return render_template('select_band.html', error='این نام بند قبلاً استفاده شده.', memberships=_user_memberships(current_user.id))
            b = Band(name=name, passhash=generate_password_hash(pw))
            db.session.add(b); db.session.commit()
            db.session.add(BandMembership(band_id=b.id, user_id=current_user.id, role='creator'))
            db.session.add(Project(band_id=b.id, name='Default'))
            db.session.commit()
            session['band_id'] = b.id
            return redirect(url_for('dashboard'))

        elif action == 'join':
            name = (request.form.get('band_name') or '').strip()
            pw   = (request.form.get('band_password') or '').strip()
            b = Band.query.filter_by(name=name).first()
            if not b or not check_password_hash(b.passhash, pw):
                return render_template('select_band.html', error='نام/پسورد بند درست نیست.', memberships=_user_memberships(current_user.id))
            if not _current_membership(b.id, current_user.id):
                db.session.add(BandMembership(band_id=b.id, user_id=current_user.id, role='member'))
                db.session.commit()
            session['band_id'] = b.id
            return redirect(url_for('dashboard'))

        elif action == 'invite_by_id':
            if 'band_id' not in session:
                return redirect(url_for('select_band'))
            band_id = session['band_id']
            mymem = _current_membership(band_id, current_user.id)
            if not mymem or mymem.role not in ('creator','admin'):
                return render_template('select_band.html', error='دسترسی دعوت نداری.', memberships=_user_memberships(current_user.id))
            uid = (request.form.get('user_id') or '').strip()
            if not uid.isdigit():
                return render_template('select_band.html', error='آیدی کاربر باید عدد باشد.', memberships=_user_memberships(current_user.id))
            uid = int(uid)
            if not User.query.get(uid):
                return render_template('select_band.html', error='چنین کاربری وجود ندارد.', memberships=_user_memberships(current_user.id))
            if not _current_membership(band_id, uid):
                db.session.add(BandMembership(band_id=band_id, user_id=uid, role='member'))
                db.session.commit()
            return render_template('select_band.html', ok='کاربر اضافه شد.', memberships=_user_memberships(current_user.id))

        elif action == 'invite_by_username':
            if 'band_id' not in session:
                return redirect(url_for('select_band'))
            band_id = session['band_id']
            mymem = _current_membership(band_id, current_user.id)
            if not mymem or mymem.role not in ('creator','admin'):
                return render_template('select_band.html', error='دسترسی دعوت نداری.', memberships=_user_memberships(current_user.id))
            uname = (request.form.get('username') or '').strip()
            if not uname:
                return render_template('select_band.html', error='نام کاربری خالی است.', memberships=_user_memberships(current_user.id))
            user = User.query.filter(User.username.ilike(uname)).first()
            if not user:
                return render_template('select_band.html', error='کاربری با این نام پیدا نشد.', memberships=_user_memberships(current_user.id))
            if _current_membership(band_id, user.id):
                return render_template('select_band.html', ok=f'کاربر «{user.username}» قبلاً عضو بوده.', memberships=_user_memberships(current_user.id))
            db.session.add(BandMembership(band_id=band_id, user_id=user.id, role='member'))
            db.session.commit()
            return render_template('select_band.html', ok=f'کاربر «{user.username}» به بند اضافه شد.', memberships=_user_memberships(current_user.id))

    return render_template('select_band.html', memberships=_user_memberships(current_user.id))

@app.post('/band/switch')
@login_required
def band_switch():
    band_id = int(request.form.get('band_id'))
    m = _current_membership(band_id, current_user.id)
    if m:
        session['band_id'] = band_id
    return redirect(url_for('dashboard'))

# ---------- Tracks ----------
@app.route('/')
@login_required
def dashboard():
    if 'band_id' not in session:
        return redirect(url_for('select_band'))
    band_id = session['band_id']
    tracks = (db.session.query(Track)
              .join(ProjectTrack, ProjectTrack.track_id == Track.id)
              .join(Project, Project.id == ProjectTrack.project_id)
              .filter(Project.band_id == band_id)
              .order_by(Track.created_at.desc())
              .all())
    return render_template('dashboard.html', tracks=tracks)

@app.route('/track/new', methods=['POST'])
@login_required
def create_track():
    if 'band_id' not in session:
        return redirect(url_for('select_band'))
    band_id = session['band_id']
    title = request.form.get('title') or 'Untitled'
    t = Track(title=title)
    db.session.add(t); db.session.commit()
    proj = Project.query.filter_by(band_id=band_id, name='Default').first()
    if not proj:
        proj = Project(band_id=band_id, name='Default'); db.session.add(proj); db.session.commit()
    if not ProjectTrack.query.filter_by(project_id=proj.id, track_id=t.id).first():
        db.session.add(ProjectTrack(project_id=proj.id, track_id=t.id)); db.session.commit()
    if not Lyrics.query.filter_by(track_id=t.id).first():
        db.session.add(Lyrics(track_id=t.id, version=1, created_by=current_user.id)); db.session.commit()
    return redirect(url_for('dashboard'))

# ---------- Track room & lyrics ----------
@app.route('/track/<int:track_id>')
@login_required
def track_room(track_id):
    if 'band_id' not in session:
        return redirect(url_for('select_band'))
    band_id = session['band_id']
    allowed = (db.session.query(ProjectTrack)
               .join(Project, Project.id == ProjectTrack.project_id)
               .filter(ProjectTrack.track_id == track_id, Project.band_id == band_id).first())
    if not allowed:
        return "Access denied for this band.", 403
    t = Track.query.get_or_404(track_id)
    lyrics = Lyrics.query.filter_by(track_id=track_id).order_by(Lyrics.version.desc()).first()
    lines = LyricsLine.query.filter_by(lyrics_id=lyrics.id).order_by(LyricsLine.line_number).all() if lyrics else []
    return render_template('track_room.html', track=t, lyrics=lyrics, lines=lines)

@app.post('/track/<int:track_id>/save_times')
@login_required
def save_times(track_id):
    payload = request.get_json() or []
    lyrics = Lyrics.query.filter_by(track_id=track_id).order_by(Lyrics.version.desc()).first()
    if not lyrics:
        lyrics = Lyrics(track_id=track_id, version=1, created_by=current_user.id); db.session.add(lyrics); db.session.commit()
    maxnum = LyricsLine.query.filter_by(lyrics_id=lyrics.id).count()
    for item in payload:
        lid = item.get('id'); beat = item.get('beat'); text = item.get('text','')
        if lid:
            line = LyricsLine.query.get(int(lid))
            if line:
                line.beat = float(beat) if beat is not None else None
                line.text = text
        else:
            maxnum += 1
            db.session.add(LyricsLine(lyrics_id=lyrics.id, line_number=maxnum, text=text, beat=float(beat) if beat else None))
    db.session.commit()
    return jsonify({'ok': True})

@app.post('/api/beat_to_time')
@login_required
def beat_to_time_api():
    data = request.get_json() or {}
    beat = float(data.get('beat', 0)); bpm = float(data.get('bpm', 84.0))
    sec = (beat / bpm) * 60.0
    mm = int(sec // 60); ss = int(sec % 60); cs = int((sec - int(sec)) * 100)
    return jsonify({'seconds': sec, 'mmss': f"{mm:02d}:{ss:02d}.{cs:02d}"})

@app.get('/track/<int:track_id>/export_lrc')
@login_required
def export_lrc(track_id):
    t = Track.query.get_or_404(track_id)
    lyrics = Lyrics.query.filter_by(track_id=track_id).order_by(Lyrics.version.desc()).first()
    lines = LyricsLine.query.filter_by(lyrics_id=lyrics.id).order_by(LyricsLine.line_number).all()
    out = [f"[ti:{t.title}]"]
    for ln in lines:
        if ln.beat is None: continue
        seconds = (ln.beat / t.bpm) * 60.0
        mm = int(seconds // 60); ss = int(seconds % 60); cs = int((seconds - int(seconds)) * 100)
        out.append(f"[{mm:02d}:{ss:02d}.{cs:02d}] {ln.text}")
    return ("\n".join(out), 200, {'Content-Type': 'text/plain; charset=utf-8'})

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=5050)
