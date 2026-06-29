from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

# ─── INSCRIPTION ───────────────────────────────────────────
@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    # Vérifications
    if not data.get('email') or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Email, username et password sont requis'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email déjà utilisé'}), 409

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username déjà utilisé'}), 409

    # Création de l'utilisateur
    user = User(
        email=data['email'],
        username=data['username'],
        password_hash=generate_password_hash(data['password']),
        role=data.get('role', 'student'),
        filiere=data.get('filiere'),
        niveau=data.get('niveau'),
        university_id=data.get('university_id')
    )

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'Inscription réussie !',
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'role': user.role
        }
    }), 201


# ─── CONNEXION ─────────────────────────────────────────────
@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email et password sont requis'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Email ou mot de passe incorrect'}), 401

    token = create_access_token(identity=str(user.id))

    return jsonify({
    'message': 'Connexion réussie !',
    'token': token,
    'user': {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'role': user.role
    }
}), 200


# ─── PROFIL CONNECTÉ ───────────────────────────────────────
@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'Utilisateur introuvable'}), 404

    return jsonify({
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'role': user.role,
        'filiere': user.filiere,
        'niveau': user.niveau,
        'bio': user.bio,
        'created_at': user.created_at.isoformat()
    }), 200


# ─── CHANGEMENT DE MOT DE PASSE ────────────────────────────
@auth_bp.route('/api/auth/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()

    if not check_password_hash(user.password_hash, data.get('old_password', '')):
        return jsonify({'error': 'Ancien mot de passe incorrect'}), 401

    user.password_hash = generate_password_hash(data['new_password'])
    db.session.commit()

    return jsonify({'message': 'Mot de passe mis à jour avec succès !'}), 200