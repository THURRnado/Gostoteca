from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # A raiz e a porta de entrada: manda para o login. Quem ja esta autenticado
    # e devolvido de la para o catalogo, pelo redirect_authenticated_user da LoginView.
    path('', RedirectView.as_view(pattern_name='login'), name='raiz'),
    path('catalogo/', include('catalogo.urls')),
    path('', include('usuarios.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
