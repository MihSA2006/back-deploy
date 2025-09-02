from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework.permissions import IsAuthenticated
from .models import CustomUser
from django.conf import settings
import os
import base64
import numpy as np
import cv2
import face_recognition
import face_recognition_models
from .face_validation import compare_faces
from django.core.files.uploadedfile import InMemoryUploadedFile
from .temp_tokens import generate_temp_token
from .temp_tokens import validate_temp_token, delete_temp_token

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        print("📥 Requête de connexion reçue")
        print(f"   - Données reçues : {request.data}")

        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            print(f"✅ Identifiants valides pour : {user.email_admin}")
            
            temp_token = generate_temp_token(user.id)
            print(f"🔑 Token temporaire généré : {temp_token}")

            return Response({
                "temp_token": temp_token,
                "message": "Identifiants valides. Procéder à la reconnaissance faciale."
            }, status=200)
        else:
            print("❌ Échec de la validation des identifiants")
            print(f"   - Erreurs : {serializer.errors}")

        return Response(serializer.errors, status=401)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Déconnexion réussie."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Token invalide ou déjà blacklisté."}, status=status.HTTP_400_BAD_REQUEST)
        
class FacialAuthView(APIView):
    def post(self, request):
        print("\n📥 Authentification faciale lancée")
        temp_token = request.data.get("temp_token")
        image_base64 = request.data.get("image_capture")

        print(f"   - Token temporaire reçu : {temp_token}")
        print(f"   - Image reçue ? {'Oui' if image_base64 else 'Non'}")

        if not temp_token or not image_base64:
            print("❌ Token ou image manquant(e)")
            return Response({"detail": "Token temporaire ou image manquant"}, status=400)

        user_id = validate_temp_token(temp_token)
        if not user_id:
            print("❌ Token invalide ou expiré")
            return Response({"detail": "Token facial invalide ou expiré"}, status=401)

        try:
            admin = CustomUser.objects.get(id=user_id)
            print(f"✅ Utilisateur trouvé : {admin.email_admin}")
        except CustomUser.DoesNotExist:
            print("❌ Utilisateur introuvable avec cet ID")
            return Response({"detail": "Utilisateur introuvable"}, status=404)

        if not admin.photo_admin:
            print("❌ Aucun visage de référence enregistré")
            return Response({"detail": "Aucune photo enregistrée"}, status=404)

        # 🔄 Traitement de l’image capturée
        try:
            img_data = base64.b64decode(image_base64.split(',')[1])
            os.makedirs("temp", exist_ok=True)
            temp_filename = os.path.join("temp", f"{admin.id}_temp.jpg")

            with open(temp_filename, "wb") as f:
                f.write(img_data)
            print(f"📸 Image temporaire enregistrée à : {temp_filename}")
        except Exception as e:
            print(f"❌ Erreur lors du traitement de l'image capturée : {e}")
            return Response({"detail": "Erreur dans le traitement de l'image"}, status=400)

        print("🔍 Début de la comparaison faciale...")
        match, distance = compare_faces(admin.photo_admin.path, temp_filename, threshold=0.6)

        os.remove(temp_filename)
        print("🧹 Image temporaire supprimée.")

        if match:
            print(f"✅ Visage reconnu. Distance : {distance:.4f}")
            delete_temp_token(temp_token)
            refresh = RefreshToken.for_user(admin)
            return Response({
                'user': UserSerializer(admin).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=200)
        else:
            print(f"❌ Visage non reconnu. Distance : {distance:.4f}")
            return Response({"detail": "Échec de la vérification faciale"}, status=403)
