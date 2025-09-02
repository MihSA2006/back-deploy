from rest_framework import serializers
from .models import TypeElection, Election, Candidat

class TypeElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeElection
        fields = '__all__'

class ElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = '__all__'
        read_only_fields = [
            'nb_candidat_inscrit',
            'dateFin',
            'tourActuel',
            'seuilMajorite',
            'status',  # ⬅️ REND LE STATUS NON MODIFIABLE
        ]

    def to_representation(self, instance):
        instance.update_status()
        instance.save(update_fields=['status'])
        return super().to_representation(instance)

class CandidatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidat
        fields = '__all__'
        read_only_fields = ['dateInscription', 'estQualifieTour2']