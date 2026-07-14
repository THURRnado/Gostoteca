# Design — Telas de login e cadastro (app `usuarios`)

**Data:** 2026-07-14
**Projeto:** Gostoteca (Atividade 03 — Aplicação CRUD, UFPB)
**Escopo:** Telas de cadastro, login e logout no app `usuarios`.

## Contexto

O projeto já tem:

- Django 6.0.7, SQLite, apps `usuarios` e `catalogo` registrados.
- Modelo `usuarios.Usuario(AbstractUser)` com `email` `unique=True, blank=False`, ativo via `AUTH_USER_MODEL`.
- Migração inicial aplicada; `Usuario` registrado no admin via `UserAdmin`.
- `gostoteca/urls.py` contém apenas `admin/`. Não existe home page.

Este design cobre os critérios da Seção 5 do documento da atividade: *"Cadastro, login e logout; senha com hash; rotas protegidas exigem login."*

## Decisões tomadas

| Decisão | Escolha | Motivo |
|---|---|---|
| Views de login/logout | `LoginView` / `LogoutView` do Django | Menos código próprio; sessão, `next` e proteção contra session fixation vêm testados do framework. |
| View de cadastro | `CreateView` + form próprio | O `UserCreationForm` padrão não inclui `email`; o campo é exigido pelo documento. |
| Destino pós-login | Caminho literal `/catalogo/` | O `catalogo` ainda não existe. Um nome de rota inexistente estouraria `NoReverseMatch` no login; o caminho literal degrada para 302 → 404, que é testável. |
| CSS | Tailwind v4 via Play CDN | Escolha do usuário. Sem build step. |
| Auto-login após cadastro | Não | Mantém "cadastro" e "login" verificáveis de forma independente. |

### Divergências em relação ao documento da atividade

1. **Bootstrap → Tailwind.** A Seção 2 do documento especifica Bootstrap. A implementação usará Tailwind. O documento ou o relatório final deve registrar a mudança.
2. **`data_cadastro` → `date_joined`.** O campo pedido na Seção 4 já existe no `AbstractUser` como `date_joined`. Não foi duplicado.

### Riscos aceitos

- **Play CDN exige internet.** As telas ficam sem estilo se a apresentação ou o container Docker estiverem sem rede. A documentação do Tailwind desaconselha o Play CDN fora de prototipagem.
- **`/catalogo/` retorna 404 até o app existir.** Navegação manual pós-login fica quebrada; os testes não.

## Componentes

### `usuarios/forms.py` (novo)

```python
class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'email')
```

O `email` herda obrigatoriedade (`blank=False`) e unicidade (`unique=True`) do modelo automaticamente, via ModelForm. Nenhum validador manual é necessário.

### `usuarios/views.py`

```python
class CadastroView(CreateView):
    form_class = UsuarioCreationForm
    template_name = 'usuarios/cadastro.html'
    success_url = reverse_lazy('login')
```

Login e logout não têm view própria.

### `usuarios/urls.py` (novo)

| Rota | View | Nome |
|---|---|---|
| `login/` | `LoginView(template_name='usuarios/login.html')` | `login` |
| `logout/` | `LogoutView` | `logout` |
| `cadastro/` | `CadastroView` | `cadastro` |

Incluído na raiz: `path('', include('usuarios.urls'))` em `gostoteca/urls.py`. URLs finais: `/login/`, `/logout/`, `/cadastro/`.

### `usuarios/templates/usuarios/` (novo)

- `base.html` — script do Tailwind v4 (`@tailwindcss/browser@4`) e `{% block conteudo %}`.
- `login.html` — estende `base.html`, renderiza o form de autenticação.
- `cadastro.html` — estende `base.html`, renderiza o `UsuarioCreationForm`.

**O logout é um `<form method="post">` com `{% csrf_token %}`, não um link.** A `LogoutView` do Django 5+ só aceita POST; `GET` retorna 405.

### `gostoteca/settings.py`

```python
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/catalogo/'
LOGOUT_REDIRECT_URL = 'login'
```

## Fluxo

1. **Cadastro:** anônimo → `/cadastro/` → form válido → `UserCreationForm.save()` cria o usuário com senha hasheada → 302 para `/login/`.
2. **Login:** `/login/` → credenciais válidas → sessão criada → 302 para `/catalogo/`.
3. **Logout:** POST em `/logout/` → sessão encerrada → 302 para `/login/`.

## Tratamento de erros

| Situação | Resultado |
|---|---|
| Username duplicado | Erro de campo no form (200) |
| Email duplicado | Erro de campo no form (200), via `unique=True` |
| Email vazio | Erro de campo no form (200), via `blank=False` |
| Senhas divergentes | Erro do `UserCreationForm` (200) |
| Senha fraca | Erro dos `AUTH_PASSWORD_VALIDATORS` (200) |
| Credenciais inválidas | 200 com mensagem genérica, sem revelar qual campo falhou |
| `GET /logout/` | 405 |

## Testes (`usuarios/tests.py`)

Sete testes, cobrindo a Seção 6 do documento:

1. Cadastro válido cria o usuário e `check_password()` confirma o hash da senha.
2. Cadastro com email duplicado é rejeitado e não cria usuário.
3. Cadastro com email vazio é rejeitado e não cria usuário.
4. Login válido retorna 302 para `/catalogo/` — sem `follow=True`, para não depender do app inexistente.
5. Login inválido retorna 200 e não cria sessão.
6. `POST /logout/` retorna 302 para `/login/`.
7. `GET /logout/` retorna 405.

Esses testes fazem o `manage.py test` do CI deixar de passar trivialmente (hoje: "Found 0 test(s)").

## Fora de escopo

- Recuperação/reset de senha (não pedido pelo documento).
- Edição de perfil e exclusão de conta (o CRUD de usuário virá depois).
- Home page e qualquer parte do app `catalogo`.
