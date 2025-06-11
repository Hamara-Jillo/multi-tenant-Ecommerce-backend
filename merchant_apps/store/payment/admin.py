from oscar.apps.payment.admin import *  

# merchant_apps/store/payment/admin.py
from django.contrib import admin
from oscar.apps.payment.admin import SourceAdmin as CoreSourceAdmin
from .models import Source as StoreSource, Transaction as StoreTransaction, SourceType as StoreSourceType

class SourceAdmin(CoreSourceAdmin):
    list_display = ('id', 'store', 'currency', 'amount_allocated')
    list_filter = ('store',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_platform_admin:
            return qs.filter(store__merchant=request.tenant)
        return qs

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'source', 'amount', 'txn_type')
    list_filter = ('source__store',)

class SourceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

admin.site.unregister(Source) 
admin.site.unregister(Transaction)  # Unregister Oscar's default
admin.site.unregister(SourceType)  # Unregister Oscar's default
admin.site.register(StoreSource, SourceAdmin)
admin.site.register(StoreTransaction, TransactionAdmin)
admin.site.register(StoreSourceType, SourceTypeAdmin)