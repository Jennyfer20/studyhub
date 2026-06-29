from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from app import db
from app.models import User, Document, University

profile_bp = Blueprint('profile', __name__)

# ─── VOIR SON PROPRE PROFIL ────────────────────────────────
@profile_bp.route('/api/profile', methods=['GET'])
@jwt_required()
def get_my_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    profile = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'bio': user.bio,
        'photo_url': user.photo_url,
        'filiere': user.filiere,
        'niveau': user.niveau,
        'university': user.university.name if user.university else None,
        'created_at': user.created_at.isoformat(),
        'documents_count': len(user.documents)
    }

    # Infos supplémentaires selon le rôle
    if user.role == 'student':
        profile['documents'] = [{
            'id': doc.id,
            'title': doc.title,
            'category': doc.category,
            'niveau': doc.niveau,
            'created_at': doc.created_at.isoformat()
        } for doc in user.documents[:5]]

    elif user.role == 'teacher':
        profile['matieres_enseignees'] = user.filiere
        profile['documents'] = [{
            'id': doc.id,
            'title': doc.title,
            'category': doc.category,
            'created_at': doc.created_at.isoformat()
        } for doc in user.documents[:5]]

    elif user.role == 'admin':
        profile['university_managed'] = user.university.name if user.university else None

    return jsonify(profile), 200


# ─── VOIR LE PROFIL D'UN AUTRE UTILISATEUR ─────────────────
@profile_bp.route('/api/profile/<int:user_id>', methods=['GET'])
@jwt_required()
def get_profile(user_id):
    user = User.query.get_or_404(user_id)

    profile = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'bio': user.bio,
        'photo_url': user.photo_url,
        'filiere': user.filiere,
        'niveau': user.niveau,
        'university': user.university.name if user.university else None,
        'documents_count': len(user.documents),
        'created_at': user.created_at.isoformat()
    }

    return jsonify(profile), 200


# ─── METTRE À JOUR SON PROFIL ──────────────────────────────
@profile_bp.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    # Champs communs à tous les rôles
    if 'bio' in data:
        user.bio = data['bio']
    if 'filiere' in data:
        user.filiere = data['filiere']
    if 'niveau' in data and user.role == 'student':
        user.niveau = data['niveau']
    if 'university_id' in data:
        university = University.query.get(data['university_id'])
        if university:
            user.university_id = data['university_id']

    db.session.commit()

    return jsonify({
        'message': 'Profil mis à jour avec succès !',
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'bio': user.bio,
            'filiere': user.filiere,
            'niveau': user.niveau
        }
    }), 200


# ─── UPLOAD PHOTO DE PROFIL ────────────────────────────────
@profile_bp.route('/api/profile/photo', methods=['POST'])
@jwt_required()
def upload_photo():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    if 'photo' not in request.files:
        return jsonify({'error': 'Aucune photo envoyée'}), 400

    photo = request.files['photo']
    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    if not ('.' in photo.filename and
            photo.filename.rsplit('.', 1)[1].lower() in allowed):
        return jsonify({'error': 'Format non autorisé'}), 400

    filename = secure_filename(f"avatar_{user_id}_{photo.filename}")
    upload_folder = 'app/static/uploads/avatars'
    os.makedirs(upload_folder, exist_ok=True)

    photo_path = os.path.join(upload_folder, filename)
    photo.save(photo_path)

    user.photo_url = f'/static/uploads/avatars/{filename}'
    db.session.commit()

    return jsonify({
        'message': 'Photo de profil mise à jour !',
        'photo_url': user.photo_url
    }), 200


# ─── LISTE DES UTILISATEURS (admin seulement) ──────────────
@profile_bp.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    user_id = int(get_jwt_identity())
    current_user = User.query.get_or_404(user_id)

    if current_user.role != 'admin':
        return jsonify({'error': 'Accès réservé aux admins'}), 403

    role_filter = request.args.get('role')
    query = User.query

    if role_filter:
        query = query.filter_by(role=role_filter)

    users = query.all()

    return jsonify({
        'users': [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'filiere': u.filiere,
            'niveau': u.niveau,
            'university': u.university.name if u.university else None,
            'created_at': u.created_at.isoformat()
        } for u in users]
    }), 200


# ─── CHANGER LE RÔLE D'UN UTILISATEUR (admin seulement) ────
@profile_bp.route('/api/users/<int:target_id>/role', methods=['PUT'])
@jwt_required()
def change_role(target_id):
    user_id = int(get_jwt_identity())
    current_user = User.query.get_or_404(user_id)

    if current_user.role != 'admin':
        return jsonify({'error': 'Accès réservé aux admins'}), 403

    target_user = User.query.get_or_404(target_id)
    data = request.get_json()

    if data.get('role') not in ['student', 'teacher', 'admin']:
        return jsonify({'error': 'Rôle invalide'}), 400

    target_user.role = data['role']
    db.session.commit()

    return jsonify({
        'message': f'Rôle mis à jour : {target_user.username} est maintenant {target_user.role}',
    }), 200