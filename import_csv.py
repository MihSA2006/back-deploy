import os
import django
import csv
from datetime import datetime
# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'i_fidy_back.settings')  # Ajuste selon ton nom de projet
django.setup()

from electeurs.models import Region, District, Commune, Fokontany, Electeur
from django.db import transaction

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')


def import_regions():
    with open(os.path.join(DATA_PATH, 'electeurs_region.csv'), newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        print("👉 Champs CSV détectés (regions):", reader.fieldnames)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}
            Region.objects.get_or_create(
                id_region=row['id_region'],
                defaults={'nom_region': row['nom_region']}
            )


def import_districts():
    with open(os.path.join(DATA_PATH, 'electeurs_district.csv'), newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}
            region = Region.objects.get(id_region=row['id_region'])
            District.objects.get_or_create(
                id_district=row['id_district'],
                defaults={
                    'nom_district': row['nom_district'],
                    'region': region
                }
            )


def import_communes():
    with open(os.path.join(DATA_PATH, 'electeurs_commune.csv'), newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}
            district = District.objects.get(id_district=row['id_district'])
            Commune.objects.get_or_create(
                id_commune=row['id_commune'],
                defaults={
                    'nom_commune': row['nom_commune'],
                    'district': district
                }
            )


def import_fokontanys():
    with open(os.path.join(DATA_PATH, 'electeurs_fokontany.csv'), newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}
            commune = Commune.objects.get(id_commune=row['id_commune'])
            Fokontany.objects.get_or_create(
                id_fokontany=row['id_fokontany'],
                defaults={
                    'nom_fokontany': row['nom_fokontany'],
                    'nb_electeur_inscrit': row['nb_electeur_inscrit'],
                    'commune': commune
                }
            )


def import_electeurs():
    with open(os.path.join(DATA_PATH, 'electeurs_electeur.csv'), newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}
            fokontany = Fokontany.objects.get(id_fokontany=row['id_fokontany'])

            # ✅ convertir la date (str -> date)
            try:
                date_naissance = datetime.strptime(row['dateNaissance'], "%Y-%m-%d").date()
            except ValueError:
                print(f"⚠️ Erreur de date pour l’électeur {row['nom_electeur']} {row['prenom_electeur']} : {row['dateNaissance']}")
                continue

            Electeur.objects.get_or_create(
                id=row['id'],
                defaults={
                    'nom_electeur': row['nom_electeur'],
                    'prenom_electeur': row['prenom_electeur'],
                    'dateNaissance': date_naissance,  # ✅ bien en `date`
                    'lieuNaissance': row['lieuNaissance'],
                    'numCIN': row['numCIN'],
                    'adresse': row['adresse'],
                    'profession': row['profession'],
                    'email': row['email'],
                    'image': row['image'] if row['image'] else None,
                    'numTel': row['numTel'],
                    'fokontany': fokontany
                }
            )


@transaction.atomic
def run_import():
    print("📥 Importation en cours...")
    import_regions()
    import_districts()
    import_communes()
    import_fokontanys()
    import_electeurs()
    print("✅ Importation terminée avec succès.")


if __name__ == '__main__':
    run_import()