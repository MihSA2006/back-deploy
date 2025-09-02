from django.urls import path
from .views import VoteCreateView, ResultatListView, ResultatFinaleDetailView, ResultatFinalePublishView, check_if_voted

urlpatterns = [
    path("voter/", VoteCreateView.as_view(), name="vote-create"),
    path("resultats/<int:election_id>/", ResultatListView.as_view(), name="resultat-list"),
    path("resultat-finale/<int:election_id>/", ResultatFinaleDetailView.as_view(), name="resultat-finale-detail"),
    path("resultat-finale/<int:election_id>/publish/", ResultatFinalePublishView.as_view(), name="resultat-finale-publish"),
    path("check/<int:election_id>/<int:auth_id>/", check_if_voted, name="vote-check"),
]
