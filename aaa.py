import csv
from openpyxl import Workbook
from datetime import date

# Données d'exemple
electeurs = [
    {
        "id": 1,
        "nom_electeur": "Rakotoarimanana",
        "prenom_electeur": "Sarobidy",
        "dateNaissance": "1998-05-20",
        "lieuNaissance": "Antananarivo",
        "numCIN": "100000000001",
        "adresse": "Lot II B 45 Bis",
        "profession": "Enseignant",
        "email": "rakoto@gmail.com",
        "image": "photos/1.jpg",
        "numTel": "0341234567",
        "fokontany_id": 3,
        "is_apte_vote": True
    },
    {
        "id": 2,
        "nom_electeur": "Randria",
        "prenom_electeur": "Voahirana",
        "dateNaissance": "1975-11-02",
        "lieuNaissance": "Fianarantsoa",
        "numCIN": "100000000002",
        "adresse": "Lot IV C 12",
        "profession": "Médecin",
        "email": "voahirana@yahoo.fr",
        "image": "",
        "numTel": "0329876543",
        "fokontany_id": 5,
        "is_apte_vote": False
    },
    {
        "id": 3,
        "nom_electeur": "Rakotomalala",
        "prenom_electeur": "Malala",
        "dateNaissance": "1985-08-15",
        "lieuNaissance": "Toliara",
        "numCIN": "100000000003",
        "adresse": "Lot I A 23",
        "profession": "Infirmier",
        "email": "malala@gmail.com",
        "image": "photos/3.jpg",
        "numTel": "0331234567",
        "fokontany_id": 2,
        "is_apte_vote": True
    },
    {
        "id": 4,
        "nom_electeur": "Randriamanantena",
        "prenom_electeur": "Andry",
        "dateNaissance": "1992-12-07",
        "lieuNaissance": "Antsirabe",
        "numCIN": "100000000004",
        "adresse": "Lot III B 17",
        "profession": "Avocat",
        "email": "andry@yahoo.fr",
        "image": "",
        "numTel": "0329871234",
        "fokontany_id": 1,
        "is_apte_vote": False
    }
]

# 1️⃣ Générer le CSV
csv_file = "electeurs.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=electeurs[0].keys())
    writer.writeheader()
    for e in electeurs:
        writer.writerow(e)

print(f"✅ Fichier CSV '{csv_file}' créé avec succès.")

# 2️⃣ Générer le Excel
excel_file = "electeurs.xlsx"
wb = Workbook()
ws = wb.active
ws.title = "Electeurs"

# Ajouter l'en-tête
ws.append(list(electeurs[0].keys()))

# Ajouter les données
for e in electeurs:
    ws.append(list(e.values()))

wb.save(excel_file)
print(f"✅ Fichier Excel '{excel_file}' créé avec succès.")
