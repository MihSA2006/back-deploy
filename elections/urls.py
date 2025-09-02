from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TypeElectionViewSet, ElectionViewSet, CandidatViewSet

router = DefaultRouter()
router.register(r'type-elections', TypeElectionViewSet)
router.register(r'elections', ElectionViewSet)
router.register(r'candidats', CandidatViewSet)

urlpatterns = [
    path('', include(router.urls)),
]