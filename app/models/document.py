from app import db
from datetime import datetime

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(256), nullable=False)
    file_type = db.Column(db.String(10), nullable=True)  # pdf, docx, image
    category = db.Column(db.String(50), nullable=True)   # cours, TD, examen, résumé
    niveau = db.Column(db.String(10), nullable=True)     # L1, L2, L3, M1, M2
    is_global = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    matiere_id = db.Column(db.Integer, db.ForeignKey('matieres.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Document {self.title}>'