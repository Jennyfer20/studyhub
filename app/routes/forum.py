from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import User, Matiere

forum_bp = Blueprint('forum', __name__)

# ─── MODÈLES ───────────────────────────────────────────────
class ForumPost(db.Model):
    __tablename__ = 'forum_posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    matiere_id = db.Column(db.Integer, db.ForeignKey('matieres.id'), nullable=True)
    is_resolved = db.Column(db.Boolean, default=False)
    votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='posts')
    matiere = db.relationship('Matiere', backref='posts')
    replies = db.relationship('ForumReply', backref='post', lazy=True, cascade='all, delete-orphan')


class ForumReply(db.Model):
    __tablename__ = 'forum_replies'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    is_validated = db.Column(db.Boolean, default=False)
    votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='replies')


# ─── CRÉER UN POST ─────────────────────────────────────────
@forum_bp.route('/api/forum/posts', methods=['POST'])
@jwt_required()
def create_post():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Titre et contenu requis'}), 400

    post = ForumPost(
        title=data['title'],
        content=data['content'],
        user_id=user_id,
        matiere_id=data.get('matiere_id')
    )

    db.session.add(post)
    db.session.commit()

    return jsonify({
        'message': 'Post créé avec succès !',
        'post': {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'user': post.user.username,
            'created_at': post.created_at.isoformat()
        }
    }), 201


# ─── LISTE DES POSTS ───────────────────────────────────────
@forum_bp.route('/api/forum/posts', methods=['GET'])
@jwt_required()
def get_posts():
    matiere_id = request.args.get('matiere_id')
    keyword = request.args.get('q')
    is_resolved = request.args.get('resolved')

    query = ForumPost.query

    if matiere_id:
        query = query.filter_by(matiere_id=matiere_id)
    if keyword:
        query = query.filter(ForumPost.title.ilike(f'%{keyword}%'))
    if is_resolved is not None:
        query = query.filter_by(is_resolved=is_resolved == 'true')

    posts = query.order_by(ForumPost.created_at.desc()).all()

    return jsonify({
        'posts': [{
            'id': p.id,
            'title': p.title,
            'content': p.content[:150] + '...' if len(p.content) > 150 else p.content,
            'user': p.user.username,
            'matiere': p.matiere.name if p.matiere else None,
            'is_resolved': p.is_resolved,
            'votes': p.votes,
            'replies_count': len(p.replies),
            'created_at': p.created_at.isoformat()
        } for p in posts],
        'total': len(posts)
    }), 200


# ─── DÉTAIL D'UN POST ──────────────────────────────────────
@forum_bp.route('/api/forum/posts/<int:post_id>', methods=['GET'])
@jwt_required()
def get_post(post_id):
    post = ForumPost.query.get_or_404(post_id)

    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'user': post.user.username,
        'matiere': post.matiere.name if post.matiere else None,
        'is_resolved': post.is_resolved,
        'votes': post.votes,
        'replies': [{
            'id': r.id,
            'content': r.content,
            'user': r.user.username,
            'is_validated': r.is_validated,
            'votes': r.votes,
            'created_at': r.created_at.isoformat()
        } for r in post.replies],
        'created_at': post.created_at.isoformat()
    }), 200


# ─── VOTER POUR UN POST ────────────────────────────────────
@forum_bp.route('/api/forum/posts/<int:post_id>/vote', methods=['POST'])
@jwt_required()
def vote_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    data = request.get_json()
    vote = data.get('vote', 1)  # 1 ou -1

    post.votes += vote
    db.session.commit()

    return jsonify({'votes': post.votes}), 200


# ─── AJOUTER UNE RÉPONSE ───────────────────────────────────
@forum_bp.route('/api/forum/posts/<int:post_id>/replies', methods=['POST'])
@jwt_required()
def add_reply(post_id):
    user_id = int(get_jwt_identity())
    ForumPost.query.get_or_404(post_id)
    data = request.get_json()

    if not data.get('content'):
        return jsonify({'error': 'Contenu requis'}), 400

    reply = ForumReply(
        content=data['content'],
        user_id=user_id,
        post_id=post_id
    )

    db.session.add(reply)
    db.session.commit()

    return jsonify({
        'message': 'Réponse ajoutée avec succès !',
        'reply': {
            'id': reply.id,
            'content': reply.content,
            'user': reply.user.username,
            'created_at': reply.created_at.isoformat()
        }
    }), 201


# ─── VALIDER UNE RÉPONSE ───────────────────────────────────
@forum_bp.route('/api/forum/replies/<int:reply_id>/validate', methods=['PUT'])
@jwt_required()
def validate_reply(reply_id):
    user_id = int(get_jwt_identity())
    reply = ForumReply.query.get_or_404(reply_id)
    post = ForumPost.query.get(reply.post_id)

    if post.user_id != user_id:
        return jsonify({'error': 'Seul l\'auteur du post peut valider une réponse'}), 403

    reply.is_validated = True
    post.is_resolved = True
    db.session.commit()

    return jsonify({'message': 'Réponse validée ! Post marqué comme résolu.'}), 200


# ─── SUPPRIMER UN POST ─────────────────────────────────────
@forum_bp.route('/api/forum/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    user_id = int(get_jwt_identity())
    post = ForumPost.query.get_or_404(post_id)

    if post.user_id != user_id:
        return jsonify({'error': 'Non autorisé'}), 403

    db.session.delete(post)
    db.session.commit()

    return jsonify({'message': 'Post supprimé avec succès !'}), 200