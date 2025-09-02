from django.urls import path
from .views import StartAuthView, FaceAuthView, VerifyOTPView, DeleteAuthSessionView

urlpatterns = [
    path('start/', StartAuthView.as_view(), name='electeur-auth-start'),
    path('face/', FaceAuthView.as_view(), name='electeur-auth-face'),
    path('verify-otp/', VerifyOTPView.as_view(), name='electeur-auth-verify'),
    path("delete/<int:id>/", DeleteAuthSessionView.as_view(), name="delete_auth_session"),
]