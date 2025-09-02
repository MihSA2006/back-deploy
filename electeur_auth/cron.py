from .models import ElecteurAuth

def purge_electeur_auth():
    ElecteurAuth.purge_stale()
    print("Purge des sessions ElecteurAuth effectuée.")