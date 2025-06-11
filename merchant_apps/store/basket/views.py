from django.views.generic import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

class BasketView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('basket:summary'))

class BasketAddView(View):
    def post(self, request, *args, **kwargs):
        messages.info(request, _("Product added to basket"))
        return HttpResponseRedirect(reverse('basket:summary'))

class BasketRemoveView(View):
    def post(self, request, *args, **kwargs):
        messages.info(request, _("Product removed from basket"))
        return HttpResponseRedirect(reverse('basket:summary'))

class VoucherAddView(View):
    def post(self, request, *args, **kwargs):
        messages.info(request, _("Voucher added"))
        return HttpResponseRedirect(reverse('basket:summary'))

class VoucherRemoveView(View):
    def post(self, request, *args, **kwargs):
        messages.info(request, _("Voucher removed"))
        return HttpResponseRedirect(reverse('basket:summary'))

class SavedBasketListView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('basket:summary'))

class SavedBasketDetailView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('basket:summary'))

class SavedBasketCreateView(View):
    def post(self, request, *args, **kwargs):
        messages.info(request, _("Basket saved"))
        return HttpResponseRedirect(reverse('basket:summary'))

class SavedBasketDeleteView(View):
    def post(self, request, *args, **kwargs):
        messages.info(request, _("Saved basket deleted"))
        return HttpResponseRedirect(reverse('basket:summary')) 