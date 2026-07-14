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


class LoginViewTest(TestCase):
    def setUp(self):
        Usuario.objects.create_user(
            username='arthur',
            email='arthur@example.com',
            password='senha-forte-123',
        )

    def test_get_login_retorna_200(self):
        resposta = self.client.get('/login/')

        self.assertEqual(resposta.status_code, 200)

    def test_login_valido_redireciona_para_catalogo(self):
        resposta = self.client.post(
            '/login/',
            data={'username': 'arthur', 'password': 'senha-forte-123'},
        )

        # Sem assertRedirects: /catalogo/ ainda nao existe e seria um 404.
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.url, '/catalogo/')
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_invalido_retorna_200_sem_criar_sessao(self):
        resposta = self.client.post(
            '/login/',
            data={'username': 'arthur', 'password': 'senha-errada'},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)


class CadastroViewTest(TestCase):
    def test_get_cadastro_retorna_200(self):
        resposta = self.client.get('/cadastro/')

        self.assertEqual(resposta.status_code, 200)

    def test_post_valido_cria_usuario_e_redireciona_para_login(self):
        resposta = self.client.post('/cadastro/', data=DADOS_VALIDOS)

        self.assertRedirects(resposta, '/login/')
        self.assertTrue(Usuario.objects.filter(username='arthur').exists())
