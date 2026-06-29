from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
from app import db
from app.models import Document, User

documents_bp = Blueprint('documents', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── UPLOAD DOCUMENT ───────────────────────────────────────
@documents_bp.route('/api/documents/upload', methods=['POST'])
@jwt_required()
def upload_document():
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier envoyé'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Fichier vide'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Type de fichier non autorisé'}), 400

    # Sauvegarde du fichier sous un nom unique (anti-collision)
    original = secure_filename(file.filename)
    ext = original.rsplit('.', 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}_{original}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, stored_name))

    # Création en base — on ne stocke que le nom de fichier
    document = Document(
        title=request.form.get('title', original),
        description=request.form.get('description'),
        file_url=stored_name,
        file_type=ext,
        category=request.form.get('category'),
        niveau=request.form.get('niveau'),
        is_global=request.form.get('is_global', 'false').lower() == 'true',
        user_id=user_id,
        matiere_id=request.form.get('matiere_id')
    )

    db.session.add(document)
    db.session.commit()

    return jsonify({
        'message': 'Document uploadé avec succès !',
        'document': {
            'id': document.id,
            'title': document.title,
            'file_type': document.file_type,
            'category': document.category,
            'niveau': document.niveau,
            'created_at': document.created_at.isoformat()
        }
    }), 201


# ─── LISTE DES DOCUMENTS ───────────────────────────────────
@documents_bp.route('/api/documents', methods=['GET'])
@jwt_required()
def get_documents():
    # Filtres optionnels
    category = request.args.get('category')
    niveau = request.args.get('niveau')
    matiere_id = request.args.get('matiere_id')
    keyword = request.args.get('q')

    query = Document.query

    if category:
        query = query.filter_by(category=category)
    if niveau:
        query = query.filter_by(niveau=niveau)
    if matiere_id:
        query = query.filter_by(matiere_id=matiere_id)
    if keyword:
        query = query.filter(Document.title.ilike(f'%{keyword}%'))

    documents = query.order_by(Document.created_at.desc()).all()

    return jsonify({
        'documents': [{
            'id': doc.id,
            'title': doc.title,
            'description': doc.description,
            'file_type': doc.file_type,
            'category': doc.category,
            'niveau': doc.niveau,
            'is_global': doc.is_global,
            'author': doc.author.username,
            'created_at': doc.created_at.isoformat()
        } for doc in documents]
    }), 200


# ─── DÉTAIL D'UN DOCUMENT ──────────────────────────────────
@documents_bp.route('/api/documents/<int:doc_id>', methods=['GET'])
@jwt_required()
def get_document(doc_id):
    document = Document.query.get_or_404(doc_id)

    return jsonify({
        'id': document.id,
        'title': document.title,
        'description': document.description,
        'download_url': f'/api/documents/{document.id}/download',
        'file_type': document.file_type,
        'category': document.category,
        'niveau': document.niveau,
        'is_global': document.is_global,
        'author': document.author.username,
        'matiere_id': document.matiere_id,
        'created_at': document.created_at.isoformat()
    }), 200


# ─── TÉLÉCHARGEMENT D'UN DOCUMENT ──────────────────────────
@documents_bp.route('/api/documents/<int:doc_id>/download', methods=['GET'])
@jwt_required()
def download_document(doc_id):
    document = Document.query.get_or_404(doc_id)

    # On accepte les anciens enregistrements (chemin complet) et les nouveaux (nom seul)
    filename = os.path.basename(document.file_url)
    upload_folder = os.path.abspath(current_app.config['UPLOAD_FOLDER'])

    if not os.path.exists(os.path.join(upload_folder, filename)):
        return jsonify({'error': 'Fichier introuvable sur le serveur'}), 404

    return send_from_directory(
        upload_folder, filename,
        as_attachment=True,
        download_name=f"{document.title}.{document.file_type}"
    )


# ─── SUPPRESSION D'UN DOCUMENT ─────────────────────────────
@documents_bp.route('/api/documents/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_document(doc_id):
    user_id = int(get_jwt_identity())
    document = Document.query.get_or_404(doc_id)

    if document.user_id != user_id:
        return jsonify({'error': 'Non autorisé'}), 403

    # Supprime le fichier physique (gère ancien chemin complet et nouveau nom seul)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = document.file_url
    if not os.path.exists(file_path):
        file_path = os.path.join(upload_folder, os.path.basename(document.file_url))
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(document)
    db.session.commit()

    return jsonify({'message': 'Document supprimé avec succès !'}), 200


# ─── RECHERCHE ─────────────────────────────────────────────
@documents_bp.route('/api/documents/search', methods=['GET'])
@jwt_required()
def search_documents():
    keyword = request.args.get('q', '')

    if not keyword:
        return jsonify({'error': 'Mot-clé requis'}), 400

    documents = Document.query.filter(
        Document.title.ilike(f'%{keyword}%') |
        Document.description.ilike(f'%{keyword}%')
    ).all()

    return jsonify({
        'results': [{
            'id': doc.id,
            'title': doc.title,
            'category': doc.category,
            'niveau': doc.niveau,
            'author': doc.author.username,
            'created_at': doc.created_at.isoformat()
        } for doc in documents]
    }), 200