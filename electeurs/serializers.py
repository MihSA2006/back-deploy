from rest_framework import serializers
from .models import Region, District, Commune, Fokontany, Electeur

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'


class CommuneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commune
        fields = '__all__'


class FokontanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Fokontany
        fields = '__all__'


class ElecteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electeur
        fields = '__all__'
