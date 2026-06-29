# StudyHub

Plateforme web et mobile qui centralise les ressources académiques et favorise l'entraide
entre étudiants, avec deux espaces : **Campus** (université spécifique) et **Global**
(toutes universités). Objectif à terme : déploiement multi-universités en Afrique.

## Stack technique

- **Backend** : Flask (API REST), SQLAlchemy, Flask-JWT-Extended
- **Base de données** : SQLite (dev) / PostgreSQL (prod)
- **Frontend web** : HTML / CSS / JavaScript (templates Jinja2)
- **Mobile** (à venir) : Flutter

## Fonctionnalités actuelles

- Authentification JWT (inscription, connexion, rôles étudiant/enseignant/admin)
- Dépôt, téléchargement, recherche et catégorisation de documents
- Structure Campus : universités, filières, matières
- Profils étudiants, commentaires et notes (1–5 étoiles), favoris
- Forum (questions/réponses, votes, validation)
- Groupes (matière, filière, projet)
- Messagerie privée et de groupe

## Installation

```bash
# 1. Cloner le dépôt
git clone <url-du-depot>
cd studyhub

# 2. Créer et activer un environnement virtuel
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. (Optionnel) Configurer les variables d'environnement
cp .env.example .env

# 5. Lancer l'application
python run.py
```

L'application démarre sur http://127.0.0.1:5000 et crée automatiquement la base de données.

## Structure du projet

```
studyhub/
├── app/
│   ├── __init__.py        # Création de l'app et enregistrement des blueprints
│   ├── models/            # Modèles SQLAlchemy
│   ├── routes/            # Endpoints API + pages
│   ├── templates/         # Vues HTML (Jinja2)
│   └── static/            # CSS, JS, fichiers uploadés
├── config.py
├── run.py
└── requirements.txt
```
