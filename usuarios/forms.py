from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Usuario

CLASSES_INPUT = (
    'w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 '
    'placeholder-slate-400 focus:border-slate-900 focus:outline-none'
)


class _FormEstilizado:
    """Aplica as classes do Tailwind nos widgets, que o Django renderiza sem classe."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs['class'] = CLASSES_INPUT


class UsuarioCreationForm(_FormEstilizado, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'email')


class LoginForm(_FormEstilizado, AuthenticationForm):
    pass
