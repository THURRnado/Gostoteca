# Resumo da sessão — 2026-07-14

Registro do que foi decidido e construído na sessão que partiu do documento da Atividade 03 e chegou até a primeira fatia do catálogo com identidade visual aplicada. Serve de matéria-prima para o relatório final e de memória das decisões que não são óbvias olhando só o código.

As seções 1 a 11 são o registro de decisões. A seção 15, no fim, traz o diálogo da sessão em ordem cronológica.

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

O `papel` (comum/admin) **não virou coluna**. Na época desta decisão a intenção era resolvê-lo pelos Groups do Django, como o documento previu — mas na fatia do catálogo isso mudou para `is_staff` (ver seção 12).

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

## 10. Pendências (estado ao fim da sessão)

Em ordem de importância para a nota:

1. **O `.docx` está defasado em cinco pontos.** Bootstrap→Tailwind; qualquer usuário cria itens; `capa_url` texto→upload; "remoção de item em uso é bloqueada" não implementado; `papel` via Group→`is_staff`. Corrigir o documento ou registrar tudo no relatório. **A quarta é a que custa nota:** é um critério escrito da Seção 5 que ficará sem implementação e sem teste (ver seção 12).
2. **Falta teste de username duplicado.** O comportamento está correto, mas sem teste — e a tabela de erros do spec o lista. São 6 linhas.
3. **`cadastro.html` não tem o bloco de `non_field_errors`** que o `login.html` tem. Inofensivo hoje (os erros do `UserCreationForm` são todos de campo), mas um `clean()` futuro falharia em silêncio.
4. **Superusuário ainda não criado** (`python manage.py createsuperuser`).
5. **`.gitattributes`** para normalizar LF/CRLF, se o André estiver em Linux ou macOS.
6. **`TIME_ZONE` está `America/Sao_Paulo`**; o fuso canônico da Paraíba é `America/Fortaleza`. Mesmo UTC−3, histórias de horário de verão diferentes. Cosmético.
7. **`docker compose up` nunca foi testado.** O `docker compose config` valida, mas a imagem nunca foi construída.
8. **Fatias 2 e 3 do catálogo** — `Preferencia` e `Comentario` — ainda não começaram.

**Resolvido durante a sessão:** "rotas protegidas exigem login" (Seção 5) era a pendência número 1 e foi fechada na fatia 1 do catálogo, com `LoginRequiredMixin` nas cinco views e um teste de anônimo → 302 para `/login/?next=`.

## 11. Consequência conhecida — resolvida

Enquanto o `catalogo` não existia, o cabeçalho com o botão "Sair" só era visível em `/cadastro/`: a `LoginView` tem `redirect_authenticated_user=True`, então um usuário logado que abrisse `/login/` era mandado para `/catalogo/`, que dava 404 — e não sobrava nenhuma outra página. **Sumiu sozinho quando a lista do catálogo passou a existir**, exatamente como previsto.

## 12. App `catalogo` — fatia 1 de 3

O `catalogo` carrega quase todo o resto do projeto: três dos quatro modelos e quatro dos cinco critérios da Seção 5. Grande demais para uma tarefa só, foi fatiado em três: **(1)** `Item` + lista + detalhe + CRUD + autorização — *feito*; **(2)** `Preferencia`; **(3)** `Comentario`.

### Mudanças no modelo de permissão

O documento diz que o administrador gerencia o catálogo e anota `criado_por` como "FK → usuario (**admin**)". Isso foi trocado por decisão do usuário:

| Ação sobre um item | Quem pode |
|---|---|
| Criar | Qualquer usuário logado |
| Ver | Qualquer usuário logado |
| Editar | Dono ou admin |
| Excluir | Dono ou admin |

Essa mudança **resolveu de graça a maior dúvida de escopo do projeto**: se o CRUD de item sairia pelo Django Admin. Não sai — se usuário comum cria itens e a Seção 5 diz que ele não acessa a administração, o CRUD tem que ser telas próprias.

### "Admin" significa `is_staff`

O documento diz `papel | enum (comum, admin) | via Group do Django`. Foi trocado por `is_staff` porque a Seção 5 também exige que "usuário comum não acessa a administração" — e o acesso ao `/admin/` é controlado por `is_staff`, não por Groups. Com Group, existiriam **duas noções de admin que podem divergir**: alguém no grupo mas com `is_staff=False` excluiria qualquer item e ainda levaria 403 no `/admin/`.

### O `DonoOuAdminMixin` e o presente do `AccessMixin`

```python
class DonoOuAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.get_object().criado_por == self.request.user or self.request.user.is_staff
```

O `handle_no_permission()` do `AccessMixin` faz `if self.raise_exception or self.request.user.is_authenticated: raise PermissionDenied`. Ou seja, **sem configurar nada**: anônimo é redirecionado ao login, logado-não-dono leva 403. É literalmente o que a Seção 6 pede ("usuário comum recebe 403/redirecionamento"), de graça.

`LoginRequiredMixin` vem **antes** na MRO, para o anônimo ser barrado antes de o `test_func` ir ao banco.

### O CASCADE e o critério que ele derruba

`Usuario` → `Item` → `Preferencia`, todos CASCADE, por escolha consciente do usuário. Duas consequências registradas como risco aceito:

- **"Remoção de item em uso é bloqueada" (Seção 5) não será implementado.** A Seção 6 exige um teste por critério; este ficará sem implementação e sem teste. A saída limpa é remover o critério do `.docx`.
- **Excluir a conta apaga dados de terceiros.** Quem sai leva os próprios itens e as preferências que outras pessoas tinham neles.

### Upload da capa

`capa_url texto` (documento) virou `capa` como `ImageField`. Consequências: **Pillow** entrou como primeira dependência de terceiros; o campo foi renomeado (`capa_url` mentiria sobre o conteúdo); e o `urls.py` ganhou `static(settings.MEDIA_URL, ...)` sob `DEBUG`.

Duas armadilhas documentadas no plano, ambas silenciosas:

- **`enctype="multipart/form-data"` no form.** Sem isso o navegador manda o nome do arquivo, não os bytes — e a capa nunca chega, sem erro nenhum.
- **`static()` no `urls.py`.** Sem isso o upload grava mas a imagem não aparece — o sintoma parece bug de upload e é roteamento.

E nos testes: **`@override_settings(MEDIA_ROOT=<tempdir>)` não é opcional** — sem isso a suíte grava arquivos de verdade na `media/` a cada execução, inclusive no CI.

### Dívida técnica paga

`LOGIN_REDIRECT_URL` deixou de ser o caminho literal `'/catalogo/'` e virou `reverse_lazy('catalogo:lista')`. Precisa ser `reverse_lazy` e não `reverse`: o `settings.py` carrega antes das URLs.

## 13. Identidade visual

Paleta definida a partir de uma imagem fornecida pelo usuário, aplicada via `@theme` do Tailwind v4:

| Nome | Hex | Uso |
|---|---|---|
| `areia` | `#F2CC85` | Texto sobre cacau, bordas, selos |
| `mel` | `#F29A2E` | Acento (linha dourada, foco) |
| `ambar` | `#D97B29` | Bordas de input, hover |
| `ferrugem` | `#A64B17` | Texto secundário, hover de botão |
| `cacau` | `#401201` | Texto principal, navbar, botão primário |
| `pergaminho` | `#FDF8F0` | Fundo de página — **derivado, não estava na imagem** |

**A sexta cor foi acrescentada por necessidade:** cinco tons saturados não constroem uma interface, falta fundo e superfície.

**Erros continuam em vermelho**, fora da paleta. Ferrugem e cacau já são avermelhados; usar um deles para erro tornaria o erro indistinguível do botão primário.

Direção estética: **grimório / biblioteca alquímica** — pergaminho, luz de vela, dourado. Tipografia **Fraunces** (display) + **Karla** (corpo), via Google Fonts. A navbar é cacau com uma linha em degradê ferrugem→mel→ferrugem embaixo, imitando o corte dourado de um livro antigo.

**Terceira dependência de internet.** O Google Fonts entrou junto do Play CDN do Tailwind. Sem rede, a apresentação perde fonte e estilo.

A marca (livro aberto com faíscas) vive em `templates/_marca.html` e usa `currentColor`, então serve sobre o cacau da navbar e sobre o pergaminho do login.

## 14. O que o processo pegou

Cinco defeitos que não teriam aparecido sem verificação — vale registrar porque três eram erros meus:

1. **`<ul>` dentro de `<p>`.** O `help_text` do `password1` é uma `<ul>`; o partial a envolvia num `<p>`, que é HTML inválido. O navegador quebrava a estrutura e a lista de regras de senha saía sem estilo. **Só apareceu na inspeção do DOM** — os testes não pegariam, e um implementador havia afirmado que o campo era vazio sem ter renderizado.
2. **Spec mentindo sobre cobertura.** O spec de autenticação afirmava cobrir a Seção 5, mas "rotas protegidas" não estava implementado. Um spec que se declara completo é como esse tipo de item se perde.
3. **Plano com o baseline errado.** Dizia 8 testes onde eram 10. O subagente **parou e perguntou em vez de adivinhar** — se tivesse seguido, os passos posteriores checariam contagens erradas.
4. **Lixo declarado como removido.** Um implementador afirmou ter apagado um `.claude/launch.json` e não apagou; a revisão de spec também não pegou. Apareceu num `git status` manual.
5. **Faíscas invisíveis.** A primeira versão do ícone tinha faíscas de 3 a 4 pixels na navbar — sumiam, e sobrava um livro comum. O código estava "correto" nas duas versões; só a tela mostrou.

O padrão: **os testes provam comportamento, não aparência nem asseio.** Todo defeito visual e toda sujeira exigiram olhar de fato.

## 15. Diálogo da sessão

Mensagens do usuário na íntegra; respostas resumidas.

**Eu:** "Leia o documento que está dentro dessa pasta, me diga o que entendeu do que foi especificado."
**Claude:** Li o `.docx` e resumi: catálogo de mídia com camada social, dois papéis, CRUD sobre quatro entidades, stack Python/Django/SQLite/Bootstrap, critérios nas Seções 5 e 6. A pasta só tinha o documento, sem código.

**Eu:** "Me dê ideias de um bom nome para esse projeto"
**Claude:** Propus nomes por vibe — Acervo, Coletânea, Resenha, Nota 10, Gosto Comum — recomendando Coletânea, que cobre os três tipos de mídia sem listar nenhum.

**Eu:** "Gosto de nomes que são junções de dois termos, me dê ideias"
**Claude:** Ofereci portmanteaus: Socervo, Gostoteca, Gostário, Opinário, Resenharia. Recomendei Gostário. Alertei que Midiateca e Ludoteca já existem com significado próprio.

**Eu:** "Agora me ajude a iniciar um projeto django. Me fale o passo a passo"
**Claude:** Checei o ambiente (Python 3.13.9, Git 2.52, Django ausente) e dei oito passos. Enfatizei criar o modelo de usuário customizado **antes** do primeiro `migrate` — trocar depois é notoriamente difícil.

**Eu:** "Me explique o porquê de cada app"
**Claude:** Expliquei a responsabilidade de cada um e admiti que quatro apps para quatro tabelas é over-engineering. Recomendei três, com dois como alternativa enxuta.

**Eu:** "prefiro usuarios e catalogo"
**Claude:** Ajustei os comandos. Avisei que `catalogo/models.py` concentraria três modelos, e que a saída futura é quebrar as views em pacote, não criar apps novos.

**Eu:** "Analise como está a estrutura do projeto agora. Então vamos começar a mexer no app 'usuarios'"
**Claude:** Projeto criado, apps registrados, `migrate` ainda não rodado — o momento exato para o modelo customizado. Descobri que `data_cadastro` já existe como `date_joined` e que o `email` precisava de override.

**Eu:** "Faça somente o .gitignore, o arquivo ci/cd e o docker compose"
**Claude:** Criei os três, mais Dockerfile e `.dockerignore` (o compose não funciona sem eles). Encontrei 4 erros E304: o `Usuario` existia sem `AUTH_USER_MODEL`, e a dica do próprio Django apontava a correção errada.

**Eu:** "Sim"
**Claude:** Adicionei o `AUTH_USER_MODEL` e rodei a primeira migração. `check` limpo, e `get_user_model()` confirmando `usuarios.Usuario` com email único e obrigatório.

**Eu:** "registre o Usuario no admin e crie o superusuário"
**Claude:** Registrei com `UserAdmin`, não `ModelAdmin` — senão o campo de senha vira texto puro e dá para salvar sem hash. **Recusei criar o superusuário:** exige senha, e a senha é sua.

**Eu:** "Antes de ir para o catalogo, quero criar tela de login e cadastro em usuarios"
**Claude:** Entrei em brainstorming e apontei o bloqueio: não existia página nenhuma além do `/admin/`, então o login não tinha para onde redirecionar.

**Eu:** "Esperar o catalogo" / "Não quero usar bootstrap, quero usar tailwind css" / "Play CDN"
**Claude:** Registrei. Corrigi meu próprio pessimismo — o fluxo era testável sem seguir o redirect. Sinalizei a divergência com a Seção 2 e que o Play CDN exige internet.

**Eu:** "Vamos com a opção A"
**Claude:** Apresentei o design: `LoginView`/`LogoutView` do Django e uma `CreateView`, com form próprio por causa do email. Alertei que a `LogoutView` do Django 5+ só aceita POST e devolve 405 no GET.

**Eu:** "Sim" / "Pode iniciar"
**Claude:** Escrevi o spec, fiz `git init`, o primeiro commit, e o plano em quatro tarefas TDD. Registrei o desvio do `LoginForm`, necessário porque o Tailwind não estiliza tags nuas.

**Eu:** "Vamos com a opção 1"
**Claude:** Criei uma branch e despachei um subagente por tarefa, com duas revisões cada. Elas pegaram um bug real: `<ul>` dentro de `<p>` no help_text, invisível para os testes.

**Eu:** "Manter a branch como está"
**Claude:** Deixei os seis commits na branch. A revisão final achou um erro meu — o spec dizia cobrir a Seção 5, mas "rotas protegidas" não estava implementado. Corrigi o spec.

**Eu:** "Ao realizar as implementações, esqueça commits e etc, eu cuido disso"
**Claude:** Salvei na memória, anotando onde mora o atrito: as skills do superpowers commitam sozinhas, então preciso omitir os passos de commit dos planos e instruir cada subagente explicitamente.

**Eu:** "Crie para mim agora um readme.md com uma explicação básica do que se trata o projeto e como rodar ele"
**Claude:** Criei o README. Avisei que **nunca executei o `docker compose up`** — as instruções de Docker são corretas em teoria, não verificadas na prática.

**Eu:** "Gere um arquivo markdown dessa conversa e das principais ideias contidas nela"
**Claude:** Escrevi este documento como registro de decisões, não transcrição — o que tem valor daqui a semanas são os porquês, não o passo a passo.

**Eu:** "Vamos mexer no app 'catalago agora'. Me fale o que você entendo do que precisa ser incluido nesse app até agora."
**Claude:** Expliquei que o `catalogo` carrega quase todo o resto: três modelos e quatro critérios. Recomendei fatiar em três e levantei cinco ambiguidades do documento que eu não podia resolver sozinho.

**Eu:** "Todo usuário pode cadastrar um item, não só o admin. Porém cada usuário só pode excluir seu próprio item, o admin pode excluir qualquer item"
**Claude:** Sinalizei que isso diverge do documento em três pontos. Notei que a mudança resolve de graça a dúvida do Django Admin: o CRUD tem que ser telas próprias.

**Eu:** "Dono ou admin" / "Sim — exclui e leva as preferências junto"
**Claude:** Avisei **uma vez** que o CASCADE derruba um critério testável da Seção 5 e apaga dados de terceiros. Você manteve; registrei como risco aceito e não voltei ao assunto.

**Eu:** "upload na capa. o usuário pode comentar a própria preferencia."
**Claude:** Listei as consequências: Pillow vira dependência, `capa_url` vira `capa`, e o `urls.py` precisa servir media. Quarta divergência do documento.

**Eu:** "pode levar" / "is_staff" / "Lista + detalhe"
**Claude:** Fechei o design e escrevi o spec com cinco divergências registradas. Alertei que `is_staff` contraria a Seção 4, mas evita duas noções de admin divergindo entre si.

**Eu:** "aprovado, escreve o plano"
**Claude:** Escrevi o plano em cinco tarefas, **sem passos de commit** conforme sua instrução. Documentei as armadilhas do `enctype` e do `static()` para media.

**Eu:** "1"
**Claude:** Despachei os subagentes. O da Task 1 parou e perguntou: o plano dizia 8 testes de baseline, eram 10. O erro era meu; corrigi o plano e as contagens seguintes.

**Eu:** "Retome de onde parou"
**Claude:** Como você interrompeu o revisor de qualidade, fiz a revisão eu mesmo em vez de reenviá-lo. Achei um `.claude/launch.json` que o subagente da Task 3 jurou ter apagado.

**Eu:** [imagem da paleta] "Use a paleta de cores contida na imagem para o projeto. Crie uma navbar com o icon de um livro aberto meio mágico e o nome catálogo ao lado, deixe a fonte por volta de uns 20px."
**Claude:** Apliquei a paleta via `@theme` do Tailwind v4 e criei a navbar. Direção estética: grimório — Fraunces e Karla, cacau com corte dourado. Acrescentei uma sexta cor derivada para o fundo.

**Eu:** "Errei algo, o nome não é catálogo e sim 'Gostoteca', corrija isso e continue"
**Claude:** Corrigi nos três lugares. Refiz o ícone: as faíscas tinham 3px e sumiam na navbar. Agora são duas, maiores, e extraí o SVG para um partial — estava triplicado.

**Eu:** "Atualize o arquivo ... colocando conversas contidas nessa sessão ... Depois disso crie uma tela para erro 404."
**Claude:** Atualizei este documento com o diálogo e corrigi as partes que envelheceram. Criei a tela de 404 no tom do grimório (ver seção 16).

## 16. Tela de 404

`templates/404.html`, encontrada automaticamente pelo Django quando `DEBUG=False`.

**Ela não aparece em desenvolvimento.** Com `DEBUG=True` o Django mostra a própria página de debug, com a lista de rotas. Para ver a tela real é preciso `DEBUG=False` e `ALLOWED_HOSTS` preenchido — e nesse modo o `static()` para de servir as capas, porque ele só funciona sob `DEBUG`.

---

## Documentos relacionados

- `docs/superpowers/specs/2026-07-14-login-cadastro-design.md` — design das telas de autenticação
- `docs/superpowers/plans/2026-07-14-login-cadastro.md` — plano em 4 tarefas TDD
- `docs/superpowers/specs/2026-07-14-catalogo-item-design.md` — design da fatia 1 do catálogo, com as 5 divergências e os riscos aceitos
- `docs/superpowers/plans/2026-07-14-catalogo-item.md` — plano em 5 tarefas TDD, sem passos de commit
