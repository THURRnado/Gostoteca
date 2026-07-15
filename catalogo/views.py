from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ItemForm
from .mixins import DonoOuAdminMixin
from .models import Item


class ItemListView(LoginRequiredMixin, ListView):
    model = Item


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, DonoOuAdminMixin, UpdateView):
    model = Item
    form_class = ItemForm


class ItemDeleteView(LoginRequiredMixin, DonoOuAdminMixin, DeleteView):
    model = Item
    success_url = reverse_lazy('catalogo:lista')
