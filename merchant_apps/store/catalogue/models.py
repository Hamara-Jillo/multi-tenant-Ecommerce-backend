from django.db import models
from oscar.apps.catalogue.abstract_models import (
    AbstractProduct, AbstractProductClass, AbstractCategory,
    AbstractProductAttribute, AbstractOption, AbstractProductAttributeValue,
    AbstractProductImage, AbstractProductRecommendation, AbstractAttributeOption,
    AbstractAttributeOptionGroup, AbstractProductCategory
)
from merchant_apps.store.meta.models import Store

class Product(AbstractProduct):
    store = models.ForeignKey(
        Store, 
        on_delete=models.CASCADE,
        related_name='catalogue_products',
        verbose_name='Store',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('store', 'upc')] 
        app_label = 'catalogue'

    def save(self, *args, **kwargs):
        if not self.store and hasattr(self, 'request'):
            pass
        super().save(*args, **kwargs)

class ProductClass(AbstractProductClass):
    store = models.ForeignKey(
        'store_meta.Store',
        on_delete=models.CASCADE,
        related_name='product_classes',
        null=True,
        blank=True,
    )

class Category(AbstractCategory):
    store = models.ForeignKey(
        'store_meta.Store',
        on_delete=models.CASCADE,
        related_name='store_categories',
        verbose_name='Store',
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = [('store', 'slug')]
        verbose_name_plural = 'Categories'

class ProductAttribute(AbstractProductAttribute):
    store = models.ForeignKey(
        'store_meta.Store',
        on_delete=models.CASCADE,
        related_name='store_attributes',
        null=True,
        blank=True,
    )

class ProductAttributeValue(AbstractProductAttributeValue):
    value_boolean = models.BooleanField(null=True)

class ProductImage(AbstractProductImage):
    pass

class ProductRecommendation(AbstractProductRecommendation):
    pass

class AttributeOption(AbstractAttributeOption):
    pass

class AttributeOptionGroup(AbstractAttributeOptionGroup):
    pass

class ProductCategory(AbstractProductCategory):
    pass

class Option(AbstractOption):
    store = models.ForeignKey(
        'store_meta.Store',
        on_delete=models.CASCADE,
        related_name='store_options',
        null=True,
        blank=True,
    )

# Import remaining Oscar catalogue models
from oscar.apps.catalogue.models import *