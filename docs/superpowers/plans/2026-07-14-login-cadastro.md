# Telas de Login e Cadastro — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar as telas de cadastro, login e logout no app `usuarios`, cobertas por sete testes automatizados.

**Architecture:** Login e logout usam `LoginView`/`LogoutView` do `django.contrib.auth`, configuradas direto no `urls.py` do app. O cadastro usa uma `CreateView` com `UsuarioCreationForm`, que estende `UserCreationForm` para incluir o campo `email` (obrigatório e único, herdado do modelo). Os templates estendem um `base.html` que carrega o Tailwind v4 via Play CDN.

**Tech Stack:** Django 6.0.7, SQLite, Tailwind CSS v4 (Play CDN), `manage.py test` (framework de testes do Django).

**Referência:** [Spec aprovado](../specs/2026-07-14-login-cadastro-design.md)

---

## Notas de contexto para quem implementar

- **Rodar comandos sempre de dentro de `Gostoteca/`** (onde está o `manage.py`), usando o Python da venv: `.\venv\Scripts\python.exe`.
- **`LogoutView` só aceita POST** no Django 5+. Um link `<a>` para logout retorna 405. O template usa `<form method="post">`.
- **`LOGIN_REDIRECT_URL` aponta para `/catalogo/`**, que ainda não existe. Isso é intencional (ver spec). Os testes de login verificam `status_code` e `.url` **sem seguir o redirect** — nunca use `assertRedirects` nesses dois testes, pois ele segue e bateria num 404.
- **Desvio em relação ao spec:** o spec previa apenas `UsuarioCreationForm` em `forms.py`. Este plano adiciona também `LoginForm(AuthenticationForm)` e a constante `CLASSES_INPUT`, porque os widgets do Django renderizam `<input>` sem classe e o Tailwind não estiliza tags nuas.
- **Senha usada nos testes:** `senha-forte-123`. Ela passa pelos quatro `AUTH_PASSWORD_VALIDATORS` ativos (comprimento, similaridade com username/email, senha comum, apenas-numérica). Se trocar, verifique que a nova também passa.

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `usuarios/forms.py` (criar) | `UsuarioCreationForm`, `LoginForm` e as classes CSS dos inputs |
| `usuarios/views.py` (modificar) | Apenas `CadastroView` |
| `usuarios/urls.py` (criar) | As três rotas do app |
| `usuarios/templates/usuarios/base.html` (criar) | HTML externo + Tailwind CDN |
| `usuarios/templates/usuarios/login.html` (criar) | Tela de login |
| `usuarios/templates/usuarios/cadastro.html` (criar) | Tela de cadastro |
| `usuarios/tests.py` (modificar) | Os sete testes |
| `gostoteca/urls.py` (modificar) | Incluir `usuarios.urls` |
| `gostoteca/settings.py` (modificar) | `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` |

---

## Task 1: Form de cadastro com email

**Files:**
- Create: `usuarios/forms.py`
- Test: `usuarios/tests.py`

- [ ] **Step 1: Escrever os testes que falham**

Substitua todo o conteúdo de `usuarios/tests.py` por:

```python
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
```

- [ ] **Step 2: Rodar os testes para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test usuarios -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'usuarios.forms'`

- [ ] **Step 3: Escrever a implementação mínima**

Crie `usuarios/forms.py`:

```python
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
```

Os campos `password1`/`password2` vêm do próprio `UserCreationForm` e por isso não aparecem em `Meta.fields`. A obrigatoriedade e a unicidade do `email` vêm do modelo (`blank=False`, `unique=True`) — não há validador manual.

- [ ] **Step 4: Rodar os testes para confirmar que passam**

Run: `.\venv\Scripts\python.exe manage.py test usuarios -v 2`
Expected: PASS — `Ran 3 tests` / `OK`

- [ ] **Step 5: Commit**

```bash
git add usuarios/forms.py usuarios/tests.py
git commit -m "feat(usuarios): form de cadastro com email obrigatorio e unico"
```

---

## Task 2: Rotas, settings, template base e tela de login

**Files:**
- Create: `usuarios/urls.py`, `usuarios/templates/usuarios/base.html`, `usuarios/templates/usuarios/login.html`
- Modify: `gostoteca/urls.py`, `gostoteca/settings.py`, `usuarios/tests.py`

- [ ] **Step 1: Escrever os testes que falham**

Acrescente ao final de `usuarios/tests.py`:

```python
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
```

- [ ] **Step 2: Rodar os testes para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test usuarios.LoginViewTest -v 2`
Expected: FAIL — os três testes retornam 404, porque a rota `/login/` não existe.

- [ ] **Step 3: Criar as rotas do app**

Crie `usuarios/urls.py`:

```python
from django.contrib.auth.views import LoginView
from django.urls import path

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
]
```

- [ ] **Step 4: Incluir as rotas no projeto**

Substitua todo o conteúdo de `gostoteca/urls.py` por:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
]
```

- [ ] **Step 5: Configurar os settings de autenticação**

Em `gostoteca/settings.py`, logo abaixo da linha `AUTH_USER_MODEL = 'usuarios.Usuario'`, acrescente:

```python
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/catalogo/'  # Caminho literal: o app catalogo ainda nao existe.
```

- [ ] **Step 6: Criar o template base**

Crie `usuarios/templates/usuarios/base.html`:

```html
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block titulo %}Gostoteca{% endblock %}</title>
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
</head>
<body class="min-h-screen bg-slate-100 flex items-center justify-center p-4">
  {% block conteudo %}{% endblock %}
</body>
</html>
```

- [ ] **Step 7: Criar a tela de login**

Crie `usuarios/templates/usuarios/login.html`:

```html
{% extends 'usuarios/base.html' %}

{% block titulo %}Entrar — Gostoteca{% endblock %}

{% block conteudo %}
<main class="w-full max-w-sm bg-white rounded-xl shadow-sm p-8">
  <h1 class="text-2xl font-semibold text-slate-900 mb-6">Entrar</h1>

  {% if form.non_field_errors %}
    <div class="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
      {% for erro in form.non_field_errors %}<p>{{ erro }}</p>{% endfor %}
    </div>
  {% endif %}

  <form method="post" class="space-y-4">
    {% csrf_token %}
    {% for campo in form %}
      <div>
        <label for="{{ campo.id_for_label }}" class="block text-sm font-medium text-slate-700 mb-1">
          {{ campo.label }}
        </label>
        {{ campo }}
        {% for erro in campo.errors %}
          <p class="mt-1 text-sm text-red-600">{{ erro }}</p>
        {% endfor %}
      </div>
    {% endfor %}
    <button type="submit"
            class="w-full rounded-lg bg-slate-900 py-2 font-medium text-white hover:bg-slate-700">
      Entrar
    </button>
  </form>
</main>
{% endblock %}
```

Ainda **sem** link para o cadastro: a rota `cadastro` só existe na Task 3, e um `{% url 'cadastro' %}` aqui estouraria `NoReverseMatch` ao renderizar.

- [ ] **Step 8: Rodar os testes para confirmar que passam**

Run: `.\venv\Scripts\python.exe manage.py test usuarios -v 2`
Expected: PASS — `Ran 6 tests` / `OK`

- [ ] **Step 9: Commit**

```bash
git add usuarios/urls.py usuarios/templates gostoteca/urls.py gostoteca/settings.py usuarios/tests.py
git commit -m "feat(usuarios): tela de login com LoginView e template base"
```

---

## Task 3: Tela de cadastro

**Files:**
- Modify: `usuarios/views.py`, `usuarios/urls.py`, `usuarios/templates/usuarios/login.html`, `usuarios/tests.py`
- Create: `usuarios/templates/usuarios/cadastro.html`

- [ ] **Step 1: Escrever os testes que falham**

Acrescente ao final de `usuarios/tests.py`:

```python
class CadastroViewTest(TestCase):
    def test_get_cadastro_retorna_200(self):
        resposta = self.client.get('/cadastro/')

        self.assertEqual(resposta.status_code, 200)

    def test_post_valido_cria_usuario_e_redireciona_para_login(self):
        resposta = self.client.post('/cadastro/', data=DADOS_VALIDOS)

        self.assertRedirects(resposta, '/login/')
        self.assertTrue(Usuario.objects.filter(username='arthur').exists())
```

Aqui `assertRedirects` **pode** ser usado: `/login/` existe desde a Task 2 e responde 200.

- [ ] **Step 2: Rodar os testes para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test usuarios.CadastroViewTest -v 2`
Expected: FAIL — 404, porque a rota `/cadastro/` não existe.

- [ ] **Step 3: Escrever a view**

Substitua todo o conteúdo de `usuarios/views.py` por:

```python
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import UsuarioCreationForm


class CadastroView(CreateView):
    form_class = UsuarioCreationForm
    template_name = 'usuarios/cadastro.html'
    success_url = reverse_lazy('login')
```

- [ ] **Step 4: Registrar a rota**

Substitua todo o conteúdo de `usuarios/urls.py` por:

```python
from django.contrib.auth.views import LoginView
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
    path('cadastro/', views.CadastroView.as_view(), name='cadastro'),
]
```

- [ ] **Step 5: Criar a tela de cadastro**

Crie `usuarios/templates/usuarios/cadastro.html`:

```html
{% extends 'usuarios/base.html' %}

{% block titulo %}Criar conta — Gostoteca{% endblock %}

{% block conteudo %}
<main class="w-full max-w-sm bg-white rounded-xl shadow-sm p-8">
  <h1 class="text-2xl font-semibold text-slate-900 mb-6">Criar conta</h1>

  <form method="post" class="space-y-4">
    {% csrf_token %}
    {% for campo in form %}
      <div>
        <label for="{{ campo.id_for_label }}" class="block text-sm font-medium text-slate-700 mb-1">
          {{ campo.label }}
        </label>
        {{ campo }}
        {% if campo.help_text %}
          <p class="mt-1 text-xs text-slate-500">{{ campo.help_text|safe }}</p>
        {% endif %}
        {% for erro in campo.errors %}
          <p class="mt-1 text-sm text-red-600">{{ erro }}</p>
        {% endfor %}
      </div>
    {% endfor %}
    <button type="submit"
            class="w-full rounded-lg bg-slate-900 py-2 font-medium text-white hover:bg-slate-700">
      Cadastrar
    </button>
  </form>

  <p class="mt-6 text-center text-sm text-slate-600">
    Já tem conta? <a href="{% url 'login' %}" class="text-slate-900 underline">Entrar</a>
  </p>
</main>
{% endblock %}
```

- [ ] **Step 6: Adicionar o link de cadastro na tela de login**

Em `usuarios/templates/usuarios/login.html`, logo antes do `</main>`, acrescente:

```html
  <p class="mt-6 text-center text-sm text-slate-600">
    Não tem conta? <a href="{% url 'cadastro' %}" class="text-slate-900 underline">Cadastre-se</a>
  </p>
```

- [ ] **Step 7: Rodar os testes para confirmar que passam**

Run: `.\venv\Scripts\python.exe manage.py test usuarios -v 2`
Expected: PASS — `Ran 8 tests` / `OK`

- [ ] **Step 8: Commit**

```bash
git add usuarios/views.py usuarios/urls.py usuarios/templates usuarios/tests.py
git commit -m "feat(usuarios): tela de cadastro com CreateView"
```

---

## Task 4: Logout

**Files:**
- Modify: `usuarios/urls.py`, `gostoteca/settings.py`, `usuarios/templates/usuarios/base.html`, `usuarios/tests.py`

- [ ] **Step 1: Escrever os testes que falham**

Acrescente ao final de `usuarios/tests.py`:

```python
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
```

O segundo teste trava o comportamento do Django 5+: `GET` em logout é 405 e **não** encerra a sessão.

- [ ] **Step 2: Rodar os testes para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test usuarios.LogoutViewTest -v 2`
Expected: FAIL — 404, porque a rota `/logout/` não existe.

- [ ] **Step 3: Registrar a rota**

Substitua todo o conteúdo de `usuarios/urls.py` por:

```python
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
```

- [ ] **Step 4: Configurar o destino do logout**

Em `gostoteca/settings.py`, logo abaixo de `LOGIN_REDIRECT_URL`, acrescente:

```python
LOGOUT_REDIRECT_URL = 'login'
```

- [ ] **Step 5: Adicionar o botão de logout no template base**

Em `usuarios/templates/usuarios/base.html`, substitua a tag `<body>` inteira (da abertura ao fechamento) por:

```html
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

  <div class="flex items-center justify-center p-4">
    {% block conteudo %}{% endblock %}
  </div>
</body>
```

O logout é um `<form method="post">` com `{% csrf_token %}`, **nunca** um `<a href>`. A `LogoutView` do Django 5+ recusa `GET` com 405 — foi o que o teste do Step 1 travou.

- [ ] **Step 6: Rodar a suíte inteira**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: PASS — `Ran 10 tests` / `OK`

- [ ] **Step 7: Rodar os mesmos comandos do CI**

Run: `.\venv\Scripts\python.exe manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `.\venv\Scripts\python.exe manage.py test`
Expected: `OK` — e o CI deixa de passar trivialmente ("Found 0 test(s)").

- [ ] **Step 8: Commit**

```bash
git add usuarios/urls.py usuarios/templates gostoteca/settings.py usuarios/tests.py
git commit -m "feat(usuarios): logout por POST"
```

---

## Verificação manual (opcional, ao final)

```bash
.\venv\Scripts\python.exe manage.py runserver
```

1. `http://127.0.0.1:8000/cadastro/` — criar uma conta. Deve redirecionar para o login.
2. Tentar cadastrar o **mesmo email** de novo. Deve mostrar erro no campo email, sem criar usuário.
3. `http://127.0.0.1:8000/login/` — entrar. Deve redirecionar para `/catalogo/` e **mostrar um 404** — esperado, o app não existe ainda.
4. Abrir `http://127.0.0.1:8000/cadastro/` **ainda logado**: o cabeçalho com o botão "Sair" deve aparecer. Clicar em Sair deve levar de volta ao login.

Sobre o passo 4: não adianta voltar para `/login/` para ver o cabeçalho, porque `redirect_authenticated_user=True` chuta um usuário já autenticado de volta para `/catalogo/` (404). Enquanto o `catalogo` não existir, `/cadastro/` é a única página que um usuário logado consegue abrir — ou seja, o botão "Sair" só é visível ali. Isso se resolve sozinho quando a home do catálogo existir; não é um defeito a corrigir agora.

As telas só aparecem estilizadas **com internet** (Play CDN).

## Contagem de testes

O spec previa sete testes. Este plano entrega **dez**: os sete do spec mais três que apareceram naturalmente ao decompor as tarefas (`GET /login/` → 200, `GET /cadastro/` → 200, e a verificação de que o login inválido não cria sessão). Nenhum requisito do spec ficou sem teste.
