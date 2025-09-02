from rest_framework import viewsets
from .models import TypeElection, Election, Candidat
from .serializers import TypeElectionSerializer, ElectionSerializer, CandidatSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as drf_status
from django.utils import timezone


class TypeElectionViewSet(viewsets.ModelViewSet):
    queryset = TypeElection.objects.all()
    serializer_class = TypeElectionSerializer

class ElectionViewSet(viewsets.ModelViewSet):
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer

    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        election = self.get_object()
        nouveau_statut = request.data.get('status')

        if nouveau_statut not in dict(Election.STATUS_CHOICES):
            return Response({"error": "Statut invalide"}, status=drf_status.HTTP_400_BAD_REQUEST)

        now = timezone.now()

        if nouveau_statut == "En cours":
            election.dateDebut = now
            election.dateFin = now + timezone.timedelta(days=1)
            election.status = "En cours"
        elif nouveau_statut == "Terminée":
            election.dateFin = now
            election.status = "Terminée"
        elif nouveau_statut == "Annulée":
            election.dateDebut = None
            election.dateFin = None
            election.status = "Annulée"
        else:
            election.status = nouveau_statut  # fallback si d'autres cas

        election.save()
        return Response({
            "message": "Statut et dates mis à jour avec succès",
            "status": election.status,
            "dateDebut": election.dateDebut,
            "dateFin": election.dateFin,
        })


class CandidatViewSet(viewsets.ModelViewSet):
    queryset = Candidat.objects.all()
    serializer_class = CandidatSerializer




