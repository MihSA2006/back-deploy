from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('regions', RegionViewSet)
router.register('districts', DistrictViewSet)
router.register('communes', CommuneViewSet)
router.register('fokontanys', FokontanyViewSet)
router.register('electeurs', ElecteurViewSet)

# urlpatterns = [
#     path('', include(router.urls)),
#     path("electeurs/preview/", preview_electeurs),
#     path("electeurs/save/", save_electeurs),
# ]

urlpatterns = [
    path("electeurs/preview/", preview_electeurs),
    path("electeurs/save/", save_electeurs),
    path("electeurs/verifier/", verifier_electeur),
    path('', include(router.urls)),  # router après les routes personnalisées
]
