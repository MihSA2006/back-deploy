# init_data.py
import os
import django
from django.utils import timezone
from datetime import timedelta
import subprocess

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "i_fidy_back.settings")
django.setup()

from elections.models import TypeElection, Election, Candidat
from electeurs.models import Electeur  # Assure-toi que ce modèle existe bien

# 1. Création des types d’élections
types = ["Elections Presidentielle", "Elections Legislatif", "Election Communale"]
for titre in types:
    obj, created = TypeElection.objects.get_or_create(titre=titre)
    if created:
        print(f"[OK] TypeElection créé : {titre}")
    else:
        print(f"[INFO] TypeElection déjà existant : {titre}")

# Récupérer le type d’élection présidentielle
type_pres = TypeElection.objects.get(titre="Elections Presidentielle")

# 2. Création de l’élection présidentielle (dans 15 jours)
date_debut = timezone.now() + timedelta(days=15)
election, created = Election.objects.get_or_create(
    type_election=type_pres,
    dateDebut=date_debut,
)
if created:
    print(f"[OK] Election présidentielle créée : {election}")
else:
    print(f"[INFO] Election présidentielle déjà existante : {election}")

# 3. Ajout de 2 candidats
# Assure-toi que les électeurs avec id=1 et id=2 existent
images_path = os.path.join("media", "images", "candidats")

candidats_data = [
    {"id_electeur": 1, "numCandidat": 1, "pseudo": "Face1", "photo": "face1.jpg"},
    {"id_electeur": 2, "numCandidat": 2, "pseudo": "JackieChan", "photo": "jackie-chan2.jpg"},
]

for data in candidats_data:
    try:
        electeur = Electeur.objects.get(pk=data["id_electeur"])
    except Electeur.DoesNotExist:
        print(f"[ERREUR] Electeur avec id={data['id_electeur']} introuvable.")
        continue

    photo_path = os.path.join(images_path, data["photo"])
    if not os.path.exists(photo_path):
        print(f"[ERREUR] Image introuvable : {photo_path}")
        continue

    with open(photo_path, "rb") as f:
        candidat, created = Candidat.objects.get_or_create(
            election=election,
            id_electeur=electeur,
            numCandidat=data["numCandidat"],
            defaults={
                "pseudo": data["pseudo"],
                "biographie": f"Biographie de {data['pseudo']}",
                "photo_candidat": f"images/candidats/{data['photo']}",
            },
        )
        if created:
            print(f"[OK] Candidat {data['pseudo']} ajouté.")
        else:
            print(f"[INFO] Candidat {data['pseudo']} déjà existant.")

# 4. Mise à jour du statut de l’élection → En cours
election.status = "En cours"
election.dateDebut = timezone.now()
election.dateFin = timezone.now() + timedelta(days=1)
election.save(update_fields=["status", "dateDebut", "dateFin"])
print(f"[OK] Election mise à jour en cours : {election}")

# 5. Exécution du script import_votes.py
# try:
#     print("[INFO] Exécution de import_votes.py ...")
#     subprocess.run(["python", "import_votes.py"], check=True)
#     print("[OK] Script import_votes.py exécuté avec succès.")
# except subprocess.CalledProcessError as e:
#     print(f"[ERREUR] Echec lors de l’exécution de import_votes.py : {e}")
