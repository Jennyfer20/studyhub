from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import User

groups_bp = Blueprint('groups', __name__)

# ─── MODÈLES ───────────────────────────────────────────────
class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(20), default='matiere')  # matiere, filiere, projet
    is_global = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='created_groups')
    members = db.relationship('GroupMember', backref='group', lazy=True, cascade='all, delete-orphan')


class GroupMember(db.Model):
    __tablename__ = 'group_members'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # member, admin
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='group_memberships')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'group_id', name='unique_member'),
    )


# ─── CRÉER UN GROUPE ───────────────────────────────────────
@groups_bp.route('/api/groups', methods=['POST'])
@jwt_required()
def create_group():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Nom du groupe requis'}), 400

    group = Group(
        name=data['name'],
        description=data.get('description'),
        type=data.get('type', 'matiere'),
        is_global=data.get('is_global', False),
        created_by=user_id
    )

    db.session.add(group)
    db.session.flush()

    # Créateur devient admin du groupe
    member = GroupMember(
        user_id=user_id,
        group_id=group.id,
        role='admin'
    )

    db.session.add(member)
    db.session.commit()

    return jsonify({
        'message': 'Groupe créé avec succès !',
        'group': {
            'id': group.id,
            'name': group.name,
            'description': group.description,
            'type': group.type,
            'is_global': group.is_global,
            'created_by': group.creator.username
        }
    }), 201


# ─── LISTE DES GROUPES ─────────────────────────────────────
@groups_bp.route('/api/groups', methods=['GET'])
@jwt_required()
def get_groups():
    type_filter = request.args.get('type')
    is_global = request.args.get('global')
    keyword = request.args.get('q')

    query = Group.query

    if type_filter:
        query = query.filter_by(type=type_filter)
    if is_global is not None:
        query = query.filter_by(is_global=is_global == 'true')
    if keyword:
        query = query.filter(Group.name.ilike(f'%{keyword}%'))

    groups = query.order_by(Group.created_at.desc()).all()

    return jsonify({
        'groups': [{
            'id': g.id,
            'name': g.name,
            'description': g.description,
            'type': g.type,
            'is_global': g.is_global,
            'members_count': len(g.members),
            'created_by': g.creator.username,
            'created_at': g.created_at.isoformat()
        } for g in groups],
        'total': len(groups)
    }), 200


# ─── REJOINDRE UN GROUPE ───────────────────────────────────
@groups_bp.route('/api/groups/<int:group_id>/join', methods=['POST'])
@jwt_required()
def join_group(group_id):
    user_id = int(get_jwt_identity())
    group = Group.query.get_or_404(group_id)

    existing = GroupMember.query.filter_by(
        user_id=user_id,
        group_id=group_id
    ).first()

    if existing:
        return jsonify({'error': 'Tu es déjà membre de ce groupe'}), 409

    member = GroupMember(user_id=user_id, group_id=group_id)
    db.session.add(member)
    db.session.commit()

    return jsonify({
        'message': f'Tu as rejoint le groupe {group.name} !'
    }), 201


# ─── QUITTER UN GROUPE ─────────────────────────────────────
@groups_bp.route('/api/groups/<int:group_id>/leave', methods=['DELETE'])
@jwt_required()
def leave_group(group_id):
    user_id = int(get_jwt_identity())

    member = GroupMember.query.filter_by(
        user_id=user_id,
        group_id=group_id
    ).first()

    if not member:
        return jsonify({'error': 'Tu n\'es pas membre de ce groupe'}), 404

    db.session.delete(member)
    db.session.commit()

    return jsonify({'message': 'Tu as quitté le groupe !'}), 200


# ─── MEMBRES D'UN GROUPE ───────────────────────────────────
@groups_bp.route('/api/groups/<int:group_id>/members', methods=['GET'])
@jwt_required()
def get_members(group_id):
    Group.query.get_or_404(group_id)
    members = GroupMember.query.filter_by(group_id=group_id).all()

    return jsonify({
        'members': [{
            'id': m.user.id,
            'username': m.user.username,
            'role': m.role,
            'filiere': m.user.filiere,
            'niveau': m.user.niveau,
            'joined_at': m.joined_at.isoformat()
        } for m in members],
        'total': len(members)
    }), 200


# ─── MES GROUPES ───────────────────────────────────────────
@groups_bp.route('/api/groups/mine', methods=['GET'])
@jwt_required()
def get_my_groups():
    user_id = int(get_jwt_identity())
    memberships = GroupMember.query.filter_by(user_id=user_id).all()

    return jsonify({
        'groups': [{
            'id': m.group.id,
            'name': m.group.name,
            'description': m.group.description,
            'type': m.group.type,
            'role': m.role,
            'members_count': len(m.group.members),
            'joined_at': m.joined_at.isoformat()
        } for m in memberships],
        'total': len(memberships)
    }), 200


# ─── SUPPRIMER UN GROUPE ───────────────────────────────────
@groups_bp.route('/api/groups/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    user_id = int(get_jwt_identity())
    group = Group.query.get_or_404(group_id)

    if group.created_by != user_id:
        return jsonify({'error': 'Non autorisé'}), 403

    db.session.delete(group)
    db.session.commit()

    return jsonify({'message': 'Groupe supprimé avec succès !'}), 200