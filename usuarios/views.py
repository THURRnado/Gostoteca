from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView

from catalogo.models import Review

from .forms import UsuarioCreationForm


class CadastroView(CreateView):
    form_class = UsuarioCreationForm
    template_name = 'usuarios/cadastro.html'
    success_url = reverse_lazy('login')


class ContaDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'usuarios/conta_confirm_delete.html'
    success_url = reverse_lazy('login')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['meus_itens'] = self.request.user.itens.count()
        contexto['reviews_de_terceiros'] = (
            Review.objects.filter(item__criado_por=self.request.user)
            .exclude(usuario=self.request.user)
            .count()
        )
        return contexto

    def form_valid(self, form):
        usuario = self.request.user
        logout(self.request)
        usuario.delete()
        return HttpResponseRedirect(self.get_success_url())
