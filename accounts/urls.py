from django.urls import path
from .views import RegisterView, LoginView, ProfileView, LogoutView, FacialAuthView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('face-auth/', FacialAuthView.as_view(), name='face-auth'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
