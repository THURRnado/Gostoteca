from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import UsuarioCreationForm


class CadastroView(CreateView):
    form_class = UsuarioCreationForm
    template_name = 'usuarios/cadastro.html'
    success_url = reverse_lazy('login')
