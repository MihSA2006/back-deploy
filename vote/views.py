from rest_framework.permissions import IsAdminUser
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Vote, Resultat, ResultatFinale
from .serializers import VoteSerializer, ResultatSerializer, ResultatFinaleSerializer

from rest_framework.decorators import api_view
from electeurs.models import Electeur
from electeur_auth.models import ElecteurAuth

# ✅ Enregistrer un vote
class VoteCreateView(generics.CreateAPIView):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer


# ✅ Lister les résultats d'une élection
class ResultatListView(generics.ListAPIView):
    serializer_class = ResultatSerializer

    def get_queryset(self):
        election_id = self.kwargs["election_id"]
        return Resultat.objects.filter(election_id=election_id).order_by("-nb_votes")


# ✅ Consulter le résultat final d’une élection
class ResultatFinaleDetailView(APIView):
    def get(self, request, election_id):
        resultat_final = get_object_or_404(ResultatFinale, election_id=election_id)


        serializer = ResultatFinaleSerializer(resultat_final)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ✅ Endpoint pour publier/dépublier un résultat final (admin uniquement)
# Endpoint pour publier/dépublier un résultat final (plus besoin d'auth)
class ResultatFinalePublishView(generics.UpdateAPIView):
    queryset = ResultatFinale.objects.all()
    serializer_class = ResultatFinaleSerializer
    permission_classes = []  # 🔓 aucune permission requise

    def get_object(self):
        election_id = self.kwargs["election_id"]
        return get_object_or_404(ResultatFinale, election_id=election_id)
    

@api_view(["GET"])
def check_if_voted(request, election_id, auth_id):
    try:
        # récupérer l'électeur à partir de sa session auth
        session = ElecteurAuth.objects.get(id=auth_id, is_valid=True)
        electeur = session.electeur
    except ElecteurAuth.DoesNotExist:
        return Response({"error": "Session invalide"}, status=401)

    has_voted = Vote.objects.filter(election_id=election_id, electeur=electeur).exists()
    return Response({"has_voted": has_voted})



# from rest_framework import generics, status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from django.shortcuts import get_object_or_404

# from .models import Vote, Resultat, ResultatFinale
# from .serializers import VoteSerializer, ResultatSerializer, ResultatFinaleSerializer


# # ✅ Enregistrer un vote
# class VoteCreateView(generics.CreateAPIView):
#     queryset = Vote.objects.all()
#     serializer_class = VoteSerializer


# # ✅ Lister les résultats d'une élection
# class ResultatListView(generics.ListAPIView):
#     serializer_class = ResultatSerializer

#     def get_queryset(self):
#         election_id = self.kwargs["election_id"]
#         return Resultat.objects.filter(election_id=election_id).order_by("-nb_votes")


# # ✅ Consulter le résultat final d’une élection
# class ResultatFinaleDetailView(APIView):
#     def get(self, request, election_id):
#         resultat_final = get_object_or_404(ResultatFinale, election_id=election_id)
#         serializer = ResultatFinaleSerializer(resultat_final)
#         return Response(serializer.data, status=status.HTTP_200_OK)
