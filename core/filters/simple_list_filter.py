from django.contrib.admin import SimpleListFilter

class StoreFilter(SimpleListFilter):
    title = 'Store'
    parameter_name = 'store'

    def lookups(self, request, model_admin):
        # Assuming request.tenant has a list of stores, or adjust accordingly
        # Here we are assuming the filtering should be by the parent's store ID.
        stores = set()
        for obj in model_admin.get_queryset(request):
            # Collect store info from parent relationship.
            store = getattr(obj.shippingmethod_ptr, 'store', None)
            if store:
                stores.add((store.id, store.name))
        return list(stores)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(shippingmethod_ptr__store_id=self.value())
        return queryset

class EnabledFilter(SimpleListFilter):
    title = 'Enabled'
    parameter_name = 'enabled'

    def lookups(self, request, model_admin):
        return (('True', 'Yes'), ('False', 'No'))

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.filter(shippingmethod_ptr__enabled=True)
        if self.value() == 'False':
            return queryset.filter(shippingmethod_ptr__enabled=False)
        return queryset
