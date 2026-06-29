from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student')  # student, teacher, admin
    bio = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(256), nullable=True)
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=True)
    filiere = db.Column(db.String(100), nullable=True)
    niveau = db.Column(db.String(10), nullable=True)  # L1, L2, L3, M1, M2
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    documents = db.relationship('Document', backref='author', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'