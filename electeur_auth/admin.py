from django.contrib import admin
from .models import ElecteurAuth

@admin.register(ElecteurAuth)
class ElecteurAuthAdmin(admin.ModelAdmin):
    list_display = ('id','electeur','is_identifiant_valid','is_facial_valid','is_valid','date_auth','expired_at')
    readonly_fields = ('electeur','is_identifiant_valid','is_facial_valid','is_valid','date_auth','expired_at','otp_hash')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
