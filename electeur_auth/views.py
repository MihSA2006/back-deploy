from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .serializers import StartAuthSerializer, FaceAuthSerializer, VerifyOTPSerializer
from .models import ElecteurAuth
from .utils import cleanup_expired_auths

class StartAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print("\n[StartAuthView] 🚀 Début du processus d’authentification (étape 1)")
        print("[StartAuthView] Données reçues :", request.data)

        serializer = StartAuthSerializer(data=request.data)
        if serializer.is_valid():
            auth = serializer.save()
            print(f"[StartAuthView] ✅ Auth créée avec ID={auth.id} pour électeur={auth.electeur}")
            return Response({"auth_id": auth.id, "status": "ident_valid"}, status=status.HTTP_201_CREATED)

        print("[StartAuthView] ❌ Erreurs de validation :", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FaceAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print("\n[FaceAuthView] 🚀 Début du processus de reconnaissance faciale (étape 2)")
        print("[FaceAuthView] Données reçues :", request.data)

        cleanup_expired_auths()
        print("[FaceAuthView] 🧹 Sessions expirées nettoyées")

        serializer = FaceAuthSerializer(data=request.data)
        if serializer.is_valid():
            print("[FaceAuthView] ✅ Données valides")
            response = serializer.save()
            print("[FaceAuthView] 🎉 Succès :", response)
            return Response(response, status=status.HTTP_200_OK)

        print("[FaceAuthView] ❌ Erreurs de validation :", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print("\n[VerifyOTPView] 🚀 Début de vérification OTP (étape 3)")
        print("[VerifyOTPView] Données reçues :", request.data)

        cleanup_expired_auths()
        print("[VerifyOTPView] 🧹 Sessions expirées nettoyées")

        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            print("[VerifyOTPView] ✅ OTP validé avec succès")
            return Response(result, status=status.HTTP_200_OK)

        print("[VerifyOTPView] ❌ Erreurs de validation :", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# electeur_auth/views.py
class DeleteAuthSessionView(APIView):
    def delete(self, request, id):   # <--- ici on met "id"
        try:
            session = ElecteurAuth.objects.get(id=id)  # idem ici
            session.delete()
            return Response({"message": "Session supprimée"}, status=200)
        except ElecteurAuth.DoesNotExist:
            return Response({"error": "Session introuvable"}, status=404)

