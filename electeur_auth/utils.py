# electeur_auth/utils.py

from django.utils import timezone
from .models import ElecteurAuth

def cleanup_expired_auths():
    try:
        expired_count = ElecteurAuth.objects.filter(expired_at__lt=timezone.now()).count()
        ElecteurAuth.objects.filter(expired_at__lt=timezone.now()).delete()
        print(f"[CLEANUP] {expired_count} sessions expirées supprimées.")
    except Exception as e:
        import traceback
        print("[CLEANUP][ERREUR]", str(e))
        traceback.print_exc()
