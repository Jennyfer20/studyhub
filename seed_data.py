"""
Script de données de démonstration pour StudyHub.

Remplit la base avec des universités, filières, matières, étudiants, documents,
posts de forum, groupes, commentaires, favoris et messages — pour que toutes les
pages affichent du contenu réaliste.

Usage :
    python seed_data.py            # peuple si la base est vide de démo
    python seed_data.py --force    # efface les données existantes puis re-peuple

Comptes de démo créés (mot de passe identique pour tous : demo1234) :
    alice@studyhub.cm, bruno@studyhub.cm, chloe@studyhub.cm,
    david@studyhub.cm (enseignant), admin@studyhub.cm (admin)
"""
import os
import sys
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User, University, Filiere, Matiere, Document
from app.routes.forum import ForumPost, ForumReply, PostLike
from app.routes.groups import Group, GroupMember
from app.routes.comments import Comment
from app.routes.favorites import Favorite
from app.routes.messages import Message

DEMO_PASSWORD = 'demo1234'


def wipe():
    """Efface toutes les données (pas le schéma)."""
    for model in (Message, Favorite, Comment, PostLike, ForumReply, ForumPost,
                  GroupMember, Group, Document, Matiere, Filiere, User, University):
        db.session.query(model).delete()
    db.session.commit()


def make_file(upload_folder, stored_name, text):
    """Crée un petit fichier réel pour que le téléchargement fonctionne."""
    os.makedirs(upload_folder, exist_ok=True)
    with open(os.path.join(upload_folder, stored_name), 'w', encoding='utf-8') as f:
        f.write(text)


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        force = '--force' in sys.argv
        existing = University.query.filter_by(name='Université de Yaoundé I').first()
        if existing and not force:
            print("La base contient déjà des données de démo.")
            print("Relance avec  python seed_data.py --force  pour tout réinitialiser.")
            return
        if force:
            print("Réinitialisation des données...")
            wipe()

        upload_folder = app.config['UPLOAD_FOLDER']

        # ─── UNIVERSITÉS ───────────────────────────────────────
        uni1 = University(name='Université de Yaoundé I', country='Cameroun', city='Yaoundé')
        uni2 = University(name='Université de Douala', country='Cameroun', city='Douala')
        db.session.add_all([uni1, uni2])
        db.session.flush()

        # ─── FILIÈRES ──────────────────────────────────────────
        f_info = Filiere(name='Informatique', university_id=uni1.id)
        f_gestion = Filiere(name='Gestion', university_id=uni1.id)
        f_reseaux = Filiere(name='Réseaux & Télécoms', university_id=uni2.id)
        db.session.add_all([f_info, f_gestion, f_reseaux])
        db.session.flush()

        # ─── MATIÈRES ──────────────────────────────────────────
        m_python = Matiere(name='Programmation Python', filiere_id=f_info.id)
        m_bd = Matiere(name='Bases de données', filiere_id=f_info.id)
        m_compta = Matiere(name='Comptabilité générale', filiere_id=f_gestion.id)
        m_reseaux = Matiere(name='Administration réseaux', filiere_id=f_reseaux.id)
        db.session.add_all([m_python, m_bd, m_compta, m_reseaux])
        db.session.flush()

        # ─── UTILISATEURS ──────────────────────────────────────
        pw = generate_password_hash(DEMO_PASSWORD)
        alice = User(email='alice@studyhub.cm', username='alice', password_hash=pw,
                     role='student', filiere='Informatique', niveau='L2',
                     university_id=uni1.id, bio="Passionnée de Python et d'IA.")
        bruno = User(email='bruno@studyhub.cm', username='bruno', password_hash=pw,
                     role='student', filiere='Gestion', niveau='L3',
                     university_id=uni1.id, bio="Étudiant en gestion, fan de comptabilité.")
        chloe = User(email='chloe@studyhub.cm', username='chloe', password_hash=pw,
                     role='student', filiere='Réseaux & Télécoms', niveau='M1',
                     university_id=uni2.id, bio="Future ingénieure réseaux.")
        david = User(email='david@studyhub.cm', username='david', password_hash=pw,
                     role='teacher', filiere='Informatique', niveau=None,
                     university_id=uni1.id, bio="Enseignant en informatique.")
        admin = User(email='admin@studyhub.cm', username='admin', password_hash=pw,
                     role='admin', university_id=uni1.id, bio="Administrateur de la plateforme.")
        db.session.add_all([alice, bruno, chloe, david, admin])
        db.session.flush()

        # ─── DOCUMENTS ─────────────────────────────────────────
        docs_data = [
            ('Cours Python — Chapitre 1', 'Introduction aux variables et types.', 'cours', 'L2', m_python.id, alice.id, False),
            ('TD Python — Les boucles', 'Exercices sur for et while.', 'td', 'L2', m_python.id, david.id, False),
            ('Examen Bases de données 2024', 'Sujet d\'examen SQL avec corrigé.', 'examen', 'L2', m_bd.id, david.id, True),
            ('Résumé Comptabilité générale', 'Fiche de révision bilan et compte de résultat.', 'résumé', 'L3', m_compta.id, bruno.id, False),
            ('Cours Réseaux — Modèle OSI', 'Les 7 couches expliquées simplement.', 'cours', 'M1', m_reseaux.id, chloe.id, True),
            ('TD SQL — Jointures', 'Exercices sur INNER et LEFT JOIN.', 'td', 'L2', m_bd.id, alice.id, False),
        ]
        docs = []
        for i, (title, desc, cat, niv, mid, uid, glob) in enumerate(docs_data):
            stored = f'demo_doc_{i+1}.txt'
            make_file(upload_folder, stored, f'{title}\n\n{desc}\n\n(Document de démonstration StudyHub)')
            d = Document(title=title, description=desc, file_url=stored, file_type='txt',
                         category=cat, niveau=niv, is_global=glob, user_id=uid, matiere_id=mid)
            docs.append(d)
        db.session.add_all(docs)
        db.session.flush()

        # ─── COMMENTAIRES & NOTES ──────────────────────────────
        db.session.add_all([
            Comment(content='Très clair, merci !', rating=5, user_id=bruno.id, document_id=docs[0].id),
            Comment(content='Bien mais il manque des exemples.', rating=4, user_id=chloe.id, document_id=docs[0].id),
            Comment(content='Le corrigé m\'a beaucoup aidé.', rating=5, user_id=alice.id, document_id=docs[2].id),
            Comment(content='Parfait pour réviser.', rating=5, user_id=chloe.id, document_id=docs[4].id),
        ])

        # ─── FAVORIS ───────────────────────────────────────────
        db.session.add_all([
            Favorite(user_id=alice.id, document_id=docs[2].id),
            Favorite(user_id=alice.id, document_id=docs[4].id),
            Favorite(user_id=bruno.id, document_id=docs[0].id),
        ])

        # ─── FORUM ─────────────────────────────────────────────
        post1 = ForumPost(title='Comment lire un fichier en Python ?',
                          content='Bonjour, quelqu\'un peut m\'expliquer open() et with ?',
                          user_id=alice.id, matiere_id=m_python.id, votes=3)
        post2 = ForumPost(title='Différence entre INNER JOIN et LEFT JOIN ?',
                          content='Je confonds toujours les deux, une astuce ?',
                          user_id=bruno.id, matiere_id=m_bd.id, votes=5, is_resolved=True)
        db.session.add_all([post1, post2])
        db.session.flush()
        db.session.add_all([
            ForumReply(content='Utilise `with open("f.txt") as f:` c\'est plus sûr.',
                       user_id=david.id, post_id=post1.id, votes=2),
            ForumReply(content='INNER = intersection, LEFT = tout à gauche + correspondances.',
                       user_id=chloe.id, post_id=post2.id, votes=4, is_validated=True),
        ])

        # ─── LIKES SUR LES POSTS ───────────────────────────────
        db.session.add_all([
            PostLike(user_id=bruno.id, post_id=post1.id),
            PostLike(user_id=chloe.id, post_id=post1.id),
            PostLike(user_id=david.id, post_id=post1.id),
            PostLike(user_id=alice.id, post_id=post2.id),
            PostLike(user_id=chloe.id, post_id=post2.id),
        ])

        # ─── GROUPES ───────────────────────────────────────────
        g1 = Group(name='Groupe Python L2', description='Entraide sur la programmation Python.',
                   type='matiere', is_global=False, created_by=alice.id)
        g2 = Group(name='Projet Web StudyHub', description='On construit une app ensemble !',
                   type='projet', is_global=True, created_by=chloe.id)
        g3 = Group(name='Filière Informatique', description='Tous les étudiants en info.',
                   type='filiere', is_global=False, created_by=david.id)
        db.session.add_all([g1, g2, g3])
        db.session.flush()
        db.session.add_all([
            GroupMember(user_id=alice.id, group_id=g1.id, role='admin'),
            GroupMember(user_id=bruno.id, group_id=g1.id, role='member'),
            GroupMember(user_id=chloe.id, group_id=g2.id, role='admin'),
            GroupMember(user_id=alice.id, group_id=g2.id, role='member'),
            GroupMember(user_id=david.id, group_id=g3.id, role='admin'),
        ])

        # ─── MESSAGES ──────────────────────────────────────────
        db.session.add_all([
            Message(content='Salut Bruno, tu as le TD de Python ?', sender_id=alice.id, receiver_id=bruno.id, is_read=True),
            Message(content='Oui je te l\'envoie ce soir !', sender_id=bruno.id, receiver_id=alice.id, is_read=True),
            Message(content='Merci beaucoup 🙏', sender_id=alice.id, receiver_id=bruno.id, is_read=False),
            Message(content='Chloé, on se voit pour le projet web ?', sender_id=alice.id, receiver_id=chloe.id, is_read=False),
        ])

        db.session.commit()

        print("Donnees de demonstration creees avec succes !")
        print(f"   {University.query.count()} universites, {User.query.count()} utilisateurs, "
              f"{Document.query.count()} documents,")
        print(f"   {ForumPost.query.count()} posts de forum, {Group.query.count()} groupes, "
              f"{Comment.query.count()} commentaires.")
        print()
        print("Connexion de demo (mot de passe : demo1234) :")
        print("   alice@studyhub.cm  (étudiante)")
        print("   david@studyhub.cm  (enseignant)")
        print("   admin@studyhub.cm  (admin)")


if __name__ == '__main__':
    seed()
