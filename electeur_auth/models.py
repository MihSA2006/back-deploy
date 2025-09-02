from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from datetime import timedelta

from electeurs.models import Electeur  # adapte l'import selon ton app

class ElecteurAuth(models.Model):
    id = models.AutoField(primary_key=True)
    electeur = models.ForeignKey(Electeur, on_delete=models.CASCADE, related_name='auth_sessions')
    is_identifiant_valid = models.BooleanField(default=False)
    is_facial_valid = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=False)  # true après OTP ok
    date_auth = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    otp_hash = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['electeur']),
            models.Index(fields=['is_valid']),
            models.Index(fields=['date_auth']),
            models.Index(fields=['expired_at']),
        ]
        constraints = [
            # is_valid => is_identifiant_valid & is_facial_valid
            models.CheckConstraint(
                check=Q(is_valid=False) | (Q(is_identifiant_valid=True) & Q(is_facial_valid=True)),
                name='valid_requires_ident_and_face'
            ),
            # is_facial_valid => is_identifiant_valid
            models.CheckConstraint(
                check=Q(is_facial_valid=False) | Q(is_identifiant_valid=True),
                name='face_requires_ident'
            ),
        ]
        # Si tu es sur PostgreSQL, tu peux activer cette contrainte partielle
        # pour garantir 1 seule session valide non expirée par électeur :
        # constraints += [
        #     models.UniqueConstraint(
        #         fields=['electeur'],
        #         condition=Q(is_valid=True) & Q(expired_at__gt=timezone.now()),
        #         name='unique_active_valid_session_per_electeur'
        #     )
        # ]

    def clean(self):
        # Interdire d’avoir une session valide déjà active simultanément
        if not self.pk:
            now = timezone.now()
            exists_active = ElecteurAuth.objects.filter(
                electeur=self.electeur,
                is_valid=True,
                expired_at__gt=now
            ).exists()
            if exists_active:
                raise ValidationError("Une session active existe déjà pour cet électeur.")

    def set_otp(self, otp_plain: str):
        self.otp_hash = make_password(otp_plain)

    def check_otp(self, otp_plain: str) -> bool:
        if not self.otp_hash:
            return False
        return check_password(otp_plain, self.otp_hash)

    @property
    def is_expired(self):
        return self.expired_at is not None and self.expired_at <= timezone.now()

    @staticmethod
    def purge_stale():
        """Supprime:
        - les sessions non-valides de plus de 5 minutes
        - les sessions valides mais expirées
        """
        now = timezone.now()
        stale_threshold = now - timedelta(minutes=5)
        ElecteurAuth.objects.filter(is_valid=False, date_auth__lt=stale_threshold).delete()
        ElecteurAuth.objects.filter(is_valid=True, expired_at__lt=now).delete()
