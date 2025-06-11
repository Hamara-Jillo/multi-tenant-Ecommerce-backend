from oscar.apps.order.utils import OrderCreator
from django.utils.deprecation import MiddlewareMixin

class TenantOrderCreator(OrderCreator):
    def create_order(self, user, basket, **kwargs):
        order = super().create_order(user, basket, **kwargs)
        order.store = basket.store  # Assuming basket is tenant-scoped
        order.save()
        return order

class OrderCreatorMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.order_creator = TenantOrderCreator()