from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Vote, Resultat, ResultatFinale
from electeur_auth.models import ElecteurAuth


class VoteSerializer(serializers.ModelSerializer):
    auth_id = serializers.IntegerField(write_only=True)  # identifiant de session auth

    class Meta:
        model = Vote
        fields = ["id_vote", "election", "candidat", "auth_id", "date_vote"]

        read_only_fields = ["id_vote", "date_vote"]

    def validate(self, data):
        auth_id = data.pop("auth_id", None)
        if not auth_id:
            raise serializers.ValidationError({"auth_id": "auth_id est requis."})

        try:
            auth = ElecteurAuth.objects.select_related("electeur").get(pk=auth_id)
        except ElecteurAuth.DoesNotExist:
            raise serializers.ValidationError({"auth_id": "Session d’authentification introuvable."})

        if not auth.is_valid or auth.is_expired:
            raise serializers.ValidationError({"auth_id": "Session invalide ou expirée."})

        data["electeur"] = auth.electeur
        return data


class ResultatSerializer(serializers.ModelSerializer):
    candidat_nom = serializers.CharField(source="candidat.nom_candidat", read_only=True)

    class Meta:
        model = Resultat
        fields = [
            "id_resultat",
            "election",
            "candidat",
            "candidat_nom",
            "tour",
            "nb_votes",
            "total_votes_election",
            "taux_participation",
        ]


class ResultatFinaleSerializer(serializers.ModelSerializer):
    candidat_elu_nom = serializers.CharField(source="candidat_elu.nom_candidat", read_only=True)

    class Meta:
        model = ResultatFinale
        fields = [
            "id_resultatFinale",
            "election",
            "candidat_elu",
            "candidat_elu_nom",
            "nb_vote_total_obtenu",
            "taux_participation",
            "tour_finale",
            "date_finalisation",
            "archive_pdf",
            "is_publish",  # ✅ Ajouté
        ]
        read_only_fields = ["id_resultatFinale", "date_finalisation", "archive_pdf"]
