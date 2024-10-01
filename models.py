from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile = db.relationship('Profile', backref='user', uselist=False)

    # Relationships for followers and following
    followers = db.relationship(
        'Follow',
        foreign_keys='Follow.followed_id',
        backref='followed',
        lazy='dynamic'
    )
    followed = db.relationship(
        'Follow',
        foreign_keys='Follow.follower_id',
        backref='follower',
        lazy='dynamic'
    )

    def follow(self, user):
        """Follow another user."""
        if not self.is_following(user):
            follow = Follow(follower_id=self.id, followed_id=user.id)
            db.session.add(follow)
            db.session.commit()

    def unfollow(self, user):
        """Unfollow another user."""
        follow = Follow.query.filter_by(
            follower_id=self.id,
            followed_id=user.id
        ).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def is_following(self, user):
        # Check if the current user is following the given user.
        return Follow.query.filter_by(
            follower_id=self.id,
            followed_id=user.id
        ).first() is not None

    def is_followed_by(self, user):
        # Check if the current user is followed by the given user.
        return Follow.query.filter_by(
            follower_id=user.id,
            followed_id=self.id
        ).first() is not None

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Follow {self.follower_id} -> {self.followed_id}>'

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(150), nullable=True)
