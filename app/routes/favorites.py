from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import User, Document

favorites_bp = Blueprint('favorites', __name__)

# ─── MODÈLE FAVORI ─────────────────────────────────────────
class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='favorites')
    document = db.relationship(
        'Document',
        backref=db.backref('favorited_by', cascade='all, delete-orphan')
    )

    __table_args__ = (
        db.UniqueConstraint('user_id', 'document_id', name='unique_favorite'),
    )


# ─── AJOUTER AUX FAVORIS ───────────────────────────────────
@favorites_bp.route('/api/documents/<int:doc_id>/favorite', methods=['POST'])
@jwt_required()
def add_favorite(doc_id):
    user_id = int(get_jwt_identity())
    Document.query.get_or_404(doc_id)

    # Vérifie si déjà en favori
    existing = Favorite.query.filter_by(
        user_id=user_id,
        document_id=doc_id
    ).first()

    if existing:
        return jsonify({'error': 'Document déjà en favori'}), 409

    favorite = Favorite(user_id=user_id, document_id=doc_id)
    db.session.add(favorite)
    db.session.commit()

    return jsonify({
        'message': 'Document ajouté aux favoris !',
        'favorite_id': favorite.id
    }), 201


# ─── RETIRER DES FAVORIS ───────────────────────────────────
@favorites_bp.route('/api/documents/<int:doc_id>/favorite', methods=['DELETE'])
@jwt_required()
def remove_favorite(doc_id):
    user_id = int(get_jwt_identity())

    favorite = Favorite.query.filter_by(
        user_id=user_id,
        document_id=doc_id
    ).first()

    if not favorite:
        return jsonify({'error': 'Document non trouvé dans les favoris'}), 404

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({'message': 'Document retiré des favoris !'}), 200


# ─── LISTE DES FAVORIS ─────────────────────────────────────
@favorites_bp.route('/api/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    user_id = int(get_jwt_identity())
    favorites = Favorite.query.filter_by(user_id=user_id)\
                              .order_by(Favorite.created_at.desc()).all()

    return jsonify({
        'favorites': [{
            'id': f.id,
            'document': {
                'id': f.document.id,
                'title': f.document.title,
                'category': f.document.category,
                'niveau': f.document.niveau,
                'file_type': f.document.file_type,
                'author': f.document.author.username,
                'created_at': f.document.created_at.isoformat()
            },
            'added_at': f.created_at.isoformat()
        } for f in favorites],
        'total': len(favorites)
    }), 200


# ─── VÉRIFIER SI UN DOCUMENT EST EN FAVORI ─────────────────
@favorites_bp.route('/api/documents/<int:doc_id>/favorite', methods=['GET'])
@jwt_required()
def check_favorite(doc_id):
    user_id = int(get_jwt_identity())

    favorite = Favorite.query.filter_by(
        user_id=user_id,
        document_id=doc_id
    ).first()

    return jsonify({
        'is_favorite': favorite is not None
    }), 200