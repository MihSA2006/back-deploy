import os
import django
import csv
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'i_fidy_back.settings')
django.setup()

from vote.models import Vote
from elections.models import Election, Candidat
from electeurs.models import Electeur


DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')


def import_votes():
    """
    Importer un fichier CSV contenant des votes.
    Colonnes attendues :
        election_id, electeur_id, candidat_id, tour
    """
    filename = os.path.join(DATA_PATH, 'votes.csv')
    with open(filename, newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        print("👉 Champs CSV détectés (votes):", reader.fieldnames)

        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}

            try:
                # utiliser les bons champs PK
                election = Election.objects.get(id_election=row['election_id'])
                electeur = Electeur.objects.get(id=row['electeur_id'])
                candidat = Candidat.objects.get(id_candidat=row['candidat_id'])

                vote = Vote(
                    election=election,
                    electeur=electeur,
                    candidat=candidat,
                    tour=int(row['tour'])
                )
                vote.save()  # déclenche clean(), encryption et signal Resultat

            except Exception as e:
                print(f"❌ Erreur ligne {row}: {e}")


@transaction.atomic
def run_import():
    print("📥 Importation des votes en cours...")
    import_votes()
    print("✅ Importation des votes terminée.")


if __name__ == '__main__':
    run_import()
