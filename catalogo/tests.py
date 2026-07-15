import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .models import Item

Usuario = get_user_model()


def cria_usuario(username='arthur', **extra):
    return Usuario.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='senha-forte-123',
        **extra,
    )


class ItemModelTest(TestCase):
    def setUp(self):
        self.usuario = cria_usuario()

    def test_str_mostra_titulo_e_ano(self):
        item = Item.objects.create(
            titulo='Hollow Knight',
            tipo=Item.Tipo.JOGO,
            ano=2017,
            criado_por=self.usuario,
        )

        self.assertEqual(str(item), 'Hollow Knight (2017)')

    def test_campos_opcionais_nascem_vazios(self):
        item = Item.objects.create(
            titulo='Duna',
            tipo=Item.Tipo.LIVRO,
            ano=1965,
            criado_por=self.usuario,
        )

        self.assertEqual(item.criador, '')
        self.assertEqual(item.descricao, '')
        self.assertFalse(item.capa)

    def test_tipo_fora_do_enum_e_rejeitado(self):
        item = Item(
            titulo='Revista Veja',
            tipo='revista',
            ano=2020,
            criado_por=self.usuario,
        )

        with self.assertRaises(ValidationError):
            item.full_clean()


class ItemListViewTest(TestCase):
    def setUp(self):
        self.usuario = cria_usuario()
        Item.objects.create(
            titulo='Hollow Knight',
            tipo=Item.Tipo.JOGO,
            ano=2017,
            criado_por=self.usuario,
        )

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get('/catalogo/')

        self.assertRedirects(resposta, '/login/?next=/catalogo/')

    def test_logado_ve_a_lista_com_os_itens(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.get('/catalogo/')

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Hollow Knight')


class ItemDetailViewTest(TestCase):
    def setUp(self):
        self.usuario = cria_usuario()
        self.item = Item.objects.create(
            titulo='Duna',
            tipo=Item.Tipo.LIVRO,
            ano=1965,
            descricao='Um planeta deserto e muita especiaria.',
            criado_por=self.usuario,
        )

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(f'/catalogo/{self.item.pk}/')

        self.assertRedirects(resposta, f'/login/?next=/catalogo/{self.item.pk}/')

    def test_logado_ve_o_detalhe(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.get(f'/catalogo/{self.item.pk}/')

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Um planeta deserto e muita especiaria.')

    def test_item_inexistente_retorna_404(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.get('/catalogo/9999/')

        self.assertEqual(resposta.status_code, 404)


def imagem_de_teste(nome='capa.png'):
    buffer = BytesIO()
    Image.new('RGB', (1, 1), 'red').save(buffer, format='PNG')
    return SimpleUploadedFile(nome, buffer.getvalue(), content_type='image/png')


DADOS_ITEM = {
    'titulo': 'Hollow Knight',
    'tipo': 'jogo',
    'ano': 2017,
    'criador': 'Team Cherry',
    'descricao': 'Metroidvania sobre insetos.',
}


class ItemCreateViewTest(TestCase):
    def setUp(self):
        self.usuario = cria_usuario()

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get('/catalogo/novo/')

        self.assertRedirects(resposta, '/login/?next=/catalogo/novo/')

    def test_logado_ve_o_formulario(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.get('/catalogo/novo/')

        self.assertEqual(resposta.status_code, 200)

    def test_item_criado_pertence_ao_usuario_logado(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.post('/catalogo/novo/', data=DADOS_ITEM)

        item = Item.objects.get(titulo='Hollow Knight')
        self.assertEqual(item.criado_por, self.usuario)
        self.assertRedirects(resposta, f'/catalogo/{item.pk}/')

    def test_criado_por_do_post_e_ignorado(self):
        outro = cria_usuario('andre')
        self.client.login(username='arthur', password='senha-forte-123')

        self.client.post('/catalogo/novo/', data=DADOS_ITEM | {'criado_por': outro.pk})

        item = Item.objects.get(titulo='Hollow Knight')
        self.assertEqual(item.criado_por, self.usuario)

    def test_tipo_invalido_nao_cria_item(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.post('/catalogo/novo/', data=DADOS_ITEM | {'tipo': 'revista'})

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Item.objects.exists())

    def test_titulo_vazio_nao_cria_item(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.post('/catalogo/novo/', data=DADOS_ITEM | {'titulo': ''})

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Item.objects.exists())


class ItemUploadTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_temp = tempfile.mkdtemp()
        cls.override = override_settings(MEDIA_ROOT=cls.media_temp)
        cls.override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.override.disable()
        shutil.rmtree(cls.media_temp, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cria_usuario()
        self.client.login(username='arthur', password='senha-forte-123')

    def test_upload_de_capa_grava_o_arquivo(self):
        self.client.post('/catalogo/novo/', data=DADOS_ITEM | {'capa': imagem_de_teste()})

        item = Item.objects.get(titulo='Hollow Knight')
        self.assertTrue(item.capa)
        self.assertIn('capas/', item.capa.name)

    def test_arquivo_que_nao_e_imagem_e_rejeitado(self):
        arquivo = SimpleUploadedFile('virus.png', b'isto nao e uma imagem', content_type='image/png')

        resposta = self.client.post('/catalogo/novo/', data=DADOS_ITEM | {'capa': arquivo})

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Item.objects.exists())


class ItemUpdateViewTest(TestCase):
    def setUp(self):
        self.dono = cria_usuario('arthur')
        self.outro = cria_usuario('andre')
        self.admin = cria_usuario('chefe', is_staff=True)
        self.item = Item.objects.create(
            titulo='Hollow Knight',
            tipo=Item.Tipo.JOGO,
            ano=2017,
            criado_por=self.dono,
        )
        self.url = f'/catalogo/{self.item.pk}/editar/'

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(resposta, f'/login/?next={self.url}')

    def test_dono_edita_o_proprio_item(self):
        self.client.login(username='arthur', password='senha-forte-123')

        self.client.post(self.url, data=DADOS_ITEM | {'titulo': 'Silksong'})

        self.item.refresh_from_db()
        self.assertEqual(self.item.titulo, 'Silksong')

    def test_admin_edita_item_alheio(self):
        self.client.login(username='chefe', password='senha-forte-123')

        self.client.post(self.url, data=DADOS_ITEM | {'titulo': 'Corrigido pelo admin'})

        self.item.refresh_from_db()
        self.assertEqual(self.item.titulo, 'Corrigido pelo admin')

    def test_outro_usuario_recebe_403(self):
        self.client.login(username='andre', password='senha-forte-123')

        resposta = self.client.post(self.url, data=DADOS_ITEM | {'titulo': 'Vandalizado'})

        self.assertEqual(resposta.status_code, 403)
        self.item.refresh_from_db()
        self.assertEqual(self.item.titulo, 'Hollow Knight')


class ItemDeleteViewTest(TestCase):
    def setUp(self):
        self.dono = cria_usuario('arthur')
        self.outro = cria_usuario('andre')
        self.admin = cria_usuario('chefe', is_staff=True)
        self.item = Item.objects.create(
            titulo='Hollow Knight',
            tipo=Item.Tipo.JOGO,
            ano=2017,
            criado_por=self.dono,
        )
        self.url = f'/catalogo/{self.item.pk}/excluir/'

    def test_dono_exclui_o_proprio_item(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.post(self.url)

        self.assertRedirects(resposta, '/catalogo/')
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_admin_exclui_item_alheio(self):
        self.client.login(username='chefe', password='senha-forte-123')

        self.client.post(self.url)

        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_outro_usuario_recebe_403(self):
        self.client.login(username='andre', password='senha-forte-123')

        resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())
