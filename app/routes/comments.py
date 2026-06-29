from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import User, Document

comments_bp = Blueprint('comments', __name__)

# ─── MODÈLE COMMENTAIRE ────────────────────────────────────
class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)  # 1-5 étoiles
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='comments')
    document = db.relationship(
        'Document',
        backref=db.backref('comments', cascade='all, delete-orphan')
    )


# ─── AJOUTER UN COMMENTAIRE ────────────────────────────────
@comments_bp.route('/api/documents/<int:doc_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(doc_id):
    user_id = int(get_jwt_identity())
    Document.query.get_or_404(doc_id)
    data = request.get_json()

    if not data.get('content'):
        return jsonify({'error': 'Contenu requis'}), 400

    rating = data.get('rating')
    if rating and (int(rating) < 1 or int(rating) > 5):
        return jsonify({'error': 'La note doit être entre 1 et 5'}), 400

    comment = Comment(
        content=data['content'],
        rating=int(rating) if rating else None,
        user_id=user_id,
        document_id=doc_id
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({
        'message': 'Commentaire ajouté avec succès !',
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'rating': comment.rating,
            'user': comment.user.username,
            'created_at': comment.created_at.isoformat()
        }
    }), 201


# ─── LISTE DES COMMENTAIRES D'UN DOCUMENT ──────────────────
@comments_bp.route('/api/documents/<int:doc_id>/comments', methods=['GET'])
@jwt_required()
def get_comments(doc_id):
    Document.query.get_or_404(doc_id)
    comments = Comment.query.filter_by(document_id=doc_id)\
                            .order_by(Comment.created_at.desc()).all()

    # Calcul de la note moyenne
    ratings = [c.rating for c in comments if c.rating]
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

    return jsonify({
        'comments': [{
            'id': c.id,
            'content': c.content,
            'rating': c.rating,
            'user': c.user.username,
            'created_at': c.created_at.isoformat()
        } for c in comments],
        'total': len(comments),
        'avg_rating': avg_rating
    }), 200


# ─── SUPPRIMER UN COMMENTAIRE ──────────────────────────────
@comments_bp.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    user_id = int(get_jwt_identity())
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != user_id:
        return jsonify({'error': 'Non autorisé'}), 403

    db.session.delete(comment)
    db.session.commit()

    return jsonify({'message': 'Commentaire supprimé avec succès !'}), 200