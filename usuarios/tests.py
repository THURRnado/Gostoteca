from django.contrib.auth import get_user_model
from django.test import TestCase

from catalogo.models import Item, Review

from .forms import UsuarioCreationForm

Usuario = get_user_model()

DADOS_VALIDOS = {
    'username': 'arthur',
    'email': 'arthur@example.com',
    'password1': 'senha-forte-123',
    'password2': 'senha-forte-123',
}


class RaizTest(TestCase):
    def test_anonimo_na_raiz_cai_no_login(self):
        resposta = self.client.get('/')

        self.assertRedirects(resposta, '/login/')

    def test_logado_na_raiz_segue_ate_o_catalogo(self):
        Usuario.objects.create_user(
            username='arthur', email='arthur@example.com', password='senha-forte-123'
        )
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.get('/', follow=True)

        # A raiz manda para /login/, que por sua vez manda o usuario ja
        # autenticado para o catalogo (redirect_authenticated_user=True).
        self.assertRedirects(resposta, '/catalogo/')


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


class LogoutViewTest(TestCase):
    def setUp(self):
        Usuario.objects.create_user(
            username='arthur',
            email='arthur@example.com',
            password='senha-forte-123',
        )
        self.client.login(username='arthur', password='senha-forte-123')

    def test_logout_por_post_encerra_sessao_e_redireciona_para_login(self):
        resposta = self.client.post('/logout/')

        self.assertRedirects(resposta, '/login/')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_por_get_retorna_405(self):
        resposta = self.client.get('/logout/')

        self.assertEqual(resposta.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)


class ContaDeleteViewTest(TestCase):
    def setUp(self):
        self.arthur = Usuario.objects.create_user(
            username='arthur', email='arthur@example.com', password='senha-forte-123'
        )
        self.andre = Usuario.objects.create_user(
            username='andre', email='andre@example.com', password='senha-forte-123'
        )
        self.item_do_arthur = Item.objects.create(
            titulo='Hollow Knight', tipo=Item.Tipo.JOGO, ano=2017, criado_por=self.arthur
        )
        self.review_do_andre = Review.objects.create(
            usuario=self.andre, item=self.item_do_arthur, nota=8
        )

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get('/conta/excluir/')

        self.assertRedirects(resposta, '/login/?next=/conta/excluir/')

    def test_confirmacao_mostra_os_numeros_do_estrago(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.get('/conta/excluir/')

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context['meus_itens'], 1)
        self.assertEqual(resposta.context['reviews_de_terceiros'], 1)

    def test_post_apaga_a_conta_e_encerra_a_sessao(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.post('/conta/excluir/')

        self.assertRedirects(resposta, '/login/')
        self.assertFalse(Usuario.objects.filter(username='arthur').exists())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_exclusao_leva_itens_e_reviews_de_terceiros_em_cascata(self):
        self.client.login(username='arthur', password='senha-forte-123')

        self.client.post('/conta/excluir/')

        self.assertFalse(Item.objects.filter(pk=self.item_do_arthur.pk).exists())
        self.assertFalse(Review.objects.filter(pk=self.review_do_andre.pk).exists())
        self.assertTrue(Usuario.objects.filter(username='andre').exists())
