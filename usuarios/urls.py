from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path(
        'login/',
        LoginView.as_view(
            template_name='usuarios/login.html',
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('cadastro/', views.CadastroView.as_view(), name='cadastro'),
]
