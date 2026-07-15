# Design — Item e catálogo (app `catalogo`, fatia 1 de 3)

**Data:** 2026-07-14
**Projeto:** Gostoteca (Atividade 03 — Aplicação CRUD, UFPB)
**Escopo:** Modelo `Item`, listagem, detalhe e CRUD, com autorização.

## Contexto

O app `catalogo` está vazio (só o esqueleto do `startapp`). Ele carrega três dos quatro modelos do documento e a maior parte dos critérios da Seção 5 — grande demais para um spec só. Está dividido em três fatias:

| Fatia | Conteúdo | Estado |
|---|---|---|
| **1** | `Item` + lista + detalhe + CRUD + `LoginRequiredMixin` | **Este spec** |
| 2 | `Preferencia` (nota, opinião, unicidade, só-o-dono) | Depois |
| 3 | `Comentario` (camada social) | Depois |

O que já existe: Django 6.0.7, SQLite, `usuarios.Usuario` com autenticação completa (cadastro, login, logout), `MEDIA_URL`/`MEDIA_ROOT` configurados mas sem uso, e `LOGIN_REDIRECT_URL = '/catalogo/'` apontando para o vazio (404).

Esta fatia fecha o critério da Seção 5 que ficou pendente: **"rotas protegidas exigem login"**.

## Decisões tomadas

| Decisão | Escolha | Motivo |
|---|---|---|
| Quem cria item | Qualquer usuário logado | Escolha do usuário (diverge do documento) |
| Quem edita/exclui | Dono ou admin | Escolha do usuário; simétrico entre editar e excluir |
| O que é "admin" | `is_staff` | Uma noção só de admin. Como `is_staff` já controla o acesso ao `/admin/`, usar Group criaria duas noções que podem divergir |
| Autorização | `DonoOuAdminMixin(UserPassesTestMixin)` | O `handle_no_permission()` do `AccessMixin` já entrega 403 para logado e redirect para anônimo, sem configuração — exatamente o que a Seção 6 pede |
| Capa | `ImageField` + Pillow | Escolha do usuário (diverge do documento). `FileField` não valida que o arquivo é imagem |
| `Item` → `Preferencia` | `CASCADE` | Escolha do usuário (diverge do documento) |
| `Usuario` → `Item` | `CASCADE` | Escolha do usuário |
| Onde mora o CRUD de item | Views próprias, não Django Admin | Usuário comum cria itens e não acessa o `/admin/` (Seção 5), logo o Admin não serve |

### Divergências em relação ao documento da atividade

Todas conscientes. **Corrigir o `.docx` ou registrar no relatório final.**

1. **Bootstrap → Tailwind** (Seção 2). Herdada da fatia de autenticação.
2. **Qualquer usuário cria itens** (Seções 1, 4 e 5). O documento diz que o administrador gerencia o catálogo e anota `criado_por` como "FK → usuario (**admin**)". A implementação permite que qualquer usuário logado cadastre, e o `criado_por` passa a significar "dono", não "autoridade".
3. **`capa_url` texto → `capa` upload** (Seção 4). O documento especifica `capa_url texto, opcional`, isto é, uma URL. A implementação usa upload de arquivo. O campo foi renomeado porque `capa_url` mentiria sobre o próprio conteúdo.
4. **"Remoção de item em uso é bloqueada" não será implementado** (Seção 5). O documento traz isso como critério de aceitação; a escolha foi `CASCADE`. **Consequência para a nota:** a Seção 6 exige "cada critério de aceitação com ao menos um teste automatizado", e este critério ficará sem implementação e sem teste. A saída limpa é remover o critério do `.docx`.
5. **`papel` via Group → `is_staff`** (Seção 4). O documento diz "via Group do Django". Corrige também a afirmação do spec anterior (`2026-07-14-login-cadastro-design.md`), que dizia que o papel sairia dos Groups.

### Riscos aceitos

- **CASCADE em dois níveis.** `Usuario` → `Item` → `Preferencia`, todos CASCADE. Um usuário que exclui a própria conta apaga os itens que cadastrou **e as preferências que outras pessoas tinham nesses itens**. Perda de dados de terceiros por ação de um. Escolhido conscientemente.
- **Play CDN exige internet** (herdado da fatia anterior).

## Componentes

### `catalogo/models.py` (novo conteúdo)

```python
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

    def __str__(self):
        return f'{self.titulo} ({self.ano})'
```

`TextChoices` dá validação de `tipo` no form e no admin sem código extra. `criador`, `descricao` e `capa` são `blank=True` porque o documento os marca opcionais.

### `catalogo/mixins.py` (novo)

```python
class DonoOuAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.get_object().criado_por == self.request.user or self.request.user.is_staff
```

Em arquivo próprio porque as fatias 2 e 3 vão reusá-lo (preferência e comentário têm a mesma forma de "só o dono mexe").

### `catalogo/forms.py` (novo)

`ItemForm(FormEstilizado, ModelForm)` com `fields = ('titulo', 'tipo', 'ano', 'criador', 'descricao', 'capa')`.

**`criado_por` não aparece no form.** Ele é preenchido no `form_valid` da view a partir do `request.user`. Se estivesse no form, um POST forjado poderia atribuir autoria a outra pessoa.

### `catalogo/views.py` (novo conteúdo)

| Rota | View | Quem pode |
|---|---|---|
| `/catalogo/` | `ItemListView(LoginRequiredMixin, ListView)` | Qualquer logado |
| `/catalogo/<pk>/` | `ItemDetailView(LoginRequiredMixin, DetailView)` | Qualquer logado |
| `/catalogo/novo/` | `ItemCreateView(LoginRequiredMixin, CreateView)` | Qualquer logado |
| `/catalogo/<pk>/editar/` | `ItemUpdateView(LoginRequiredMixin, DonoOuAdminMixin, UpdateView)` | Dono ou admin |
| `/catalogo/<pk>/excluir/` | `ItemDeleteView(LoginRequiredMixin, DonoOuAdminMixin, DeleteView)` | Dono ou admin |

`LoginRequiredMixin` vem antes do `DonoOuAdminMixin` na MRO para que o anônimo seja redirecionado sem sequer buscar o objeto no banco.

### `catalogo/urls.py` (novo)

`app_name = 'catalogo'`, com as cinco rotas nomeadas: `lista`, `detalhe`, `novo`, `editar`, `excluir`.

### Templates

`catalogo/templates/catalogo/`: `item_list.html`, `item_detail.html`, `item_form.html` (compartilhado entre criar e editar) e `item_confirm_delete.html`.

## Mudanças em código existente

### Reestruturação dos templates compartilhados

`base.html` e `_campo.html` saem de `usuarios/templates/usuarios/` e vão para `templates/` na raiz do projeto, com `TEMPLATES['DIRS'] = [BASE_DIR / 'templates']`.

**Motivo:** o layout do site não pertence ao app de autenticação. Um template do catálogo fazendo `{% extends 'usuarios/base.html' %}` lê mal, e o erro se multiplicaria nas fatias 2 e 3. Afeta `login.html` e `cadastro.html`, que passam a estender `'base.html'` e incluir `'_campo.html'`.

### `_FormEstilizado` → `FormEstilizado`

O mixin perde o underscore (que o marcava como privado do módulo) porque o `catalogo/forms.py` passa a importá-lo. A revisão de qualidade da fatia anterior já havia previsto exatamente este momento.

**Onde fica:** permanece em `usuarios/forms.py`; o `catalogo` importa de lá. Criar um app `core` só para um mixin de cinco linhas seria desproporcional, e o `catalogo` já depende do `usuarios` pela FK de `criado_por` — a importação não adiciona acoplamento que ainda não exista.

### `gostoteca/settings.py`

- `LOGIN_REDIRECT_URL = reverse_lazy('catalogo:lista')` — encerra a dívida técnica do caminho literal `/catalogo/`.
- `TEMPLATES['DIRS'] = [BASE_DIR / 'templates']`.

### `gostoteca/urls.py`

- `path('catalogo/', include('catalogo.urls'))`
- `+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` sob `if settings.DEBUG`. Sem isso as capas salvam mas não aparecem — e o sintoma parece bug de upload quando é roteamento.

### `requirements.txt`

Ganha `Pillow`. Primeira dependência de terceiros do projeto; obrigatória para `ImageField`.

## Fluxo

1. **Anônimo em `/catalogo/`** → 302 para `/login/?next=/catalogo/`.
2. **Login** → 302 para `/catalogo/` (agora existe).
3. **Criar** → `/catalogo/novo/` → form válido → `criado_por = request.user` → 302 para o detalhe.
4. **Editar/excluir** → dono ou admin passam; outro usuário logado leva 403; anônimo é redirecionado.

## Tratamento de erros

| Situação | Resultado |
|---|---|
| Anônimo em qualquer rota do catálogo | 302 para `/login/?next=...` |
| Logado não-dono e não-admin em editar/excluir | 403 |
| `titulo` ou `ano` vazios | Erro de campo no form (200) |
| `tipo` fora do enum | Erro de campo no form (200), via `TextChoices` |
| Arquivo não-imagem em `capa` | Erro de campo no form (200), via `ImageField`/Pillow |
| Item inexistente | 404 |

## Testes (`catalogo/tests.py`)

1. **Anônimo em `/catalogo/` → 302 para `/login/?next=/catalogo/`.** *Fecha o critério "rotas protegidas exigem login" da Seção 5.*
2. Logado em `/catalogo/` → 200 e a lista mostra os itens.
3. Logado cria item → `criado_por` é o próprio usuário.
4. Dono edita o próprio item → 302, alteração persistida.
5. Admin (`is_staff`) edita item alheio → 302.
6. Usuário comum edita item alheio → **403**, item inalterado.
7. Dono exclui o próprio item → item some do banco.
8. Usuário comum exclui item alheio → **403**, item continua no banco.
9. Upload de capa grava o arquivo e o `item.capa` aponta para ele.
10. `tipo` fora do enum invalida o form.

**Os testes que fazem upload precisam de `@override_settings(MEDIA_ROOT=<tempdir>)`.** Sem isso eles gravam arquivos de verdade na pasta `media/` do projeto e deixam lixo a cada execução — inclusive na máquina de quem rodar o CI.

## Fora de escopo

- `Preferencia` e `Comentario` (fatias 2 e 3).
- Busca, filtro por tipo e paginação na lista — não pedidos pelo documento.
- Moderação de comentários e usuários (Seção 1) — sem critério testável no documento; provavelmente Django Admin.
- Validação de `ano` (não-futuro, mínimo) — o documento pede apenas "obrigatório".
- Limite de tamanho do upload.
