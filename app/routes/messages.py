from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import User

messages_bp = Blueprint('messages', __name__)

# ─── MODÈLE MESSAGE ────────────────────────────────────────
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    group_id = db.Column(db.Integer, nullable=True)  # pour les messages de groupe
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')


# ─── ENVOYER UN MESSAGE PRIVÉ ──────────────────────────────
@messages_bp.route('/api/messages', methods=['POST'])
@jwt_required()
def send_message():
    sender_id = int(get_jwt_identity())
    data = request.get_json()

    if not data.get('content'):
        return jsonify({'error': 'Contenu requis'}), 400

    if not data.get('receiver_id') and not data.get('group_id'):
        return jsonify({'error': 'Destinataire ou groupe requis'}), 400

    # Vérifie que le destinataire existe
    if data.get('receiver_id'):
        User.query.get_or_404(data['receiver_id'])

    message = Message(
        content=data['content'],
        sender_id=sender_id,
        receiver_id=data.get('receiver_id'),
        group_id=data.get('group_id')
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({
        'message': 'Message envoyé !',
        'data': {
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'created_at': message.created_at.isoformat()
        }
    }), 201


# ─── CONVERSATION ENTRE DEUX UTILISATEURS ──────────────────
@messages_bp.route('/api/messages/<int:user_id>', methods=['GET'])
@jwt_required()
def get_conversation(user_id):
    current_id = int(get_jwt_identity())

    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_id, Message.receiver_id == user_id),
            db.and_(Message.sender_id == user_id, Message.receiver_id == current_id)
        )
    ).order_by(Message.created_at.asc()).all()

    # Marque les messages comme lus
    for msg in messages:
        if msg.receiver_id == current_id and not msg.is_read:
            msg.is_read = True
    db.session.commit()

    return jsonify({
        'messages': [{
            'id': m.id,
            'content': m.content,
            'sender': m.sender.username,
            'is_mine': m.sender_id == current_id,
            'is_read': m.is_read,
            'created_at': m.created_at.isoformat()
        } for m in messages]
    }), 200


# ─── MESSAGES D'UN GROUPE ──────────────────────────────────
@messages_bp.route('/api/groups/<int:group_id>/messages', methods=['GET'])
@jwt_required()
def get_group_messages(group_id):
    current_id = int(get_jwt_identity())

    messages = Message.query.filter_by(group_id=group_id)\
                            .order_by(Message.created_at.asc()).all()

    return jsonify({
        'messages': [{
            'id': m.id,
            'content': m.content,
            'sender': m.sender.username,
            'is_mine': m.sender_id == current_id,
            'created_at': m.created_at.isoformat()
        } for m in messages]
    }), 200


# ─── ENVOYER UN MESSAGE DANS UN GROUPE ─────────────────────
@messages_bp.route('/api/groups/<int:group_id>/messages', methods=['POST'])
@jwt_required()
def send_group_message(group_id):
    sender_id = int(get_jwt_identity())
    data = request.get_json()

    if not data.get('content'):
        return jsonify({'error': 'Contenu requis'}), 400

    message = Message(
        content=data['content'],
        sender_id=sender_id,
        group_id=group_id
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({
        'message': 'Message envoyé dans le groupe !',
        'data': {
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'created_at': message.created_at.isoformat()
        }
    }), 201


# ─── LISTE DES CONVERSATIONS ───────────────────────────────
@messages_bp.route('/api/messages', methods=['GET'])
@jwt_required()
def get_conversations():
    current_id = int(get_jwt_identity())

    # Récupère tous les utilisateurs avec qui on a échangé
    sent = db.session.query(Message.receiver_id).filter_by(sender_id=current_id)\
                     .filter(Message.receiver_id.isnot(None)).distinct()
    received = db.session.query(Message.sender_id).filter_by(receiver_id=current_id).distinct()

    user_ids = set([r[0] for r in sent] + [r[0] for r in received])

    conversations = []
    for uid in user_ids:
        user = User.query.get(uid)
        last_msg = Message.query.filter(
            db.or_(
                db.and_(Message.sender_id == current_id, Message.receiver_id == uid),
                db.and_(Message.sender_id == uid, Message.receiver_id == current_id)
            )
        ).order_by(Message.created_at.desc()).first()

        unread = Message.query.filter_by(
            sender_id=uid,
            receiver_id=current_id,
            is_read=False
        ).count()

        conversations.append({
            'user': {'id': user.id, 'username': user.username},
            'last_message': last_msg.content[:50] if last_msg else None,
            'unread_count': unread,
            'updated_at': last_msg.created_at.isoformat() if last_msg else None
        })

    conversations.sort(key=lambda x: x['updated_at'] or '', reverse=True)

    return jsonify({'conversations': conversations}), 200


# ─── MESSAGES NON LUS ──────────────────────────────────────
@messages_bp.route('/api/messages/unread', methods=['GET'])
@jwt_required()
def get_unread():
    current_id = int(get_jwt_identity())
    count = Message.query.filter_by(receiver_id=current_id, is_read=False).count()
    return jsonify({'unread_count': count}), 200