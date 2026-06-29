from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, University, Filiere, Matiere

university_bp = Blueprint('university', __name__)


# ─── LISTE DES UNIVERSITÉS ─────────────────────────────────
@university_bp.route('/api/universities', methods=['GET'])
@jwt_required()
def get_universities():
    universities = University.query.all()

    return jsonify({
        'universities': [{
            'id': u.id,
            'name': u.name,
            'country': u.country,
            'city': u.city
        } for u in universities]
    }), 200


# ─── CRÉER UNE UNIVERSITÉ (admin) ──────────────────────────
@university_bp.route('/api/universities', methods=['POST'])
@jwt_required()
def create_university():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user.role != 'admin':
        return jsonify({'error': 'Accès réservé aux admins'}), 403

    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Nom requis'}), 400

    if University.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Université déjà existante'}), 409

    university = University(
        name=data['name'],
        country=data.get('country'),
        city=data.get('city')
    )

    db.session.add(university)
    db.session.commit()

    return jsonify({
        'message': 'Université créée avec succès !',
        'university': {
            'id': university.id,
            'name': university.name,
            'country': university.country,
            'city': university.city
        }
    }), 201


# ─── LISTE DES FILIÈRES D'UNE UNIVERSITÉ ───────────────────
@university_bp.route('/api/universities/<int:uni_id>/filieres', methods=['GET'])
@jwt_required()
def get_filieres(uni_id):
    university = University.query.get_or_404(uni_id)
    filieres = Filiere.query.filter_by(university_id=uni_id).all()

    return jsonify({
        'university': university.name,
        'filieres': [{
            'id': f.id,
            'name': f.name
        } for f in filieres]
    }), 200


# ─── CRÉER UNE FILIÈRE ─────────────────────────────────────
@university_bp.route('/api/universities/<int:uni_id>/filieres', methods=['POST'])
@jwt_required()
def create_filiere(uni_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Accès réservé aux admins et enseignants'}), 403

    University.query.get_or_404(uni_id)
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Nom requis'}), 400

    filiere = Filiere(
        name=data['name'],
        university_id=uni_id
    )

    db.session.add(filiere)
    db.session.commit()

    return jsonify({
        'message': 'Filière créée avec succès !',
        'filiere': {
            'id': filiere.id,
            'name': filiere.name
        }
    }), 201


# ─── LISTE DES MATIÈRES D'UNE FILIÈRE ─────────────────────
@university_bp.route('/api/filieres/<int:filiere_id>/matieres', methods=['GET'])
@jwt_required()
def get_matieres(filiere_id):
    filiere = Filiere.query.get_or_404(filiere_id)
    matieres = Matiere.query.filter_by(filiere_id=filiere_id).all()

    return jsonify({
        'filiere': filiere.name,
        'matieres': [{
            'id': m.id,
            'name': m.name
        } for m in matieres]
    }), 200


# ─── CRÉER UNE MATIÈRE ─────────────────────────────────────
@university_bp.route('/api/filieres/<int:filiere_id>/matieres', methods=['POST'])
@jwt_required()
def create_matiere(filiere_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Accès réservé aux admins et enseignants'}), 403

    Filiere.query.get_or_404(filiere_id)
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Nom requis'}), 400

    matiere = Matiere(
        name=data['name'],
        filiere_id=filiere_id
    )

    db.session.add(matiere)
    db.session.commit()

    return jsonify({
        'message': 'Matière créée avec succès !',
        'matiere': {
            'id': matiere.id,
            'name': matiere.name
        }
    }), 201