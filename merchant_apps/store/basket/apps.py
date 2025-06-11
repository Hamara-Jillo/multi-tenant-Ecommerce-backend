import oscar.apps.basket.apps as apps
from django.urls import path

class BasketConfig(apps.BasketConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'merchant_apps.store.basket'
    label = 'basket'
    verbose_name = 'Store Basket Management'

    def ready(self):
        # Disable Oscar's receivers by not calling super()
        pass  # Remove Oscar's StockAlert signal handlers

    def get_urls(self):
        from . import views
        urls = [
            path('', views.BasketView.as_view(), name='summary'),
            path('add/<int:pk>/', views.BasketAddView.as_view(), name='add'),
            path('vouchers/add/', views.VoucherAddView.as_view(), name='vouchers-add'),
            path('vouchers/<int:pk>/remove/', views.VoucherRemoveView.as_view(), name='vouchers-remove'),
            path('saved/', views.SavedBasketListView.as_view(), name='saved-basket-list'),
            path('saved/<int:pk>/', views.SavedBasketDetailView.as_view(), name='saved-basket-detail'),
            path('saved/<int:pk>/delete/', views.SavedBasketDeleteView.as_view(), name='saved-basket-delete'),
            path('saved/create/', views.SavedBasketCreateView.as_view(), name='saved-basket-create'),
        ]
        return self.post_process_urls(urls)
