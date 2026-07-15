# Item e Catálogo — Plano de Implementação (fatia 1 de 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o modelo `Item` com listagem, detalhe e CRUD autorizado, fechando o critério "rotas protegidas exigem login" que ficou pendente da fatia de autenticação.

**Architecture:** Cinco CBVs do Django em `catalogo/views.py`. `LoginRequiredMixin` em todas; editar e excluir ganham também um `DonoOuAdminMixin(UserPassesTestMixin)` que entrega 403 para logado-não-dono e redirect para anônimo, sem configuração extra. O `criado_por` é preenchido no `form_valid`, nunca vindo do POST. A capa é upload real (`ImageField` + Pillow).

**Tech Stack:** Django 6.0.7, SQLite, Pillow, Tailwind CSS v4 (Play CDN), `manage.py test`.

**Referência:** [Spec aprovado](../specs/2026-07-14-catalogo-item-design.md)

---

## ⚠️ NÃO COMMITE

**O usuário cuida do git sozinho.** Este plano não tem passos de commit, e isso é deliberado — não é esquecimento. Não rode `git add`, `git commit`, `git branch` ou qualquer outro comando de git. Deixe todas as alterações no working tree.

## Notas de contexto para quem implementar

- **Rodar tudo de dentro de `Gostoteca/`** (onde está o `manage.py`), com o Python da venv: `.\venv\Scripts\python.exe`. Windows/PowerShell.
- **O app `catalogo` está vazio** — só o esqueleto do `startapp`. Já está em `INSTALLED_APPS`.
- **O app `usuarios` está pronto** e tem 10 testes passando. Várias tasks aqui mexem nele; **se algum dos 10 quebrar, conserte antes de seguir**.
- **`admin` significa `is_staff`**, não Group e não `is_superuser`. Decisão registrada no spec.
- **`AnonymousUser.is_staff` é `False`** e `item.criado_por == AnonymousUser()` é `False`, então o `DonoOuAdminMixin` não explode com anônimo — mas o `LoginRequiredMixin` vem antes na MRO e o intercepta primeiro, evitando a ida ao banco.
- **Cuidado com `NoReverseMatch`:** um `{% url 'catalogo:lista' %}` em template só é seguro depois que a rota existir (Task 3). Foi exatamente essa a armadilha na fatia anterior.

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `templates/base.html` (criar; sai de `usuarios/`) | Layout do site: HTML externo, Tailwind, cabeçalho |
| `templates/_campo.html` (criar; sai de `usuarios/`) | Renderização de um campo de formulário |
| `catalogo/models.py` (modificar) | Modelo `Item` |
| `catalogo/mixins.py` (criar) | `DonoOuAdminMixin` — reusado nas fatias 2 e 3 |
| `catalogo/forms.py` (criar) | `ItemForm` |
| `catalogo/views.py` (modificar) | As cinco CBVs |
| `catalogo/urls.py` (criar) | As cinco rotas, com `app_name` |
| `catalogo/templates/catalogo/` (criar) | `item_list`, `item_detail`, `item_form`, `item_confirm_delete` |
| `catalogo/tests.py` (modificar) | Os testes |
| `usuarios/forms.py` (modificar) | `_FormEstilizado` → `FormEstilizado` |
| `usuarios/templates/usuarios/login.html`, `cadastro.html` (modificar) | Novos caminhos de `extends`/`include` |
| `gostoteca/settings.py` (modificar) | `DIRS`, `LOGIN_REDIRECT_URL` |
| `gostoteca/urls.py` (modificar) | `include` do catálogo, `static()` para media |
| `requirements.txt` (modificar) | Pillow |

---

## Task 1: Preparação — Pillow, templates compartilhados e rename do mixin

Refatoração pura, sem funcionalidade nova. O critério de sucesso é **os 10 testes existentes continuarem passando**.

**Files:**
- Create: `templates/base.html`, `templates/_campo.html`
- Delete: `usuarios/templates/usuarios/base.html`, `usuarios/templates/usuarios/_campo.html`
- Modify: `requirements.txt`, `gostoteca/settings.py`, `usuarios/forms.py`, `usuarios/templates/usuarios/login.html`, `usuarios/templates/usuarios/cadastro.html`

- [ ] **Step 1: Confirmar o ponto de partida**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 10 tests` / `OK`

Se não for 10/10, pare e reporte — a base não está no estado esperado.

- [ ] **Step 2: Instalar o Pillow**

```powershell
.\venv\Scripts\python.exe -m pip install Pillow
.\venv\Scripts\python.exe -m pip freeze > requirements.txt
```

Confira que o `requirements.txt` resultante contém `Pillow` e **continua contendo** `Django`, `asgiref`, `sqlparse` e `tzdata`.

- [ ] **Step 3: Criar `templates/base.html`**

Crie a pasta `templates/` na raiz (ao lado do `manage.py`) e o arquivo `templates/base.html`:

```html
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block titulo %}Gostoteca{% endblock %}</title>
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
</head>
<body class="min-h-screen bg-slate-100">
  {% if user.is_authenticated %}
    <header class="flex items-center justify-end gap-4 bg-white px-6 py-3 shadow-sm">
      <span class="text-sm text-slate-600">{{ user.username }}</span>
      <form method="post" action="{% url 'logout' %}">
        {% csrf_token %}
        <button type="submit" class="text-sm font-medium text-slate-900 underline">Sair</button>
      </form>
    </header>
  {% endif %}

  {% block conteudo %}{% endblock %}
</body>
</html>
```

**Diferença em relação ao arquivo antigo:** a `<div class="flex items-center justify-center p-4">` que envolvia o `{% block conteudo %}` **saiu**. Ela centraliza vertical e horizontalmente, o que é certo para o card de login mas errado para uma lista de catálogo, que quer largura total e alinhamento ao topo. Cada página passa a trazer o próprio wrapper de layout (Steps 6 e 7).

Ainda **sem** link para o catálogo no cabeçalho: a rota `catalogo:lista` só existe na Task 3, e um `{% url %}` aqui estouraria `NoReverseMatch` em todas as páginas.

- [ ] **Step 4: Criar `templates/_campo.html`**

```html
<div>
  <label for="{{ campo.id_for_label }}" class="block text-sm font-medium text-slate-700 mb-1">
    {{ campo.label }}
  </label>
  {{ campo }}
  {% if campo.help_text %}
    <div class="mt-1 text-xs text-slate-500">{{ campo.help_text|safe }}</div>
  {% endif %}
  {% for erro in campo.errors %}
    <p class="mt-1 text-sm text-red-600">{{ erro }}</p>
  {% endfor %}
</div>
```

Conteúdo idêntico ao antigo. O `<div>` (não `<p>`) no help_text é proposital — o help_text do `password1` é uma `<ul>`, e `<ul>` dentro de `<p>` é HTML inválido. **Não "conserte" isso.**

- [ ] **Step 5: Apagar os templates antigos e configurar o DIRS**

Apague `usuarios/templates/usuarios/base.html` e `usuarios/templates/usuarios/_campo.html`.

Em `gostoteca/settings.py`, na lista `TEMPLATES`, troque `'DIRS': [],` por:

```python
        'DIRS': [BASE_DIR / 'templates'],
```

`BASE_DIR` já está definido no topo do arquivo. `APP_DIRS: True` continua como está — os templates de app (`login.html`, `cadastro.html`) seguem sendo encontrados normalmente.

- [ ] **Step 6: Atualizar `usuarios/templates/usuarios/login.html`**

Substitua todo o conteúdo por:

```html
{% extends 'base.html' %}

{% block titulo %}Entrar — Gostoteca{% endblock %}

{% block conteudo %}
<div class="flex items-center justify-center p-4">
  <main class="w-full max-w-sm bg-white rounded-xl shadow-sm p-8">
    <h1 class="text-2xl font-semibold text-slate-900 mb-6">Entrar</h1>

    {% if form.non_field_errors %}
      <div class="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
        {% for erro in form.non_field_errors %}<p>{{ erro }}</p>{% endfor %}
      </div>
    {% endif %}

    <form method="post" class="space-y-4">
      {% csrf_token %}
      {% for campo in form %}{% include '_campo.html' %}{% endfor %}
      <button type="submit"
              class="w-full rounded-lg bg-slate-900 py-2 font-medium text-white hover:bg-slate-700">
        Entrar
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-slate-600">
      Não tem conta? <a href="{% url 'cadastro' %}" class="text-slate-900 underline">Cadastre-se</a>
    </p>
  </main>
</div>
{% endblock %}
```

Mudou: `extends 'usuarios/base.html'` → `'base.html'`; `include 'usuarios/_campo.html'` → `'_campo.html'`; e o `<main>` ganhou a `<div>` de centralização que saiu do `base.html`.

- [ ] **Step 7: Atualizar `usuarios/templates/usuarios/cadastro.html`**

Substitua todo o conteúdo por:

```html
{% extends 'base.html' %}

{% block titulo %}Criar conta — Gostoteca{% endblock %}

{% block conteudo %}
<div class="flex items-center justify-center p-4">
  <main class="w-full max-w-sm bg-white rounded-xl shadow-sm p-8">
    <h1 class="text-2xl font-semibold text-slate-900 mb-6">Criar conta</h1>

    <form method="post" class="space-y-4">
      {% csrf_token %}
      {% for campo in form %}{% include '_campo.html' %}{% endfor %}
      <button type="submit"
              class="w-full rounded-lg bg-slate-900 py-2 font-medium text-white hover:bg-slate-700">
        Cadastrar
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-slate-600">
      Já tem conta? <a href="{% url 'login' %}" class="text-slate-900 underline">Entrar</a>
    </p>
  </main>
</div>
{% endblock %}
```

- [ ] **Step 8: Renomear o mixin em `usuarios/forms.py`**

Substitua todo o conteúdo por:

```python
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Usuario

CLASSES_INPUT = (
    'w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 '
    'placeholder-slate-400 focus:border-slate-900 focus:outline-none'
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
```

Única mudança: o underscore saiu de `_FormEstilizado`, porque o `catalogo/forms.py` vai importá-lo na Task 4.

- [ ] **Step 9: Verificar que nada regrediu**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 10 tests` / `OK`

Run: `.\venv\Scripts\python.exe manage.py check`
Expected: `System check identified no issues (0 silenced).`

**Esta task não adiciona testes.** Ela é refatoração, e a rede de segurança são os 10 que já existem. Se algum falhar com `TemplateDoesNotExist`, o `DIRS` do Step 5 ou os caminhos dos Steps 6/7 estão errados.

---

## Task 2: Modelo `Item`

**Files:**
- Modify: `catalogo/models.py`, `catalogo/tests.py`
- Create: `catalogo/migrations/0001_initial.py` (gerado)

- [ ] **Step 1: Escrever os testes que falham**

Substitua todo o conteúdo de `catalogo/tests.py` por:

```python
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

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
```

- [ ] **Step 2: Rodar para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test catalogo -v 2`
Expected: FAIL — `ImportError: cannot import name 'Item' from 'catalogo.models'`

- [ ] **Step 3: Escrever o modelo**

Substitua todo o conteúdo de `catalogo/models.py` por:

```python
from django.conf import settings
from django.db import models


class Item(models.Model):
    class Tipo(models.TextChoices):
        JOGO = 'jogo', 'Jogo'
        FILME = 'filme', 'Filme'
        LIVRO = 'livro', 'Livro'

    titulo = models.CharField('título', max_length=200)
    tipo = models.CharField('tipo', max_length=10, choices=Tipo.choices)
    ano = models.PositiveIntegerField('ano')
    criador = models.CharField('criador', max_length=200, blank=True)
    descricao = models.TextField('descrição', blank=True)
    capa = models.ImageField('capa', upload_to='capas/', blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='cadastrado por',
    )

    class Meta:
        ordering = ('titulo',)
        verbose_name = 'item'
        verbose_name_plural = 'itens'

    def __str__(self):
        return f'{self.titulo} ({self.ano})'
```

Use `settings.AUTH_USER_MODEL`, **nunca** importe o `Usuario` diretamente — é a forma correta de referenciar o modelo de usuário e evita import circular.

- [ ] **Step 4: Gerar e aplicar a migração**

```powershell
.\venv\Scripts\python.exe manage.py makemigrations catalogo
.\venv\Scripts\python.exe manage.py migrate
```

Expected: `Create model Item` e depois `Applying catalogo.0001_initial... OK`.

- [ ] **Step 5: Rodar para confirmar que passam**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 13 tests` / `OK` (10 do `usuarios` + 3 novos)

---

## Task 3: Lista e detalhe

Esta task fecha o critério **"rotas protegidas exigem login"** da Seção 5 do documento da atividade, pendente desde a fatia anterior.

**Files:**
- Create: `catalogo/urls.py`, `catalogo/templates/catalogo/item_list.html`, `catalogo/templates/catalogo/item_detail.html`
- Modify: `catalogo/views.py`, `catalogo/tests.py`, `gostoteca/urls.py`, `gostoteca/settings.py`, `templates/base.html`

- [ ] **Step 1: Escrever os testes que falham**

Acrescente ao final de `catalogo/tests.py`:

```python
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
```

O `test_anonimo_e_redirecionado_para_login` **é** o critério "rotas protegidas exigem login". Aqui `assertRedirects` pode ser usado: `/login/` existe e responde 200.

- [ ] **Step 2: Rodar para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test catalogo -v 2`
Expected: FAIL — 404, porque `/catalogo/` não existe.

- [ ] **Step 3: Escrever as views**

Substitua todo o conteúdo de `catalogo/views.py` por:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView

from .models import Item


class ItemListView(LoginRequiredMixin, ListView):
    model = Item


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item
```

A `ListView` procura `catalogo/item_list.html` e passa `object_list`; a `DetailView` procura `catalogo/item_detail.html` e passa `object`. Ambos os nomes são convenção do Django — por isso não precisamos declarar `template_name`.

- [ ] **Step 4: Criar `catalogo/urls.py`**

```python
from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.ItemListView.as_view(), name='lista'),
    path('<int:pk>/', views.ItemDetailView.as_view(), name='detalhe'),
]
```

O `app_name` cria o namespace, então as rotas são referenciadas como `catalogo:lista` e `catalogo:detalhe`.

- [ ] **Step 5: Incluir as rotas e servir os uploads**

Substitua todo o conteúdo de `gostoteca/urls.py` por:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('catalogo/', include('catalogo.urls')),
    path('', include('usuarios.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

O `static()` só funciona com `DEBUG=True` e existe para servir as capas em desenvolvimento. Sem ele, o upload grava o arquivo mas a imagem não aparece — sintoma que parece bug de upload e é roteamento.

- [ ] **Step 6: Apontar o `LOGIN_REDIRECT_URL` para a rota nomeada**

Em `gostoteca/settings.py`, no topo do arquivo, junto dos outros imports, acrescente:

```python
from django.urls import reverse_lazy
```

E troque a linha do `LOGIN_REDIRECT_URL` por:

```python
LOGIN_REDIRECT_URL = reverse_lazy('catalogo:lista')
```

Apague o comentário `# Caminho literal: o app catalogo ainda nao existe.` — a dívida técnica acabou de ser paga. **Precisa ser `reverse_lazy`, não `reverse`:** o `settings.py` é carregado antes das URLs, e o `reverse` tentaria resolver na hora do import, estourando.

**Atenção ao teste `test_login_valido_redireciona_para_catalogo` do `usuarios`**, que espera `resposta.url == '/catalogo/'`. Ele deve continuar passando: `reverse_lazy('catalogo:lista')` resolve para exatamente `/catalogo/`, graças ao prefixo do Step 5. Se ele falhar, o problema é o prefixo da rota — **não altere o teste para acomodar**.

- [ ] **Step 7: Criar `catalogo/templates/catalogo/item_list.html`**

```html
{% extends 'base.html' %}

{% block titulo %}Catálogo — Gostoteca{% endblock %}

{% block conteudo %}
<main class="mx-auto max-w-5xl p-6">
  <h1 class="mb-6 text-2xl font-semibold text-slate-900">Catálogo</h1>

  {% if object_list %}
    <ul class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {% for item in object_list %}
        <li class="rounded-xl bg-white p-4 shadow-sm">
          <a href="{% url 'catalogo:detalhe' item.pk %}" class="block">
            {% if item.capa %}
              <img src="{{ item.capa.url }}" alt="" class="mb-3 h-40 w-full rounded-lg object-cover">
            {% endif %}
            <h2 class="font-medium text-slate-900">{{ item.titulo }}</h2>
            <p class="text-sm text-slate-600">{{ item.get_tipo_display }} · {{ item.ano }}</p>
          </a>
        </li>
      {% endfor %}
    </ul>
  {% else %}
    <p class="text-slate-600">Nenhum item no catálogo ainda.</p>
  {% endif %}
</main>
{% endblock %}
```

`get_tipo_display` é gerado automaticamente pelo Django para qualquer campo com `choices` — mostra "Jogo" em vez de "jogo".

- [ ] **Step 8: Criar `catalogo/templates/catalogo/item_detail.html`**

```html
{% extends 'base.html' %}

{% block titulo %}{{ object.titulo }} — Gostoteca{% endblock %}

{% block conteudo %}
<main class="mx-auto max-w-3xl p-6">
  <a href="{% url 'catalogo:lista' %}" class="text-sm text-slate-600 underline">← Voltar ao catálogo</a>

  <article class="mt-4 rounded-xl bg-white p-6 shadow-sm">
    {% if object.capa %}
      <img src="{{ object.capa.url }}" alt="" class="mb-4 max-h-96 rounded-lg object-contain">
    {% endif %}

    <h1 class="text-2xl font-semibold text-slate-900">{{ object.titulo }}</h1>
    <p class="mt-1 text-sm text-slate-600">
      {{ object.get_tipo_display }} · {{ object.ano }}{% if object.criador %} · {{ object.criador }}{% endif %}
    </p>

    {% if object.descricao %}
      <p class="mt-4 text-slate-800">{{ object.descricao }}</p>
    {% endif %}

    <p class="mt-6 text-xs text-slate-500">Cadastrado por {{ object.criado_por }}</p>
  </article>
</main>
{% endblock %}
```

Ainda **sem** botões de editar/excluir — as rotas só existem na Task 5.

- [ ] **Step 9: Adicionar o link do catálogo no cabeçalho**

Em `templates/base.html`, dentro do `<header>`, **antes** do `<span>` com o username, acrescente:

```html
      <a href="{% url 'catalogo:lista' %}" class="mr-auto text-sm font-medium text-slate-900">Gostoteca</a>
```

Agora é seguro: a rota `catalogo:lista` passou a existir no Step 4. O `mr-auto` empurra o resto do cabeçalho para a direita.

- [ ] **Step 10: Rodar a suíte inteira**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 18 tests` / `OK` (10 do `usuarios` + 3 do modelo + 5 novos)

Run: `.\venv\Scripts\python.exe manage.py check`
Expected: `System check identified no issues (0 silenced).`

---

## Task 4: Criar item

**Files:**
- Create: `catalogo/forms.py`, `catalogo/templates/catalogo/item_form.html`
- Modify: `catalogo/views.py`, `catalogo/urls.py`, `catalogo/tests.py`, `catalogo/templates/catalogo/item_list.html`

- [ ] **Step 1: Escrever os testes que falham**

Primeiro, acrescente estes imports ao topo de `catalogo/tests.py`, junto dos que já existem:

```python
import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
```

Depois acrescente ao final do arquivo:

```python
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
```

**O `override_settings(MEDIA_ROOT=...)` não é opcional.** Sem ele os testes gravam arquivos de verdade na pasta `media/` do projeto e deixam lixo a cada execução, inclusive no CI. O `setUpClass`/`tearDownClass` cria e apaga um diretório temporário.

- [ ] **Step 2: Rodar para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test catalogo -v 2`
Expected: FAIL — 404 nos testes de `/catalogo/novo/`.

- [ ] **Step 3: Criar `catalogo/forms.py`**

```python
from django import forms

from usuarios.forms import FormEstilizado

from .models import Item


class ItemForm(FormEstilizado, forms.ModelForm):
    class Meta:
        model = Item
        fields = ('titulo', 'tipo', 'ano', 'criador', 'descricao', 'capa')
```

**`criado_por` não está em `fields`, e isso é de propósito.** A view o preenche a partir do `request.user`. Se estivesse no form, um POST forjado poderia atribuir a autoria a outra pessoa — é o que o `test_criado_por_do_post_e_ignorado` trava.

O `FormEstilizado` vem do app `usuarios`. O `catalogo` já depende dele pela FK de `criado_por`, então o import não cria acoplamento novo.

- [ ] **Step 4: Acrescentar a view**

Substitua todo o conteúdo de `catalogo/views.py` por:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView

from .forms import ItemForm
from .models import Item


class ItemListView(LoginRequiredMixin, ListView):
    model = Item


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        return super().form_valid(form)
```

A `CreateView` procura `catalogo/item_form.html` e redireciona para `get_absolute_url()` do objeto criado — que ainda não existe. O Step 5 resolve isso.

- [ ] **Step 5: Dar um `get_absolute_url` ao `Item`**

Em `catalogo/models.py`, acrescente o import no topo:

```python
from django.urls import reverse
```

E acrescente este método à classe `Item`, logo abaixo do `__str__`:

```python
    def get_absolute_url(self):
        return reverse('catalogo:detalhe', kwargs={'pk': self.pk})
```

Com isso a `CreateView` sabe para onde redirecionar depois de salvar, sem precisar de `success_url`. Não é migração — é só um método, o banco não muda.

- [ ] **Step 6: Registrar a rota**

Substitua todo o conteúdo de `catalogo/urls.py` por:

```python
from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.ItemListView.as_view(), name='lista'),
    path('novo/', views.ItemCreateView.as_view(), name='novo'),
    path('<int:pk>/', views.ItemDetailView.as_view(), name='detalhe'),
]
```

`novo/` vem **antes** de `<int:pk>/`. Como `novo` não é um inteiro, a ordem não causaria conflito aqui — mas manter as rotas literais antes das paramétricas é o hábito que evita bugs sutis quando o parâmetro é `<str:slug>`.

- [ ] **Step 7: Criar `catalogo/templates/catalogo/item_form.html`**

```html
{% extends 'base.html' %}

{% block titulo %}Novo item — Gostoteca{% endblock %}

{% block conteudo %}
<main class="mx-auto max-w-2xl p-6">
  <h1 class="mb-6 text-2xl font-semibold text-slate-900">Novo item</h1>

  <form method="post" enctype="multipart/form-data" class="space-y-4 rounded-xl bg-white p-6 shadow-sm">
    {% csrf_token %}
    {% for campo in form %}{% include '_campo.html' %}{% endfor %}
    <div class="flex gap-3">
      <button type="submit"
              class="rounded-lg bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-700">
        Salvar
      </button>
      <a href="{% url 'catalogo:lista' %}"
         class="rounded-lg px-4 py-2 font-medium text-slate-700 hover:bg-slate-200">Cancelar</a>
    </div>
  </form>
</main>
{% endblock %}
```

**O `enctype="multipart/form-data"` é obrigatório.** Sem ele o navegador manda só o nome do arquivo, não os bytes, e a capa nunca chega — silenciosamente, sem erro. É a causa mais comum de "meu upload não funciona" em Django.

- [ ] **Step 8: Adicionar o botão de novo item na lista**

Em `catalogo/templates/catalogo/item_list.html`, substitua a linha do `<h1>` por:

```html
  <div class="mb-6 flex items-center justify-between">
    <h1 class="text-2xl font-semibold text-slate-900">Catálogo</h1>
    <a href="{% url 'catalogo:novo' %}"
       class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">
      Novo item
    </a>
  </div>
```

- [ ] **Step 9: Rodar a suíte inteira**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 26 tests` / `OK` (18 anteriores + 8 novos)

---

## Task 5: Editar e excluir, com autorização

**Files:**
- Create: `catalogo/mixins.py`, `catalogo/templates/catalogo/item_confirm_delete.html`
- Modify: `catalogo/views.py`, `catalogo/urls.py`, `catalogo/tests.py`, `catalogo/templates/catalogo/item_detail.html`, `catalogo/templates/catalogo/item_form.html`

- [ ] **Step 1: Escrever os testes que falham**

Acrescente ao final de `catalogo/tests.py`:

```python
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
```

Os dois `test_outro_usuario_recebe_403` são o critério da Seção 6: "usuário comum recebe 403/redirecionamento nas rotas de admin". Repare que cada um verifica **também** que o dado não mudou — o 403 sozinho não provaria que a alteração foi barrada.

- [ ] **Step 2: Rodar para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test catalogo -v 2`
Expected: FAIL — 404, porque as rotas não existem.

- [ ] **Step 3: Criar `catalogo/mixins.py`**

```python
from django.contrib.auth.mixins import UserPassesTestMixin


class DonoOuAdminMixin(UserPassesTestMixin):
    """Libera o objeto para quem o criou e para quem tem is_staff.

    O handle_no_permission() do AccessMixin ja faz a distincao certa sozinho:
    levanta PermissionDenied (403) para usuario autenticado e redireciona
    anonimo para o login. Nao mexa em raise_exception.
    """

    def test_func(self):
        return self.get_object().criado_por == self.request.user or self.request.user.is_staff
```

- [ ] **Step 4: Acrescentar as views**

Substitua todo o conteúdo de `catalogo/views.py` por:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ItemForm
from .mixins import DonoOuAdminMixin
from .models import Item


class ItemListView(LoginRequiredMixin, ListView):
    model = Item


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, DonoOuAdminMixin, UpdateView):
    model = Item
    form_class = ItemForm


class ItemDeleteView(LoginRequiredMixin, DonoOuAdminMixin, DeleteView):
    model = Item
    success_url = reverse_lazy('catalogo:lista')
```

A ordem `LoginRequiredMixin, DonoOuAdminMixin` importa: o `LoginRequiredMixin.dispatch` roda primeiro e redireciona o anônimo **antes** de o `test_func` buscar o objeto no banco.

- [ ] **Step 5: Registrar as rotas**

Substitua todo o conteúdo de `catalogo/urls.py` por:

```python
from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.ItemListView.as_view(), name='lista'),
    path('novo/', views.ItemCreateView.as_view(), name='novo'),
    path('<int:pk>/', views.ItemDetailView.as_view(), name='detalhe'),
    path('<int:pk>/editar/', views.ItemUpdateView.as_view(), name='editar'),
    path('<int:pk>/excluir/', views.ItemDeleteView.as_view(), name='excluir'),
]
```

- [ ] **Step 6: Criar `catalogo/templates/catalogo/item_confirm_delete.html`**

```html
{% extends 'base.html' %}

{% block titulo %}Excluir {{ object.titulo }} — Gostoteca{% endblock %}

{% block conteudo %}
<main class="mx-auto max-w-md p-6">
  <div class="rounded-xl bg-white p-6 shadow-sm">
    <h1 class="text-xl font-semibold text-slate-900">Excluir item</h1>
    <p class="mt-3 text-slate-700">
      Tem certeza que quer excluir <strong>{{ object.titulo }}</strong>? Esta ação não pode ser desfeita.
    </p>

    <form method="post" class="mt-6 flex gap-3">
      {% csrf_token %}
      <button type="submit"
              class="rounded-lg bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-700">
        Excluir
      </button>
      <a href="{% url 'catalogo:detalhe' object.pk %}"
         class="rounded-lg px-4 py-2 font-medium text-slate-700 hover:bg-slate-200">Cancelar</a>
    </form>
  </div>
</main>
{% endblock %}
```

A `DeleteView` do Django exige POST para excluir — o GET só mostra esta confirmação.

- [ ] **Step 7: Mostrar os botões de editar e excluir no detalhe**

Em `catalogo/templates/catalogo/item_detail.html`, logo antes do `</article>`, acrescente:

```html
    {% if object.criado_por == user or user.is_staff %}
      <div class="mt-6 flex gap-3 border-t border-slate-200 pt-4">
        <a href="{% url 'catalogo:editar' object.pk %}"
           class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">
          Editar
        </a>
        <a href="{% url 'catalogo:excluir' object.pk %}"
           class="rounded-lg px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50">
          Excluir
        </a>
      </div>
    {% endif %}
```

O `{% if %}` repete a regra do `DonoOuAdminMixin` — mas ele **esconde**, não protege. A proteção de verdade é o mixin; isto só evita mostrar um botão que daria 403.

- [ ] **Step 8: Ajustar o título do formulário para servir aos dois usos**

O `item_form.html` é usado pela `CreateView` e pela `UpdateView`, mas hoje diz "Novo item" sempre. Em `catalogo/templates/catalogo/item_form.html`, troque as duas linhas do título e do `<h1>` por:

```html
{% block titulo %}{% if object %}Editar {{ object.titulo }}{% else %}Novo item{% endif %} — Gostoteca{% endblock %}
```

e

```html
  <h1 class="mb-6 text-2xl font-semibold text-slate-900">
    {% if object %}Editar item{% else %}Novo item{% endif %}
  </h1>
```

Na `CreateView` o `object` é `None`; na `UpdateView` é o item sendo editado. É assim que um único template serve aos dois.

- [ ] **Step 9: Rodar a suíte inteira**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 33 tests` / `OK` (26 anteriores + 7 novos)

- [ ] **Step 10: Rodar os comandos do CI**

Run: `.\venv\Scripts\python.exe manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `.\venv\Scripts\python.exe manage.py test`
Expected: `OK`

- [ ] **Step 11: Confirmar que nada foi commitado**

Run: `git status --short`
Expected: **vários arquivos modificados e não rastreados.** É o resultado correto. As alterações ficam no working tree para o usuário commitar. Se a saída estiver vazia, alguém commitou — reporte isso.

---

## Verificação manual (ao final)

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

1. `/login/` — entrar. Deve cair em `/catalogo/`, **agora sem 404**.
2. "Novo item" — cadastrar um item **com capa**. A imagem deve aparecer no detalhe e na lista. Se o item salvar mas a capa não aparecer, o problema é o `static()` do Step 5 da Task 3 ou o `enctype` do Step 7 da Task 4.
3. No detalhe do próprio item, "Editar" e "Excluir" devem aparecer.
4. Faça logout, cadastre um segundo usuário, e abra o detalhe do item do primeiro: **os botões não devem aparecer**. Acessar `/catalogo/<pk>/editar/` na mão deve dar **403**.

As telas só aparecem estilizadas **com internet** (Play CDN).

## Contagem de testes

O spec previa 10 testes. Este plano entrega **23 novos** (33 no total, somando os 10 do `usuarios`). Os extras cobrem casos que apareceram ao decompor as tarefas: `__str__`, campos opcionais, 404 de item inexistente, GET dos formulários, anônimo em cada rota, `criado_por` forjado via POST, título vazio e arquivo não-imagem. Nenhum dos 10 do spec ficou de fora.
