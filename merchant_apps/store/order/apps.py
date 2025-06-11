import oscar.apps.order.apps as apps


class OrderConfig(apps.OrderConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'merchant_apps.store.order'
    label = 'order'
    verbose_name = 'Store Order Management'

   
