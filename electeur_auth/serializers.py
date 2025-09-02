from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
import secrets, string
from django.core.mail import send_mail
from django.conf import settings

from .models import ElecteurAuth
from electeurs.models import Electeur
from .face_validation import compare_faces  # ton fichier

import os
from django.core.files.storage import default_storage
from django.conf import settings

# 1) Démarrer l'authentification avec nom+prenom+cin
class StartAuthSerializer(serializers.Serializer):
    nom = serializers.CharField()
    prenom = serializers.CharField()
    numCIN = serializers.CharField()

    def validate(self, data):
        try:
            electeur = Electeur.objects.get(
                nom_electeur=data['nom'],
                prenom_electeur=data['prenom'],
                numCIN=data['numCIN']
            )
        except Electeur.DoesNotExist:
            raise serializers.ValidationError("Identifiants incorrects.")

        # Refuser si une session valide active existe
        from django.utils import timezone
        if ElecteurAuth.objects.filter(electeur=electeur, is_valid=True, expired_at__gt=timezone.now()).exists():
            raise serializers.ValidationError("Une session active existe déjà pour cet électeur.")
        data['electeur'] = electeur
        return data

    def create(self, validated):
        electeur = validated['electeur']
        # Purge préalable des sessions non-valides trop anciennes
        ElecteurAuth.purge_stale()
        auth = ElecteurAuth.objects.create(
            electeur=electeur,
            is_identifiant_valid=True,
            is_facial_valid=False,
            is_valid=False,
            expired_at=None,
            otp_hash=None
        )
        return auth




# 2) Étape faciale
class FaceAuthSerializer(serializers.Serializer):
    auth_id = serializers.IntegerField()
    captured_image = serializers.ImageField(write_only=True)

    def validate(self, data):
        print("[FaceAuthSerializer] 🔍 Validation démarrée avec données :", data)

        try:
            auth = ElecteurAuth.objects.select_related('electeur').get(pk=data['auth_id'])
            print(f"[FaceAuthSerializer] ✅ Session trouvée : auth_id={auth.id}, électeur={auth.electeur}")
        except ElecteurAuth.DoesNotExist:
            print("[FaceAuthSerializer] ❌ Session introuvable")
            raise serializers.ValidationError("Session d'authentification introuvable.")

        if not auth.is_identifiant_valid:
            print("[FaceAuthSerializer] ❌ Identifiants pas validés")
            raise serializers.ValidationError("Les identifiants ne sont pas validés.")
        if auth.is_facial_valid:
            print("[FaceAuthSerializer] ⚠️ Déjà validée par reconnaissance faciale")
            raise serializers.ValidationError("La reconnaissance faciale a déjà été validée.")
        if auth.is_expired:
            print("[FaceAuthSerializer] ❌ Session expirée")
            raise serializers.ValidationError("Session expirée.")

        if not auth.electeur.image:
            print("[FaceAuthSerializer] ❌ Pas d'image enregistrée pour l'électeur")
            raise serializers.ValidationError("Aucune image enregistrée pour cet électeur.")

        data['auth'] = auth
        return data

    def create(self, validated):
        print("[FaceAuthSerializer] 🚀 Create() avec données :", validated)
        auth: ElecteurAuth = validated['auth']
        up = validated['captured_image']

        # Sauvegarde temporaire
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_faces')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = default_storage.save(os.path.join('temp_faces', up.name), up)
        abs_temp_path = default_storage.path(temp_path)
        print(f"[FaceAuthSerializer] 📸 Image capturée sauvegardée en {abs_temp_path}")

        # Image de référence
        ref_path = auth.electeur.image.path
        print(f"[FaceAuthSerializer] 📂 Image de référence : {ref_path}")

        # Comparaison faciale
        try:
            match, distance = compare_faces(ref_path, abs_temp_path, threshold=0.7)
            print(f"[FaceAuthSerializer] 🔍 Résultat comparaison : match={match}, distance={distance}")
        except Exception as e:
            print("[FaceAuthSerializer] ❌ Erreur lors de la comparaison faciale :", str(e))
            raise serializers.ValidationError("Erreur lors de la comparaison faciale")
        finally:
            try:
                default_storage.delete(temp_path)
                print(f"[FaceAuthSerializer] 🧹 Fichier temporaire {temp_path} supprimé")
            except Exception as e:
                print("[FaceAuthSerializer] ⚠️ Erreur suppression fichier temp :", str(e))

        if not match:
            print("[FaceAuthSerializer] ❌ Reconnaissance faciale échouée")
            raise serializers.ValidationError("Reconnaissance faciale échouée.")

        # Génération OTP
        alphabet = string.ascii_letters + string.digits
        otp_plain = ''.join(secrets.choice(alphabet) for _ in range(15))
        print(f"[FaceAuthSerializer] 🔑 OTP généré (non hashé, envoyé par email) : {otp_plain}")

        # Stockage hashé
        auth.is_facial_valid = True
        auth.set_otp(otp_plain)
        auth.save(update_fields=['is_facial_valid', 'otp_hash'])
        print("[FaceAuthSerializer] ✅ OTP hashé stocké en DB")

        # Envoi email
        subject = "Votre code OTP d'authentification"
        message = (
            f"Bonjour {auth.electeur.prenom_electeur},\n\n"
            f"Voici votre code OTP : {otp_plain}\n"
            f"Il vous sera demandé pour finaliser votre authentification.\n\n"
            f"Ce code est confidentiel."
        )

        try:
            print(f"[FaceAuthSerializer] 📧 Tentative d’envoi email à {auth.electeur.email}")
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [auth.electeur.email], fail_silently=False)
            print("[FaceAuthSerializer] ✅ Email envoyé avec succès")
        except Exception as e:
            print("[FaceAuthSerializer] ❌ Erreur lors de l’envoi email :", str(e))
            raise serializers.ValidationError("Impossible d’envoyer l’email OTP.")

        return {"status": "facial_valid", "auth_id": auth.id}


# 3) Vérification de l’OTP
class VerifyOTPSerializer(serializers.Serializer):
    auth_id = serializers.IntegerField()
    otp = serializers.CharField()

    def validate(self, data):
        try:
            auth = ElecteurAuth.objects.get(pk=data['auth_id'])
        except ElecteurAuth.DoesNotExist:
            raise serializers.ValidationError("Session d'authentification introuvable.")

        if not auth.is_identifiant_valid or not auth.is_facial_valid:
            raise serializers.ValidationError("Les étapes précédentes ne sont pas validées.")
        if auth.is_valid:
            raise serializers.ValidationError("OTP déjà validé.")
        data['auth'] = auth
        return data

    def create(self, validated):
        auth: ElecteurAuth = validated['auth']
        otp_plain = validated['otp']

        if not auth.check_otp(otp_plain):
            raise serializers.ValidationError("OTP invalide.")

        # OK -> session valide 15 minutes
        from django.utils import timezone
        auth.is_valid = True
        auth.expired_at = timezone.now() + timedelta(minutes=15)
        auth.save(update_fields=['is_valid', 'expired_at'])

        return {"status": "valid", "expires_at": auth.expired_at}
