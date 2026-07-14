# Resumo da sessão — 2026-07-14

Registro do que foi decidido e construído na sessão que partiu do documento da Atividade 03 e terminou com as telas de autenticação prontas. Serve de matéria-prima para o relatório final e de memória das decisões que não são óbvias olhando só o código.

---

## 1. Ponto de partida

A pasta continha um único arquivo: `Atividade 03 - aplicacao CRUD.docx`, a especificação da atividade. Nenhum código.

O documento define uma aplicação web para catalogar preferências de mídia (jogos, filmes, livros) com camada social, dois tipos de usuário (comum e administrador), CRUD sobre quatro entidades (`usuario`, `item`, `preferencia`, `comentario`), stack Python/Django/SQLite/Bootstrap, e critérios de aceitação e teste nas Seções 5 e 6.

## 2. Nome do projeto

Brainstorm de nomes, com preferência declarada por junções de dois termos. Candidatos discutidos: `Coletânea`, `Resenha`, `Gostário`, `Socervo`, `Acervoteca`, `Midiateca` (descartado — termo já consagrado), `Ludoteca` (descartado — já significa "espaço de jogos", exclui filmes e livros).

**Escolhido: Gostoteca** (gosto + biblioteca).

## 3. Divisão em apps

A discussão passou por três configurações:

| Opção | Apps | Avaliação |
|---|---|---|
| 4 apps | `contas`, `catalogo`, `preferencias`, `social` | Over-engineering para 4 tabelas. O app `social` teria um modelo só. |
| 3 apps | `contas`, `catalogo`, `preferencias` (com comentário junto) | Meio-termo recomendado na hora. |
| **2 apps** | **`usuarios`, `catalogo`** | **Escolhido.** Mais enxuto; `usuarios` existe por necessidade técnica (ver abaixo). |

`usuarios` não é uma divisão estética: o modelo de usuário customizado precisa morar num app próprio, porque o `AUTH_USER_MODEL` é referenciado por todo o resto e conviveria mal com regras de negócio pesadas no mesmo lugar.

Consequência aceita: `catalogo/models.py` vai concentrar `Item`, `Preferencia` e `Comentario`. Quando `views.py` passar de ~300 linhas, o caminho é quebrar em pacote (`catalogo/views/item.py` etc.), **não** criar apps novos.

## 4. O modelo de usuário — a decisão mais sensível

**Timing é tudo.** O modelo de usuário customizado tem que existir antes do primeiro `migrate`. Trocar depois é notoriamente difícil. O projeto parou exatamente no ponto certo: os apps existiam, o `db.sqlite3` não.

Duas descobertas ao confrontar o documento com o que o `AbstractUser` já oferece:

- **`data_cadastro` já existe** como `date_joined`. Mesmo tipo, mesmo propósito, preenchido automaticamente. **Não foi duplicado** — criar o campo ao lado geraria dois dados que podem divergir. Registrar essa equivalência no relatório.
- **`email` precisou de override.** O documento pede único e obrigatório; o `AbstractUser` o define opcional e **não** único. Este é o único campo que o modelo redefine.

O `papel` (comum/admin) **não virou coluna** — sai dos Groups do Django, como o próprio documento previu.

Resultado:

```python
class Usuario(AbstractUser):
    email = models.EmailField('e-mail', unique=True, blank=False)
```

### A armadilha do E304

Com o `Usuario` criado mas o `AUTH_USER_MODEL` ainda ausente do settings, o `manage.py check` acusou **4 erros `fields.E304`**: o `auth.User` padrão continuava ativo ao lado do `Usuario`, e os dois brigavam pelo mesmo nome de acessor reverso em `groups` e `user_permissions`.

**A dica que o Django imprime está errada para esse caso.** Ele sugere "add or change a related_name argument" — seguir isso silenciaria os erros mantendo dois modelos de usuário coexistindo. A correção é uma linha:

```python
AUTH_USER_MODEL = 'usuarios.Usuario'
```

## 5. Admin

`Usuario` registrado com `UserAdmin`, **não** `ModelAdmin`:

```python
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ...
```

A herança traz o widget de senha com hash, os fieldsets de permissões e a tela de "adicionar usuário" em dois passos. Com um `ModelAdmin` comum, o campo de senha viraria input de texto puro e seria possível salvar senhas **sem hash** pelo admin — furando um critério da Seção 5.

O superusuário **não foi criado pelo assistente**, por decisão deliberada: criar a conta exige definir uma senha, e senhas "só para desenvolvimento" têm o hábito de sobreviver até a apresentação. O comando é interativo de propósito.

## 6. Infraestrutura

Criados: `.gitignore`, `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `.github/workflows/ci.yml`, `media/.gitkeep`.

Dois arquivos não pedidos foram necessários: o `docker-compose.yml` faz `build: .` e exige um `Dockerfile`; e o `.dockerignore` é praticamente obrigatório porque **a `venv/` está dentro da pasta do projeto** — sem ele, o build copiaria a venv inteira do Windows para dentro de uma imagem Linux.

Ressalvas registradas:

- **O `docker-compose.yml` tem um serviço só.** O documento especifica SQLite, então o banco é um arquivo no bind mount, não um container. Compose só justificaria sua existência com um Postgres separado — o que contraria a especificação.
- **O CI passa trivialmente enquanto não houver testes.** Corrigido depois: agora roda 10.
- **O `docker compose up` nunca foi executado.** O arquivo foi validado com `docker compose config`, mas a imagem nunca foi construída. As instruções do README são corretas em teoria, não verificadas na prática.

## 7. Telas de autenticação — decisões de design

### Destino pós-login

Não existia nenhuma página além do `/admin/`. Escolha: **esperar o `catalogo`**, com `LOGIN_REDIRECT_URL` apontando para o caminho literal `/catalogo/`.

Por que caminho literal e não `reverse_lazy('catalogo:lista')`: um nome de rota inexistente estoura `NoReverseMatch` **no momento do login**, quebrando o fluxo com exceção. O caminho literal degrada para um 302 → 404, que é um estado testável. **Quando o app existir, trocar pelo nome.**

O fluxo continua testável mesmo assim: o test client afirma o 302 e a URL de destino **sem seguir o redirect**.

### CSS: divergência em relação ao documento

**O documento especifica Bootstrap na Seção 2. O código usa Tailwind v4 via Play CDN.** Isso foi escolha consciente, mas cria divergência entre a especificação entregue e o código entregue. **Corrigir o `.docx` ou registrar a mudança no relatório.**

Riscos aceitos do Play CDN: exige internet (as telas ficam sem estilo numa apresentação sem rede, e o container Docker também precisa de rede), e a própria documentação do Tailwind o desaconselha fora de prototipagem. Detalhe técnico: o `cdn.tailwindcss.com` da maioria dos tutoriais é **v3**; a v4 usa `@tailwindcss/browser@4`.

### Views: prontas do Django

Escolhida a abordagem de usar `LoginView` e `LogoutView` do framework e uma `CreateView` para o cadastro, em vez de views customizadas com `authenticate()`/`login()` na mão. O trabalho pesado — validação de credenciais, rotação de sessão contra session fixation, tratamento do `next`, mensagens de erro — vem testado do framework.

Mesmo assim há código próprio onde importa: o `UserCreationForm` do Django **não inclui o campo email**, então um cadastro usando ele direto salvaria usuários sem email — furando o `blank=False` do modelo, porque validação de formulário não é a mesma coisa que validação de modelo.

### Sem auto-login após cadastro

Redirecionar para o login mantém os critérios "cadastro" e "login" verificáveis de forma independente.

## 8. Descobertas técnicas da implementação

### Logout só aceita POST

No Django 5+, a `LogoutView` **removeu o `GET`**. O clássico `<a href="{% url 'logout' %}">Sair</a>` de praticamente todo tutorial antigo devolve **405**. O logout tem que ser `<form method="post">` com `{% csrf_token %}`.

Há teste travando isso: `GET /logout/` → 405 **e a sessão sobrevive** (prova que não é um "logout silencioso").

### Tailwind não estiliza tags nuas

Os widgets do Django renderizam `<input>` sem classe alguma. Como o Tailwind é utility-first, os campos sairiam sem formatação. Solução: um mixin `_FormEstilizado` que injeta as classes via `widget.attrs`, o que obrigou a criar também um `LoginForm(AuthenticationForm)` só para isso. Foi um desvio do spec, registrado no plano.

### O bug do `<ul>` dentro de `<p>`

O partial `_campo.html` envolvia o `help_text` num `<p>`. Só que o `help_text` do `password1` **é uma `<ul>`** — vem de `password_validation.password_validators_help_text_html()`, listando as regras dos `AUTH_PASSWORD_VALIDATORS`.

`<ul>` dentro de `<p>` é HTML inválido. O navegador fechava o `<p>` sozinho, deixando um `<p>` vazio com as classes do Tailwind, uma `<ul>` órfã sem estilo (preto 16px em vez de cinza 12px) e um `</p>` sobrando.

**Como foi pego:** inspeção do DOM real, não leitura de código. Um implementador havia afirmado que o `help_text` era vazio — sem ter renderizado a página. A suíte de testes **não pegaria isso**, nem antes nem depois.

**Decisão sobre testar markup: não.** O teste que pegaria isso ou assertaria substring de HTML bruto (quebra ao reordenar uma classe do Tailwind) ou exigiria uma dependência nova de parsing. A ferramenta certa para markup inválido é um validador, não unittest — desproporcional aqui.

Correção: `<p>` → `<div>`.

## 9. Testes

10 testes, cobrindo:

1–3. Form de cadastro: válido cria usuário com senha hasheada (`assertNotEqual` no raw **e** `check_password`); email vazio rejeitado; email duplicado rejeitado.
4–6. Login: `GET` → 200; válido → 302 para `/catalogo/` + sessão; inválido → 200 sem sessão.
7–8. Cadastro via HTTP: `GET` → 200; POST válido cria e redireciona.
9–10. Logout: POST encerra sessão e redireciona; GET → 405 e sessão sobrevive.

O CSRF foi verificado com `Client(enforce_csrf_checks=True)` — o test client do Django relaxa CSRF por padrão, então sem isso a suíte poderia estar passando por acidente.

## 10. Pendências

Em ordem de importância para a nota:

1. **"Rotas protegidas exigem login" (Seção 5) não está implementado nem testado.** Não há um único `login_required` ou `LoginRequiredMixin` no projeto; o `LOGIN_URL` é config morta hoje. Adiar foi correto — não existe rota protegível enquanto o `catalogo` não existir —, mas o item precisa aterrissar junto com o app: `LoginRequiredMixin` na primeira view do catálogo e um teste "anônimo em `/catalogo/` → 302 para `/login/?next=/catalogo/`".
2. **O `.docx` diz Bootstrap; o código usa Tailwind.** Corrigir o documento ou registrar no relatório.
3. **Falta teste de username duplicado.** O comportamento está correto, mas sem teste — e a tabela de erros do spec o lista. São 6 linhas.
4. **`cadastro.html` não tem o bloco de `non_field_errors`** que o `login.html` tem. Inofensivo hoje (os erros do `UserCreationForm` são todos de campo), mas um `clean()` futuro falharia em silêncio.
5. **Superusuário ainda não criado** (`python manage.py createsuperuser`).
6. **`.gitattributes`** para normalizar LF/CRLF, se o André estiver em Linux ou macOS.
7. **`TIME_ZONE` está `America/Sao_Paulo`**; o fuso canônico da Paraíba é `America/Fortaleza`. Mesmo UTC−3, histórias de horário de verão diferentes. Cosmético.
8. **`docker compose up` nunca foi testado.**

## 11. Consequência conhecida e temporária

Enquanto o `catalogo` não existir, o cabeçalho com o botão "Sair" só é visível em `/cadastro/`. Motivo: a `LoginView` tem `redirect_authenticated_user=True`, então um usuário logado que abrir `/login/` é mandado para `/catalogo/` (404) — e não sobra nenhuma outra página que ele consiga abrir. Some sozinho quando a home do catálogo existir.

---

## Documentos relacionados

- `docs/superpowers/specs/2026-07-14-login-cadastro-design.md` — design das telas de autenticação, com as divergências e riscos aceitos
- `docs/superpowers/plans/2026-07-14-login-cadastro.md` — plano de implementação em 4 tarefas TDD
