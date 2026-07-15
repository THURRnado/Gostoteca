from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ItemForm, ReviewForm
from .mixins import DonoMixin, DonoOuAdminMixin
from .models import Item, Review


class ItemListView(LoginRequiredMixin, ListView):
    model = Item

    def get_queryset(self):
        return super().get_queryset().annotate(num_reviews=Count('reviews'))


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['reviews'] = self.object.reviews.select_related('usuario')
        contexto['minha_review'] = self.object.reviews.filter(usuario=self.request.user).first()
        return contexto


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


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'catalogo/review_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.item = get_object_or_404(Item, pk=kwargs['item_pk'])

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            existente = Review.objects.filter(usuario=request.user, item=self.item).first()
            if existente:
                return redirect('catalogo:review_editar', pk=existente.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['item'] = self.item
        return contexto

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        form.instance.item = self.item
        return super().form_valid(form)

    def get_success_url(self):
        return self.item.get_absolute_url()


class ReviewUpdateView(LoginRequiredMixin, DonoMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'catalogo/review_form.html'
    campo_dono = 'usuario'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['item'] = self.object.item
        return contexto

    def get_success_url(self):
        return self.object.item.get_absolute_url()


class ReviewDeleteView(LoginRequiredMixin, DonoOuAdminMixin, DeleteView):
    model = Review
    template_name = 'catalogo/review_confirm_delete.html'
    campo_dono = 'usuario'

    def get_success_url(self):
        return self.object.item.get_absolute_url()
