from django.contrib import admin

from public_apps.merchant.models import Merchant
from .models import User
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_platform_admin', 'is_staff', 'is_superuser')
    list_filter = ('is_platform_admin', 'is_staff', 'is_superuser')
    search_fields = ('email',)
    
    def get_queryset(self, request):
        """Filter users based on tenant"""
        qs = super().get_queryset(request)
        if request.user.is_platform_admin:
            return qs
        return qs.filter(tenant=request.tenant)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restrict tenant choice in forms"""
        if db_field.name == "merchant" and not request.user.is_platform_admin:
            kwargs["queryset"] = Merchant.objects.filter(id=request.tenant)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    


