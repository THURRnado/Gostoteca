# Design — Review e exclusão de conta (fatia final)

**Data:** 2026-07-14
**Projeto:** Gostoteca (Atividade 03 — Aplicação CRUD, UFPB)
**Escopo:** Modelo `Review` com CRUD e autorização, contagem no catálogo, e exclusão da própria conta.

## Contexto

Última fatia do projeto. O que já existe:

- `usuarios.Usuario(AbstractUser)` com email único e obrigatório; cadastro, login e logout. 10 testes.
- `catalogo.Item` com lista, detalhe e CRUD (criar: qualquer logado; editar/excluir: dono ou admin). 23 testes.
- `catalogo/mixins.py` com `DonoOuAdminMixin`.
- Paleta âmbar/ferrugem via `@theme` do Tailwind v4; `templates/base.html`, `_campo.html` e `_marca.html` compartilhados.
- 33 testes passando, `manage.py check` limpo.

**O modelo `comentario` do documento foi eliminado por decisão do usuário.** A `Review` é a camada social inteira: nota + opinião, sem comentários aninhados.

## Decisões tomadas

| Decisão | Escolha | Motivo |
|---|---|---|
| Nome do modelo | `Review` | Escolha do usuário (documento diz `preferencia`) |
| `nota` | Obrigatória, 0 a 10 | Escolha do usuário (documento diz opcional) |
| `opiniao` | Opcional | Escolha do usuário; nome vem do documento, evita colisão com o antigo `Comentario` |
| Uma review por usuário por item | `UniqueConstraint(usuario, item)` | Documento (Seção 4) e confirmação do usuário |
| Dono do item avalia o próprio item | Permitido | Escolha do usuário; nenhuma validação a escrever |
| Editar review | **Só o dono** | Escolha do usuário: admin modera apagando, não reescrevendo opinião alheia |
| Apagar review | Dono ou admin | Escolha do usuário; implementa a moderação que a Seção 1 pede |
| Review duplicada | View redireciona para editar | Ver "A armadilha do UniqueConstraint" abaixo |
| Contagem no card | `annotate(Count('reviews'))` | `item.reviews.count()` no template seria N+1 |
| Onde avaliar | Página separada (`/catalogo/<pk>/avaliar/`) | Escolha do usuário; `CreateView` idiomática, igual ao `Item` |
| Exclusão de conta | Página de confirmação avisando o estrago | Escolha do usuário; torna o CASCADE honesto |

### Divergências em relação ao documento da atividade

Lista completa e acumulada do projeto. **Corrigir o `.docx` ou registrar tudo no relatório final.**

1. **Bootstrap → Tailwind** (Seção 2).
2. **Qualquer usuário cria itens** (Seções 1, 4, 5). O documento reserva isso ao administrador.
3. **`capa_url` texto → `capa` upload** (Seção 4).
4. **"Remoção de item em uso é bloqueada" não implementado** (Seção 5). O CASCADE foi escolhido conscientemente. **Critério morto.**
5. **`papel` via Group → `is_staff`** (Seção 4).
6. **`preferencia` → `review`** (Seção 4). Renomeação.
7. **`nota` opcional → obrigatória** (Seção 4).
8. **Modelo `comentario` eliminado** (Seções 1, 4, 5). O documento define CRUD sobre quatro entidades; serão entregues três. **Critério morto:** "usuário comenta a preferência de outro usuário; edita/remove apenas o próprio comentário". Também some a descrição da Seção 1 ("comenta as preferências de outros usuários") e o subtítulo "com elementos de rede social".
9. **Admin apaga reviews** (não previsto na Seção 5, mas implementa a moderação que a Seção 1 pede e que estava sem dono).

### Cobertura dos critérios da Seção 5 ao fim desta fatia

| Critério | Estado |
|---|---|
| Cadastro, login e logout; senha com hash; rotas protegidas exigem login | ✅ Feito |
| Usuário comum não acessa a administração | ⚠️ Funciona (o Django Admin barra não-staff), mas **sem teste** |
| Administrador gerencia o catálogo | ✅ Via `is_staff` no `DonoOuAdminMixin` |
| Admin cria, edita e remove itens | ⚠️ Alterado: qualquer usuário cria; editar/excluir é dono ou admin |
| Campos obrigatórios validados | ✅ Feito |
| **Remoção de item em uso é bloqueada** | ❌ **Não será implementado** (CASCADE) |
| Usuário adiciona item como preferência com nota/opinião, sem repetir o mesmo item | ✅ Esta fatia |
| Edita e remove; altera apenas as próprias | ✅ Esta fatia |
| **Usuário comenta a preferência de outro** | ❌ **Não será implementado** (modelo eliminado) |
| Nota respeita o intervalo 0–10 | ✅ Esta fatia |
| Todas as funcionalidades acessíveis via navegador | ✅ Feito |

**Dois critérios ficam sem implementação e sem teste.** A Seção 6 exige "cada critério de aceitação com ao menos um teste automatizado".

Esta fatia também fecha o CRUD que a Seção 1 pede: *"remoção dos mesmos **e da conta** (delete)"*.

### Riscos aceitos

- **CASCADE em três níveis.** `Usuario` → `Item` → `Review`, e `Usuario` → `Review`. Excluir uma conta apaga os itens dela **e as reviews que outras pessoas escreveram nesses itens**. A tela de confirmação mostra os números antes de executar.
- **Play CDN e Google Fonts exigem internet** (herdado).

## Componentes

### `catalogo/models.py` — novo modelo

```python
class Review(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews'
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='reviews')
    nota = models.PositiveSmallIntegerField('nota (0 a 10)', validators=[MaxValueValidator(10)])
    opiniao = models.TextField('opinião', blank=True)
    data = models.DateTimeField('data', auto_now_add=True)

    class Meta:
        ordering = ('-data',)
        verbose_name = 'review'
        verbose_name_plural = 'reviews'
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'item'], name='review_unica_por_usuario_e_item'
            ),
        ]

    def __str__(self):
        return f'{self.usuario} — {self.item.titulo}: {self.nota}'
```

`PositiveSmallIntegerField` já impõe o piso zero (no banco e no form), então **só o teto precisa de validador**. O rótulo carrega a regra para a tela.

### `catalogo/mixins.py` — generalizado

```python
class DonoMixin(UserPassesTestMixin):
    """Libera o objeto apenas para quem o criou.

    O handle_no_permission() do AccessMixin ja faz a distincao certa sozinho:
    403 para usuario autenticado, redirect para anonimo. Nao mexa em raise_exception.
    """

    campo_dono = 'criado_por'

    def test_func(self):
        return getattr(self.get_object(), self.campo_dono) == self.request.user


class DonoOuAdminMixin(DonoMixin):
    """Libera tambem para quem tem is_staff."""

    def test_func(self):
        return super().test_func() or self.request.user.is_staff
```

**As views do `Item` não mudam** — `campo_dono` continua `criado_por` por padrão. As da review declaram `campo_dono = 'usuario'`.

A separação entre os dois mixins **é** a regra do usuário: editar review usa `DonoMixin`, apagar usa `DonoOuAdminMixin`.

### `catalogo/forms.py`

```python
class ReviewForm(FormEstilizado, forms.ModelForm):
    class Meta:
        model = Review
        fields = ('nota', 'opiniao')
```

`usuario` e `item` não aparecem no form — a view os preenche. Se estivessem, um POST forjado atribuiria a review a outra pessoa ou a outro item.

### `catalogo/views.py`

| Rota | Nome | View | Quem pode |
|---|---|---|---|
| `/catalogo/<int:item_pk>/avaliar/` | `catalogo:avaliar` | `ReviewCreateView(LoginRequiredMixin, CreateView)` | Qualquer logado |
| `/catalogo/review/<int:pk>/editar/` | `catalogo:review_editar` | `ReviewUpdateView(LoginRequiredMixin, DonoMixin, UpdateView)` | Só o dono |
| `/catalogo/review/<int:pk>/excluir/` | `catalogo:review_excluir` | `ReviewDeleteView(LoginRequiredMixin, DonoOuAdminMixin, DeleteView)` | Dono ou admin |

A rota da conta é `/conta/excluir/`, nome `conta_excluir`, no `usuarios/urls.py` (sem namespace, como as demais daquele app).

Mudanças nas views existentes:

- `ItemListView.get_queryset()` → `.annotate(num_reviews=Count('reviews'))`
- `ItemDetailView.get_context_data()` → `reviews` (com `select_related('usuario')`) e `minha_review`

### A armadilha do `UniqueConstraint`

O `usuario` fica fora do `ReviewForm` (preenchido na view). Só que o `ModelForm` do Django **exclui da validação os campos ausentes do form**, e uma restrição composta é pulada inteira se qualquer campo dela estiver excluído. Consequência: o `UNIQUE (usuario, item)` **nunca é checado no formulário**, e a segunda review viraria `IntegrityError` — um 500, não um erro de campo.

**Solução:** o `dispatch` da `ReviewCreateView` verifica se já existe review daquele usuário para aquele item e, se existir, redireciona para a tela de editar.

```python
def dispatch(self, request, *args, **kwargs):
    if request.user.is_authenticated:
        existente = Review.objects.filter(
            usuario=request.user, item_id=self.kwargs['item_pk']
        ).first()
        if existente:
            return redirect('catalogo:review_editar', pk=existente.pk)
    return super().dispatch(request, *args, **kwargs)
```

O `UniqueConstraint` permanece no banco como a garantia real. O redirect é UX, não integridade — e transforma um erro numa navegação útil ("você já avaliou isto, aqui está sua nota").

**Limitação aceita:** dois POSTs simultâneos ainda produziriam `IntegrityError`. Irrelevante nesta escala.

### `usuarios/views.py` — exclusão de conta

```python
class ContaDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'usuarios/conta_confirm_delete.html'
    success_url = reverse_lazy('login')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['meus_itens'] = self.request.user.itens.count()
        contexto['reviews_de_terceiros'] = (
            Review.objects.filter(item__criado_por=self.request.user)
            .exclude(usuario=self.request.user)
            .count()
        )
        return contexto

    def form_valid(self, form):
        usuario = self.request.user
        logout(self.request)
        usuario.delete()
        return HttpResponseRedirect(self.get_success_url())
```

`get_object()` devolve `request.user` — **não há `pk` na URL**, então é impossível apagar a conta de outra pessoa por essa rota. É mais forte que qualquer checagem de permissão.

O `logout()` vem **antes** do `delete()` para encerrar a sessão de forma limpa.

**Acoplamento novo:** `usuarios/views.py` passa a importar `catalogo.models.Review`. Hoje a dependência é de mão única (`catalogo` → `usuarios`). Não há ciclo em Python — o `catalogo` referencia o usuário por string via `AUTH_USER_MODEL` —, mas os dois apps passam a se conhecer. Com dois apps é aceitável; com cinco seria hora de um app `core`.

### Templates

- `catalogo/templates/catalogo/review_form.html` — serve criar e editar (`{% if object %}`)
- `catalogo/templates/catalogo/review_confirm_delete.html`
- `catalogo/templates/catalogo/_review.html` — partial com o layout pedido: **nome do usuário, nota embaixo, opinião embaixo se existir**
- `usuarios/templates/usuarios/conta_confirm_delete.html`

O `_review.html` fica **dentro do app**, não em `templates/` na raiz: ele só é usado pelo detalhe do item. A raiz é para o que atravessa apps — `base.html`, `_campo.html` e `_marca.html`.
- `item_detail.html` — lista de reviews + botão "Avaliar" / "Editar minha avaliação"
- `item_list.html` — contagem de reviews no card
- `base.html` — link "Excluir conta" na navbar

## Fluxo

1. **Avaliar:** detalhe do item → "Avaliar" → `/catalogo/<pk>/avaliar/` → form válido → `usuario` e `item` preenchidos na view → 302 para o detalhe do item.
2. **Já avaliou:** "Avaliar" → 302 direto para `/catalogo/review/<pk>/editar/`.
3. **Editar:** só o dono passa; admin e terceiros levam 403.
4. **Apagar:** dono ou admin passam; terceiros levam 403.
5. **Excluir conta:** `/conta/excluir/` → confirmação com os números → POST → logout → delete → 302 para o login.

## Tratamento de erros

| Situação | Resultado |
|---|---|
| Anônimo em qualquer rota de review ou conta | 302 para `/login/?next=...` |
| `nota` vazia | Erro de campo no form (200) |
| `nota` > 10 ou < 0 | Erro de campo no form (200) |
| `opiniao` vazia | Válido |
| Segunda tentativa de avaliar o mesmo item | 302 para editar a review existente |
| Não-dono editando review | 403 (inclusive admin) |
| Terceiro apagando review | 403 |
| Item ou review inexistente | 404 |

## Testes

**`catalogo/tests.py`** — modelo e views da review:

1. `nota` obrigatória: form sem nota é inválido.
2. `nota = 0` e `nota = 10` são válidas (as bordas).
3. `nota = 11` é inválida.
4. `opiniao` vazia é válida.
5. Review criada pertence ao usuário logado e ao item da URL.
6. `usuario`/`item` forjados no POST são ignorados.
7. Segunda visita a `/avaliar/` → 302 para editar, sem criar segunda review.
8. `UniqueConstraint` barra duplicata no banco (`IntegrityError` ao forçar via ORM).
9. Dono do item consegue avaliar o próprio item.
10. Dono edita a própria review.
11. **Admin não edita review alheia → 403.**
12. Terceiro não edita review alheia → 403.
13. Dono apaga a própria review.
14. **Admin apaga review alheia → 302.**
15. Terceiro apagando review alheia → 403.
16. Anônimo em avaliar/editar/excluir → 302 para o login.
17. Card do catálogo mostra a contagem de reviews.
18. Detalhe do item lista as reviews existentes.

**`usuarios/tests.py`** — exclusão de conta:

19. Anônimo em `/conta/excluir/` → 302 para o login.
20. GET mostra a contagem de itens e de reviews de terceiros que serão destruídos.
21. POST apaga a conta e encerra a sessão.
22. POST apaga em cascata os itens do usuário **e as reviews de terceiros nesses itens** — o teste que torna o risco do CASCADE visível em vez de teórico.

Total esperado: **33 atuais + ~22 = ~55**.

## Fora de escopo

- Modelo `Comentario` — eliminado por decisão do usuário.
- "Remoção de item em uso é bloqueada" — descartado pela escolha do CASCADE.
- Página `/conta/` com dados do perfil e edição — só a exclusão foi pedida.
- Média das notas por item — não pedida; só a contagem.
- Busca, filtro e paginação — não pedidos pelo documento.
- Teste de "usuário comum não acessa a administração" — lacuna conhecida, não coberta por esta fatia.
