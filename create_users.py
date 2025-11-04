from app import app, db, User
with app.app_context():
    users = [
        ('parsa','Parsa','parsa123'),
        ('erfan','Erfan','erfan123'),
        ('you','You','you123'),
    ]
    for u in users:
        if not User.query.filter_by(username=u[0]).first():
            db.session.add(User(username=u[0], display_name=u[1], password=u[2]))
    db.session.commit()
    print("Users created (parsa/erfan/you).")
