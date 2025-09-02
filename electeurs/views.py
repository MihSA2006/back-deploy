from rest_framework import viewsets, filters
from .models import Region, District, Commune, Fokontany, Electeur
from .serializers import *
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime

import pandas as pd
from django.http import JsonResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework.response import Response
from rest_framework import status

class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all().order_by('id_region')
    serializer_class = RegionSerializer
class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.all().order_by('id_district')
    serializer_class = DistrictSerializer
class CommuneViewSet(viewsets.ModelViewSet):
    queryset = Commune.objects.all().order_by('id_commune')
    serializer_class = CommuneSerializer
class FokontanyViewSet(viewsets.ModelViewSet):
    queryset = Fokontany.objects.all().order_by('id_fokontany')
    serializer_class = FokontanySerializer



class ElecteurViewSet(viewsets.ModelViewSet):
    queryset = Electeur.objects.all()
    serializer_class = ElecteurSerializer

    # 🆕 Ajout de filtres et recherche
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_apte_vote']  # filtre direct ?is_apte_vote=true
    search_fields = [
        'nom_electeur',
        'prenom_electeur',
        'adresse',
        'email',
        'profession',
        'numTel',
    ]

    def get_queryset(self):
        queryset = Electeur.objects.all()

        region_id = self.request.query_params.get('region')
        district_id = self.request.query_params.get('district')
        commune_id = self.request.query_params.get('commune')
        fokontany_id = self.request.query_params.get('fokontany')

        if region_id:
            queryset = queryset.filter(fokontany__commune__district__region__id_region=region_id)
        if district_id:
            queryset = queryset.filter(fokontany__commune__district__id_district=district_id)
        if commune_id:
            queryset = queryset.filter(fokontany__commune__id_commune=commune_id)
        if fokontany_id:
            queryset = queryset.filter(fokontany__id_fokontany=fokontany_id)

        # ✅ filtre apte
        apte = self.request.query_params.get('is_apte_vote')
        if apte is not None:
            apte_str = apte.lower()
            if apte_str in ('true', '1', 'yes'):
                queryset = queryset.filter(is_apte_vote=True)
            elif apte_str in ('false', '0', 'no'):
                queryset = queryset.filter(is_apte_vote=False)

        return queryset

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def preview_electeurs(request):
    file = request.FILES.get("file")
    if not file:
        print("⚠️ Aucun fichier reçu")
        return JsonResponse({"error": "Aucun fichier envoyé"}, status=400)

    try:
        print(f"📂 Fichier reçu : {file.name}")

        # Détection CSV ou Excel
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        print("📊 Colonnes détectées :", df.columns.tolist())

        colonnes_attendues = [
            "nom_electeur", "prenom_electeur", "dateNaissance",
            "lieuNaissance", "numCIN", "adresse", "profession",
            "email", "numTel", "fokontany_id", "image", "is_apte_vote"
        ]

        # Ajouter colonnes manquantes
        for col in colonnes_attendues:
            if col not in df.columns:
                print(f"⚠️ Colonne manquante ajoutée : {col}")
                df[col] = None if col == "image" else ""

        # Sélectionner et réordonner les colonnes
        df = df[colonnes_attendues]

        # Remplacer NaN par None pour image, "" pour le reste
        for col in df.columns:
            if col == "image":
                df[col] = df[col].where(pd.notna(df[col]), None)
            else:
                df[col] = df[col].fillna("")

        # Convertir date
        df["dateNaissance"] = pd.to_datetime(df["dateNaissance"], errors="coerce").dt.strftime("%Y-%m-%d")

        data = df.to_dict(orient="records")
        print(f"✅ {len(data)} lignes prêtes pour prévisualisation")
        return JsonResponse({"data": data}, safe=False)

    except Exception as e:
        print("❌ Erreur lors de la prévisualisation :", str(e))
        return JsonResponse({"error": str(e)}, status=400)


@api_view(['POST'])
def save_electeurs(request):
    electeurs = request.data.get("electeurs", [])
    created = 0

    for row in electeurs:
        try:
            date_naissance = datetime.strptime(row["dateNaissance"], "%Y-%m-%d").date()
            fokontany = Fokontany.objects.get(id_fokontany=row["fokontany_id"])

            Electeur.objects.create(
                nom_electeur=row["nom_electeur"],
                prenom_electeur=row["prenom_electeur"],
                dateNaissance=date_naissance,
                lieuNaissance=row["lieuNaissance"],
                numCIN=row["numCIN"],
                adresse=row["adresse"],
                profession=row["profession"],
                email=row["email"],
                numTel=row["numTel"],
                fokontany=fokontany,
                image=row.get("image", None),
                is_apte_vote=row.get("is_apte_vote", False)
            )
            created += 1
        except Exception as e:
            print("❌ Erreur import électeur:", e)

    return JsonResponse({"status": "ok", "importés": created})


@api_view(["POST"])
def verifier_electeur(request):
    """
    Vérifier si un électeur est dans la liste et peut voter.
    Entrées attendues : nom_electeur, prenom_electeur, numCIN
    Accessible sans authentification.
    """
    nom = request.data.get("nom_electeur", "").strip()
    prenom = request.data.get("prenom_electeur", "").strip()
    numCIN = request.data.get("numCIN", "").strip()

    if not (nom and prenom and numCIN):
        return Response(
            {"error": "Veuillez fournir nom_electeur, prenom_electeur et numCIN."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        electeur = Electeur.objects.get(
            nom_electeur__iexact=nom,
            prenom_electeur__iexact=prenom,
            numCIN=numCIN
        )

        if electeur.is_apte_vote:
            return Response({
                "present": True,
                "peut_voter": True,
                "message": f"{electeur.nom_electeur} {electeur.prenom_electeur} est présent et apte à voter."
            })
        else:
            return Response({
                "present": True,
                "peut_voter": False,
                "message": f"{electeur.nom_electeur} {electeur.prenom_electeur} est présent mais n’est pas apte à voter."
            })

    except Electeur.DoesNotExist:
        return Response({
            "present": False,
            "peut_voter": False,
            "message": "Cet électeur n’est pas trouvé dans la liste."
        })
    