from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Usuario

CLASSES_INPUT = (
    'w-full rounded-lg border border-ambar/40 bg-white px-3 py-2 text-cacau '
    'placeholder-ferrugem/40 focus:border-ferrugem focus:outline-none '
    'focus:ring-2 focus:ring-mel/40'
)


class FormEstilizado:
    """Aplica as classes do Tailwind nos widgets, que o Django renderiza sem classe."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs['class'] = CLASSES_INPUT


class UsuarioCreationForm(FormEstilizado, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'email')


class LoginForm(FormEstilizado, AuthenticationForm):
    pass
