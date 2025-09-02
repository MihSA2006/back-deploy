from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('electeurs.urls')),
    path('api/elections/', include('elections.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/auth-electeur/', include('electeur_auth.urls')),
    path('api/votes/', include('vote.urls')),
]

# Pour servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)