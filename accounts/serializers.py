from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate
import re

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email_admin = serializers.EmailField()
    nom_admin = serializers.CharField()
    prenom_admin = serializers.CharField()
    pseudo_admin = serializers.CharField()
    
    class Meta:
        model = CustomUser
        fields = [
            'nom_admin', 'prenom_admin', 'pseudo_admin',
            'email_admin', 'password', 'photo_admin'
        ]

    def validate_nom_admin(self, value):
        if not re.fullmatch(r"[A-Za-zÀ-ÿ\-\'\s]+", value):
            raise serializers.ValidationError("Le nom ne doit contenir que des lettres, des espaces, des tirets ou des apostrophes.")
        return value

    def validate_prenom_admin(self, value):
        if not re.fullmatch(r"[A-Za-zÀ-ÿ\-\'\s]+", value):
            raise serializers.ValidationError("Le prénom ne doit contenir que des lettres, des espaces, des tirets ou des apostrophes.")
        return value

    def validate_password(self, value):
        if len(value) < 12:
            raise serializers.ValidationError("Le mot de passe doit contenir au moins 12 caractères.")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Le mot de passe doit contenir au moins une lettre majuscule.")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Le mot de passe doit contenir au moins une lettre minuscule.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Le mot de passe doit contenir au moins un caractère spécial.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email_admin = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email_admin")
        password = data.get("password")
        if email and password:
            user = authenticate(email_admin=email, password=password)
            if not user:
                raise serializers.ValidationError("Email ou mot de passe incorrect.")
            if not user.is_active:
                raise serializers.ValidationError("Ce compte est désactivé.")
            return user
        else:
            raise serializers.ValidationError("Tous les champs sont obligatoires.")


class FaceImageSerializer(serializers.Serializer):
    temp_token = serializers.CharField()
    image_capture = serializers.CharField()

    def validate_image_capture(self, value):
        if not value.startswith('data:image'):
            raise serializers.ValidationError("Format d'image invalide (base64 requis)")
        return value
    
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'



