from app import db
from datetime import datetime

class University(db.Model):
    __tablename__ = 'universities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='university', lazy=True)
    filieres = db.relationship('Filiere', backref='university', lazy=True)

    def __repr__(self):
        return f'<University {self.name}>'


class Filiere(db.Model):
    __tablename__ = 'filieres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    university_id = db.Column(db.Integer, db.ForeignKey('universities.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    matieres = db.relationship('Matiere', backref='filiere', lazy=True)


class Matiere(db.Model):
    __tablename__ = 'matieres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    filiere_id = db.Column(db.Integer, db.ForeignKey('filieres.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    documents = db.relationship('Document', backref='matiere', lazy=True)