from django.contrib.auth import get_user_model
from django.test import TestCase

from .forms import UsuarioCreationForm

Usuario = get_user_model()

DADOS_VALIDOS = {
    'username': 'arthur',
    'email': 'arthur@example.com',
    'password1': 'senha-forte-123',
    'password2': 'senha-forte-123',
}


class UsuarioCreationFormTest(TestCase):
    def test_form_valido_cria_usuario_com_senha_hasheada(self):
        form = UsuarioCreationForm(data=DADOS_VALIDOS)
        self.assertTrue(form.is_valid(), form.errors)

        usuario = form.save()

        self.assertEqual(usuario.username, 'arthur')
        self.assertEqual(usuario.email, 'arthur@example.com')
        self.assertNotEqual(usuario.password, 'senha-forte-123')
        self.assertTrue(usuario.check_password('senha-forte-123'))

    def test_email_vazio_invalida_o_form(self):
        dados = DADOS_VALIDOS | {'email': ''}

        form = UsuarioCreationForm(data=dados)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertFalse(Usuario.objects.exists())

    def test_email_duplicado_invalida_o_form(self):
        Usuario.objects.create_user(
            username='andre',
            email='arthur@example.com',
            password='outra-senha-456',
        )

        form = UsuarioCreationForm(data=DADOS_VALIDOS)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(Usuario.objects.count(), 1)
