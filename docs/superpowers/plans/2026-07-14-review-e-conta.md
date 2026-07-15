# Review e Exclusão de Conta — Plano de Implementação (fatia final)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o modelo `Review` com CRUD autorizado, contagem no catálogo, e a exclusão da própria conta — fechando o último CRUD que o documento da atividade pede.

**Architecture:** `Review` liga usuário e item com `UniqueConstraint`, nota obrigatória de 0 a 10 e opinião opcional. Os mixins de autorização são generalizados por um atributo `campo_dono`, permitindo que editar (só o dono) e apagar (dono ou admin) usem mixins diferentes sobre o mesmo objeto. A exclusão de conta opera sobre `request.user`, sem `pk` na URL.

**Tech Stack:** Django 6.0.7, SQLite, Pillow, Tailwind CSS v4 (Play CDN), `manage.py test`.

**Referência:** [Spec aprovado](../specs/2026-07-14-review-e-conta-design.md)

---

## ⚠️ NÃO COMMITE

**O usuário cuida do git sozinho.** Este plano não tem passos de commit, e isso é deliberado — não é esquecimento. Não rode `git add`, `git commit`, `git branch` ou qualquer comando de git que altere estado. Deixe todas as alterações no working tree.

**Se criar arquivo temporário — script, `.claude/launch.json`, o que for — apague antes de terminar e confirme com `git status --short`.** Já aconteceu de um implementador afirmar que apagou e não ter apagado. Se você não apagar, não diga que apagou.

## Notas de contexto para quem implementar

- **Rodar tudo de dentro de `Gostoteca/`** (onde está o `manage.py`), com `.\venv\Scripts\python.exe`. Windows/PowerShell. **O repositório git está em `Gostoteca/`**, não no diretório pai.
- **Estado inicial: 33 testes passando.** Se não for 33, pare e reporte.
- **`admin` significa `is_staff`.** Não é Group nem `is_superuser`.
- **O `handle_no_permission()` do `AccessMixin` já entrega 403 para logado e redirect para anônimo, sem configuração.** Não mexa em `raise_exception`.
- **O modelo `Comentario` do documento não existe e não deve ser criado.** Foi eliminado por decisão do usuário; a `Review` é a camada social inteira.
- **Padrão do projeto:** o dono de um objeto nunca vem do POST. Fica fora do form e é preenchido na view.

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `catalogo/models.py` (modificar) | Acrescentar `Review` |
| `catalogo/mixins.py` (modificar) | `DonoMixin` + `DonoOuAdminMixin`, parametrizados por `campo_dono` |
| `catalogo/forms.py` (modificar) | Acrescentar `ReviewForm` |
| `catalogo/views.py` (modificar) | 3 views de review; `annotate` na lista; reviews no detalhe |
| `catalogo/urls.py` (modificar) | 3 rotas de review |
| `catalogo/templates/catalogo/review_form.html` (criar) | Criar e editar review |
| `catalogo/templates/catalogo/review_confirm_delete.html` (criar) | Confirmação de exclusão |
| `catalogo/templates/catalogo/_review.html` (criar) | Layout de uma review: usuário / nota / opinião |
| `catalogo/templates/catalogo/item_detail.html` (modificar) | Lista de reviews + botão avaliar |
| `catalogo/templates/catalogo/item_list.html` (modificar) | Contagem no card |
| `catalogo/tests.py` (modificar) | Testes de modelo e das views de review |
| `usuarios/views.py` (modificar) | `ContaDeleteView` |
| `usuarios/urls.py` (modificar) | Rota `conta/excluir/` |
| `usuarios/templates/usuarios/conta_confirm_delete.html` (criar) | Confirmação com os números do CASCADE |
| `usuarios/tests.py` (modificar) | Testes da exclusão de conta |
| `templates/base.html` (modificar) | Link "Excluir conta" na navbar |

---

## Task 1: Modelo `Review`

**Files:**
- Modify: `catalogo/models.py`, `catalogo/tests.py`
- Create: `catalogo/migrations/0002_review.py` (gerado)

- [ ] **Step 1: Confirmar o ponto de partida**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 33 tests` / `OK`

Se não for 33/33, pare e reporte.

- [ ] **Step 2: Escrever os testes que falham**

No topo de `catalogo/tests.py`, acrescente aos imports existentes:

```python
from django.db import IntegrityError, transaction
```

E troque a linha `from .models import Item` por:

```python
from .models import Item, Review
```

Depois acrescente ao final do arquivo:

```python
class ReviewModelTest(TestCase):
    def setUp(self):
        self.usuario = cria_usuario()
        self.item = Item.objects.create(
            titulo='Hollow Knight',
            tipo=Item.Tipo.JOGO,
            ano=2017,
            criado_por=self.usuario,
        )

    def test_str_mostra_usuario_item_e_nota(self):
        review = Review.objects.create(usuario=self.usuario, item=self.item, nota=9)

        self.assertEqual(str(review), 'arthur — Hollow Knight: 9')

    def test_opiniao_nasce_vazia(self):
        review = Review.objects.create(usuario=self.usuario, item=self.item, nota=7)

        self.assertEqual(review.opiniao, '')

    def test_notas_das_bordas_sao_validas(self):
        for nota in (0, 10):
            with self.subTest(nota=nota):
                review = Review(usuario=self.usuario, item=self.item, nota=nota)

                review.full_clean()  # nao deve levantar

    def test_nota_acima_de_dez_e_rejeitada(self):
        review = Review(usuario=self.usuario, item=self.item, nota=11)

        with self.assertRaises(ValidationError):
            review.full_clean()

    def test_review_duplicada_e_barrada_pelo_banco(self):
        Review.objects.create(usuario=self.usuario, item=self.item, nota=8)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Review.objects.create(usuario=self.usuario, item=self.item, nota=3)
```

**O `transaction.atomic()` no último teste não é enfeite.** Um `IntegrityError` dentro de um `TestCase` deixa a transação quebrada, e o teardown falha com "An error occurred in the current transaction". O `atomic()` isola a falha num savepoint.

- [ ] **Step 3: Rodar para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test catalogo -v 2`
Expected: FAIL — `ImportError: cannot import name 'Review' from 'catalogo.models'`

- [ ] **Step 4: Escrever o modelo**

Em `catalogo/models.py`, acrescente aos imports do topo:

```python
from django.core.validators import MaxValueValidator
```

E acrescente ao final do arquivo, depois da classe `Item`:

```python
class Review(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='usuário',
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='item',
    )
    nota = models.PositiveSmallIntegerField('nota (0 a 10)', validators=[MaxValueValidator(10)])
    opiniao = models.TextField('opinião', blank=True)
    data = models.DateTimeField('data', auto_now_add=True)

    class Meta:
        ordering = ('-data',)
        verbose_name = 'review'
        verbose_name_plural = 'reviews'
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'item'],
                name='review_unica_por_usuario_e_item',
            ),
        ]

    def __str__(self):
        return f'{self.usuario} — {self.item.titulo}: {self.nota}'
```

`PositiveSmallIntegerField` já impõe o piso zero — no banco e no formulário. **Só o teto precisa de validador.** O rótulo `'nota (0 a 10)'` leva a regra para a tela.

- [ ] **Step 5: Gerar e aplicar a migração**

```powershell
.\venv\Scripts\python.exe manage.py makemigrations catalogo
.\venv\Scripts\python.exe manage.py migrate
```

Expected: `Create model Review` e `Applying catalogo.0002_review... OK`.

- [ ] **Step 6: Rodar para confirmar que passam**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 38 tests` / `OK` (33 + 5 novos)

---

## Task 2: Generalizar os mixins de autorização

Refatoração pura. O critério de sucesso é **os 38 testes continuarem passando**.

**Files:**
- Modify: `catalogo/mixins.py`

- [ ] **Step 1: Reescrever o arquivo**

Substitua todo o conteúdo de `catalogo/mixins.py` por:

```python
from django.contrib.auth.mixins import UserPassesTestMixin


class DonoMixin(UserPassesTestMixin):
    """Libera o objeto apenas para quem o criou.

    Qual campo aponta para o dono varia por modelo: `Item` usa `criado_por`,
    `Review` usa `usuario`. Sobrescreva `campo_dono` na view.

    O handle_no_permission() do AccessMixin ja faz a distincao certa sozinho:
    levanta PermissionDenied (403) para usuario autenticado e redireciona
    anonimo para o login. Nao mexa em raise_exception.
    """

    campo_dono = 'criado_por'

    def test_func(self):
        return getattr(self.get_object(), self.campo_dono) == self.request.user


class DonoOuAdminMixin(DonoMixin):
    """Libera tambem para quem tem is_staff."""

    def test_func(self):
        return super().test_func() or self.request.user.is_staff
```

**As views do `Item` não mudam.** O padrão de `campo_dono` continua `criado_por`, e `DonoOuAdminMixin` mantém o mesmo comportamento de antes — por isso os testes existentes são a rede de segurança.

A separação entre os dois mixins existe porque a regra do usuário é assimétrica: **editar review é só do dono** (nem o admin reescreve opinião alheia) e **apagar é do dono ou do admin**.

- [ ] **Step 2: Verificar que nada regrediu**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 38 tests` / `OK`

Run: `.\venv\Scripts\python.exe manage.py check`
Expected: `System check identified no issues (0 silenced).`

**Esta task não adiciona testes.** Se `ItemUpdateViewTest` ou `ItemDeleteViewTest` quebrarem, a herança do `DonoOuAdminMixin` está errada.

---

## Task 3: Criar review

**Files:**
- Modify: `catalogo/forms.py`, `catalogo/views.py`, `catalogo/urls.py`, `catalogo/tests.py`
- Create: `catalogo/templates/catalogo/review_form.html`

- [ ] **Step 1: Escrever os testes que falham**

Acrescente ao final de `catalogo/tests.py`:

```python
class ReviewCreateViewTest(TestCase):
    def setUp(self):
        self.dono_do_item = cria_usuario('arthur')
        self.outro = cria_usuario('andre')
        self.item = Item.objects.create(
            titulo='Hollow Knight',
            tipo=Item.Tipo.JOGO,
            ano=2017,
            criado_por=self.dono_do_item,
        )
        self.url = f'/catalogo/{self.item.pk}/avaliar/'

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(resposta, f'/login/?next={self.url}')

    def test_logado_ve_o_formulario(self):
        self.client.login(username='andre', password='senha-forte-123')

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 200)

    def test_review_criada_pertence_ao_usuario_e_ao_item_da_url(self):
        self.client.login(username='andre', password='senha-forte-123')

        resposta = self.client.post(self.url, data={'nota': 9, 'opiniao': 'Excelente.'})

        review = Review.objects.get()
        self.assertEqual(review.usuario, self.outro)
        self.assertEqual(review.item, self.item)
        self.assertEqual(review.nota, 9)
        self.assertRedirects(resposta, f'/catalogo/{self.item.pk}/')

    def test_usuario_e_item_forjados_no_post_sao_ignorados(self):
        outro_item = Item.objects.create(
            titulo='Duna', tipo=Item.Tipo.LIVRO, ano=1965, criado_por=self.dono_do_item
        )
        self.client.login(username='andre', password='senha-forte-123')

        self.client.post(
            self.url,
            data={
                'nota': 9,
                'opiniao': '',
                'usuario': self.dono_do_item.pk,
                'item': outro_item.pk,
            },
        )

        review = Review.objects.get()
        self.assertEqual(review.usuario, self.outro)
        self.assertEqual(review.item, self.item)

    def test_opiniao_vazia_e_aceita(self):
        self.client.login(username='andre', password='senha-forte-123')

        self.client.post(self.url, data={'nota': 5, 'opiniao': ''})

        self.assertEqual(Review.objects.get().opiniao, '')

    def test_nota_vazia_nao_cria_review(self):
        self.client.login(username='andre', password='senha-forte-123')

        resposta = self.client.post(self.url, data={'nota': '', 'opiniao': 'Sem nota.'})

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Review.objects.exists())

    def test_nota_acima_de_dez_nao_cria_review(self):
        self.client.login(username='andre', password='senha-forte-123')

        resposta = self.client.post(self.url, data={'nota': 11, 'opiniao': ''})

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Review.objects.exists())

    def test_segunda_tentativa_redireciona_para_editar(self):
        review = Review.objects.create(usuario=self.outro, item=self.item, nota=7)
        self.client.login(username='andre', password='senha-forte-123')

        resposta = self.client.get(self.url)

        self.assertRedirects(resposta, f'/catalogo/review/{review.pk}/editar/')
        self.assertEqual(Review.objects.count(), 1)

    def test_dono_do_item_pode_avaliar_o_proprio_item(self):
        self.client.login(username='arthur', password='senha-forte-123')

        self.client.post(self.url, data={'nota': 10, 'opiniao': 'Meu próprio item.'})

        self.assertEqual(Review.objects.get().usuario, self.dono_do_item)
```

O `test_segunda_tentativa_redireciona_para_editar` é o que trava a solução da armadilha do `UniqueConstraint`: sem o redirect, um POST ali viraria `IntegrityError` (500).

- [ ] **Step 2: Rodar para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test catalogo.tests.ReviewCreateViewTest -v 2`
Expected: FAIL — 404, porque a rota não existe.

- [ ] **Step 3: Acrescentar o form**

Substitua todo o conteúdo de `catalogo/forms.py` por:

```python
from django import forms

from usuarios.forms import FormEstilizado

from .models import Item, Review


class ItemForm(FormEstilizado, forms.ModelForm):
    class Meta:
        model = Item
        fields = ('titulo', 'tipo', 'ano', 'criador', 'descricao', 'capa')


class ReviewForm(FormEstilizado, forms.ModelForm):
    class Meta:
        model = Review
        fields = ('nota', 'opiniao')
```

**`usuario` e `item` não estão em `fields`, de propósito.** A view os preenche a partir do `request.user` e da URL. Se estivessem, um POST forjado atribuiria a review a outra pessoa ou a outro item — é o que o `test_usuario_e_item_forjados_no_post_sao_ignorados` trava.

- [ ] **Step 4: Acrescentar a view**

Substitua todo o conteúdo de `catalogo/views.py` por:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ItemForm, ReviewForm
from .mixins import DonoOuAdminMixin
from .models import Item, Review


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


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'catalogo/review_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.item = get_object_or_404(Item, pk=kwargs['item_pk'])

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            existente = Review.objects.filter(usuario=request.user, item=self.item).first()
            if existente:
                return redirect('catalogo:review_editar', pk=existente.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['item'] = self.item
        return contexto

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        form.instance.item = self.item
        return super().form_valid(form)

    def get_success_url(self):
        return self.item.get_absolute_url()
```

Três detalhes que importam:

O `setup()` roda **antes** do `dispatch()` e busca o item uma vez só, deixando-o disponível em todos os métodos. Sem isso, seriam três `get_object_or_404` por request.

O `dispatch()` resolve a armadilha do `UniqueConstraint`: como o `usuario` fica fora do form, o Django pula a validação da restrição composta, e a segunda review estouraria `IntegrityError`. O redirect evita que o caso chegue ao form.

O `get_success_url()` é obrigatório: a `CreateView` por padrão chamaria `self.object.get_absolute_url()`, e a `Review` não tem esse método — o destino é o **item**, não a review.

- [ ] **Step 5: Registrar a rota**

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
    path('<int:item_pk>/avaliar/', views.ReviewCreateView.as_view(), name='avaliar'),
]
```

- [ ] **Step 6: Criar `catalogo/templates/catalogo/review_form.html`**

```html
{% extends 'base.html' %}

{% block titulo %}{% if object %}Editar avaliação{% else %}Avaliar{% endif %} {{ item.titulo }} — Gostoteca{% endblock %}

{% block conteudo %}
<main class="mx-auto max-w-2xl p-6">
  <a href="{{ item.get_absolute_url }}"
     class="text-sm font-medium text-ferrugem underline decoration-ambar/50 underline-offset-4 hover:text-cacau">
    ← Voltar para {{ item.titulo }}
  </a>

  <h1 class="mt-4 mb-6 font-display text-3xl font-semibold tracking-tight text-cacau">
    {% if object %}Editar minha avaliação{% else %}Avaliar {{ item.titulo }}{% endif %}
  </h1>

  <form method="post" class="space-y-4 rounded-xl border border-areia bg-white p-6 shadow-sm">
    {% csrf_token %}
    {% for campo in form %}{% include '_campo.html' %}{% endfor %}
    <div class="flex gap-3 border-t border-areia pt-5">
      <button type="submit"
              class="rounded-lg bg-cacau px-5 py-2 font-semibold text-areia transition-colors hover:bg-ferrugem">
        Salvar
      </button>
      <a href="{{ item.get_absolute_url }}"
         class="rounded-lg px-4 py-2 font-medium text-ferrugem transition-colors hover:bg-areia/40">Cancelar</a>
    </div>
  </form>
</main>
{% endblock %}
```

O `{% if object %}` faz o mesmo template servir criar e editar — na `CreateView` o `object` é `None`. A Task 4 usa este mesmo arquivo, e por isso ele já traz o `item` no contexto de ambas.

**Sem `enctype`:** a review não tem upload.

- [ ] **Step 7: Rodar a suíte inteira**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 47 tests` — **46 OK e 1 erro esperado.**

`test_segunda_tentativa_redireciona_para_editar` vai falhar com `NoReverseMatch: Reverse for 'review_editar' not found`. **Isso é um defeito de sequenciamento deste plano, não do seu trabalho.** O teste exercita o `redirect()` do `dispatch`, que aponta para uma rota criada só na Task 4. Ele fecha lá.

**Não crie a view de editar para fazê-lo passar** — é escopo da Task 4. Siga em frente; a Task 4 leva a suíte a 55/55.

---

## Task 4: Editar e apagar review

**Files:**
- Modify: `catalogo/views.py`, `catalogo/urls.py`, `catalogo/tests.py`
- Create: `catalogo/templates/catalogo/review_confirm_delete.html`

- [ ] **Step 1: Escrever os testes que falham**

Acrescente ao final de `catalogo/tests.py`:

```python
class ReviewUpdateViewTest(TestCase):
    def setUp(self):
        self.dono = cria_usuario('arthur')
        self.outro = cria_usuario('andre')
        self.admin = cria_usuario('chefe', is_staff=True)
        self.item = Item.objects.create(
            titulo='Hollow Knight', tipo=Item.Tipo.JOGO, ano=2017, criado_por=self.outro
        )
        self.review = Review.objects.create(usuario=self.dono, item=self.item, nota=7)
        self.url = f'/catalogo/review/{self.review.pk}/editar/'

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(resposta, f'/login/?next={self.url}')

    def test_dono_edita_a_propria_review(self):
        self.client.login(username='arthur', password='senha-forte-123')

        self.client.post(self.url, data={'nota': 10, 'opiniao': 'Mudei de ideia.'})

        self.review.refresh_from_db()
        self.assertEqual(self.review.nota, 10)
        self.assertEqual(self.review.opiniao, 'Mudei de ideia.')

    def test_admin_nao_edita_review_alheia(self):
        self.client.login(username='chefe', password='senha-forte-123')

        resposta = self.client.post(self.url, data={'nota': 1, 'opiniao': 'Reescrito.'})

        self.assertEqual(resposta.status_code, 403)
        self.review.refresh_from_db()
        self.assertEqual(self.review.nota, 7)

    def test_outro_usuario_nao_edita_review_alheia(self):
        self.client.login(username='andre', password='senha-forte-123')

        resposta = self.client.post(self.url, data={'nota': 1, 'opiniao': 'Vandalizado.'})

        self.assertEqual(resposta.status_code, 403)
        self.review.refresh_from_db()
        self.assertEqual(self.review.nota, 7)


class ReviewDeleteViewTest(TestCase):
    def setUp(self):
        self.dono = cria_usuario('arthur')
        self.outro = cria_usuario('andre')
        self.admin = cria_usuario('chefe', is_staff=True)
        self.item = Item.objects.create(
            titulo='Hollow Knight', tipo=Item.Tipo.JOGO, ano=2017, criado_por=self.outro
        )
        self.review = Review.objects.create(usuario=self.dono, item=self.item, nota=7)
        self.url = f'/catalogo/review/{self.review.pk}/excluir/'

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(resposta, f'/login/?next={self.url}')

    def test_dono_apaga_a_propria_review(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.post(self.url)

        self.assertRedirects(resposta, f'/catalogo/{self.item.pk}/')
        self.assertFalse(Review.objects.filter(pk=self.review.pk).exists())

    def test_admin_apaga_review_alheia(self):
        self.client.login(username='chefe', password='senha-forte-123')

        self.client.post(self.url)

        self.assertFalse(Review.objects.filter(pk=self.review.pk).exists())

    def test_outro_usuario_nao_apaga_review_alheia(self):
        self.client.login(username='andre', password='senha-forte-123')

        resposta = self.client.post(self.url)

        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(Review.objects.filter(pk=self.review.pk).exists())
```

O par `test_admin_nao_edita_review_alheia` / `test_admin_apaga_review_alheia` é o coração desta task: **o mesmo admin, sobre o mesmo objeto, com resultados opostos.** É a regra do usuário — moderar é remover, não reescrever.

Repare que em `setUp` o item é do `andre` e a review é do `arthur`: assim os testes não confundem "dono do item" com "dono da review".

- [ ] **Step 2: Rodar para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test catalogo.tests.ReviewUpdateViewTest catalogo.tests.ReviewDeleteViewTest -v 2`
Expected: FAIL — 404, porque as rotas não existem.

- [ ] **Step 3: Acrescentar as views**

Em `catalogo/views.py`, troque a linha de import dos mixins por:

```python
from .mixins import DonoMixin, DonoOuAdminMixin
```

E acrescente ao final do arquivo:

```python
class ReviewUpdateView(LoginRequiredMixin, DonoMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'catalogo/review_form.html'
    campo_dono = 'usuario'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['item'] = self.object.item
        return contexto

    def get_success_url(self):
        return self.object.item.get_absolute_url()


class ReviewDeleteView(LoginRequiredMixin, DonoOuAdminMixin, DeleteView):
    model = Review
    template_name = 'catalogo/review_confirm_delete.html'
    campo_dono = 'usuario'

    def get_success_url(self):
        return self.object.item.get_absolute_url()
```

**`DonoMixin` em editar e `DonoOuAdminMixin` em apagar — a diferença é a regra inteira.** Não uniformize.

O `get_context_data` fornece o `item` que o `review_form.html` usa nos links de voltar e cancelar.

No `ReviewDeleteView`, o `get_success_url()` é chamado **antes** do `delete()` pela `DeletionMixin`, então `self.object.item` ainda resolve.

- [ ] **Step 4: Registrar as rotas**

Substitua todo o conteúdo de `catalogo/urls.py` por:

```python
from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.ItemListView.as_view(), name='lista'),
    path('novo/', views.ItemCreateView.as_view(), name='novo'),
    path('review/<int:pk>/editar/', views.ReviewUpdateView.as_view(), name='review_editar'),
    path('review/<int:pk>/excluir/', views.ReviewDeleteView.as_view(), name='review_excluir'),
    path('<int:pk>/', views.ItemDetailView.as_view(), name='detalhe'),
    path('<int:pk>/editar/', views.ItemUpdateView.as_view(), name='editar'),
    path('<int:pk>/excluir/', views.ItemDeleteView.as_view(), name='excluir'),
    path('<int:item_pk>/avaliar/', views.ReviewCreateView.as_view(), name='avaliar'),
]
```

As rotas de `review/` vêm **antes** das de `<int:pk>/`. Como `review` não é inteiro, não haveria conflito — mas manter literais antes de paramétricas é o hábito que evita bugs sutis.

- [ ] **Step 5: Criar `catalogo/templates/catalogo/review_confirm_delete.html`**

```html
{% extends 'base.html' %}

{% block titulo %}Excluir avaliação — Gostoteca{% endblock %}

{% block conteudo %}
<main class="mx-auto max-w-md p-6">
  <div class="rounded-xl border border-areia bg-white p-6 shadow-sm">
    <h1 class="font-display text-2xl font-semibold text-cacau">Excluir avaliação</h1>
    <p class="mt-3 text-cacau/90">
      Tem certeza que quer excluir a avaliação de
      <strong class="font-semibold">{{ object.usuario }}</strong> sobre
      <strong class="font-semibold">{{ object.item.titulo }}</strong>?
      Esta ação não pode ser desfeita.
    </p>

    <form method="post" class="mt-6 flex gap-3 border-t border-areia pt-5">
      {% csrf_token %}
      <button type="submit"
              class="rounded-lg bg-red-700 px-4 py-2 font-semibold text-white transition-colors hover:bg-red-800">
        Excluir
      </button>
      <a href="{{ object.item.get_absolute_url }}"
         class="rounded-lg px-4 py-2 font-medium text-ferrugem transition-colors hover:bg-areia/40">Cancelar</a>
    </form>
  </div>
</main>
{% endblock %}
```

Mostra o nome do autor porque o admin também chega aqui, apagando review de outra pessoa — ele precisa ver de quem é.

- [ ] **Step 6: Rodar a suíte inteira**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 55 tests` / `OK` (47 + 8 novos)

---

## Task 5: Integrar as reviews no catálogo

**Files:**
- Modify: `catalogo/views.py`, `catalogo/templates/catalogo/item_list.html`, `catalogo/templates/catalogo/item_detail.html`, `catalogo/tests.py`
- Create: `catalogo/templates/catalogo/_review.html`

- [ ] **Step 1: Escrever os testes que falham**

Acrescente ao final de `catalogo/tests.py`:

```python
class ReviewNoCatalogoTest(TestCase):
    def setUp(self):
        self.dono = cria_usuario('arthur')
        self.outro = cria_usuario('andre')
        self.item = Item.objects.create(
            titulo='Hollow Knight', tipo=Item.Tipo.JOGO, ano=2017, criado_por=self.dono
        )
        Review.objects.create(usuario=self.dono, item=self.item, nota=9, opiniao='Ótimo.')
        Review.objects.create(usuario=self.outro, item=self.item, nota=6)

    def test_card_mostra_a_contagem_de_reviews(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.get('/catalogo/')

        self.assertEqual(resposta.context['object_list'][0].num_reviews, 2)

    def test_detalhe_lista_as_reviews(self):
        self.client.login(username='arthur', password='senha-forte-123')

        resposta = self.client.get(f'/catalogo/{self.item.pk}/')

        self.assertEqual(len(resposta.context['reviews']), 2)
        self.assertContains(resposta, 'Ótimo.')

    def test_detalhe_identifica_a_review_do_usuario_logado(self):
        self.client.login(username='andre', password='senha-forte-123')

        resposta = self.client.get(f'/catalogo/{self.item.pk}/')

        self.assertEqual(resposta.context['minha_review'].usuario, self.outro)
```

- [ ] **Step 2: Rodar para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test catalogo.tests.ReviewNoCatalogoTest -v 2`
Expected: FAIL — `AttributeError: 'Item' object has no attribute 'num_reviews'` e `KeyError: 'reviews'`.

- [ ] **Step 3: Acrescentar o `annotate` e o contexto do detalhe**

Em `catalogo/views.py`, acrescente aos imports do topo:

```python
from django.db.models import Count
```

E substitua as classes `ItemListView` e `ItemDetailView` por:

```python
class ItemListView(LoginRequiredMixin, ListView):
    model = Item

    def get_queryset(self):
        return super().get_queryset().annotate(num_reviews=Count('reviews'))


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['reviews'] = self.object.reviews.select_related('usuario')
        contexto['minha_review'] = self.object.reviews.filter(usuario=self.request.user).first()
        return contexto
```

O `annotate` mantém a lista em 3 queries para qualquer número de itens. Um `item.reviews.count()` no template viraria 3 + N — um catálogo de 30 itens dispararia 33 queries.

O `select_related('usuario')` no detalhe existe pelo mesmo motivo: o `_review.html` mostra `{{ review.usuario }}` em cada review, e sem ele cada uma custaria uma query.

- [ ] **Step 4: Criar `catalogo/templates/catalogo/_review.html`**

```html
<article class="rounded-xl border border-areia bg-white p-4">
  <div class="flex items-start justify-between gap-3">
    <div>
      <p class="font-display font-semibold text-cacau">{{ review.usuario }}</p>
      <p class="mt-0.5 text-sm font-semibold text-ferrugem">
        {{ review.nota }}<span class="font-normal text-ferrugem/60">/10</span>
      </p>
    </div>

    {% if review.usuario == user or user.is_staff %}
      <div class="flex shrink-0 gap-3 text-xs">
        {% if review.usuario == user %}
          <a href="{% url 'catalogo:review_editar' review.pk %}"
             class="font-medium text-ferrugem underline underline-offset-4">Editar</a>
        {% endif %}
        <a href="{% url 'catalogo:review_excluir' review.pk %}"
           class="font-medium text-red-700 underline underline-offset-4">Excluir</a>
      </div>
    {% endif %}
  </div>

  {% if review.opiniao %}
    <p class="mt-3 leading-relaxed text-cacau/90">{{ review.opiniao }}</p>
  {% endif %}
</article>
```

O layout é o pedido: **nome do usuário primeiro, nota embaixo, opinião embaixo se existir.**

Repare que os dois `{% if %}` são diferentes de propósito: **"Editar" só para o dono, "Excluir" para o dono ou o admin.** É a mesma assimetria dos mixins. Eles escondem, não protegem — a proteção é a view.

- [ ] **Step 5: Mostrar a contagem no card**

Em `catalogo/templates/catalogo/item_list.html`, substitua a linha `<p class="mt-0.5 text-sm text-ferrugem/80">{{ item.ano }}</p>` por:

```html
              <p class="mt-0.5 text-sm text-ferrugem/80">
                {{ item.ano }} ·
                {{ item.num_reviews }} {% if item.num_reviews == 1 %}avaliação{% else %}avaliações{% endif %}
              </p>
```

- [ ] **Step 6: Listar as reviews no detalhe**

Em `catalogo/templates/catalogo/item_detail.html`, logo antes do `</article>` de fechamento, **depois** do bloco `{% if object.criado_por == user or user.is_staff %}`, acrescente:

```html
      <section class="mt-8 border-t border-areia pt-6">
        <div class="mb-4 flex items-center justify-between gap-4">
          <h2 class="font-display text-xl font-semibold text-cacau">
            Avaliações <span class="text-ferrugem/60">({{ reviews|length }})</span>
          </h2>
          {% if minha_review %}
            <a href="{% url 'catalogo:review_editar' minha_review.pk %}"
               class="shrink-0 rounded-lg border border-cacau px-4 py-2 text-sm font-semibold text-cacau transition-colors hover:bg-areia/40">
              Editar minha avaliação
            </a>
          {% else %}
            <a href="{% url 'catalogo:avaliar' object.pk %}"
               class="shrink-0 rounded-lg bg-cacau px-4 py-2 text-sm font-semibold text-areia transition-colors hover:bg-ferrugem">
              Avaliar
            </a>
          {% endif %}
        </div>

        {% if reviews %}
          <div class="space-y-3">
            {% for review in reviews %}{% include 'catalogo/_review.html' %}{% endfor %}
          </div>
        {% else %}
          <p class="text-sm text-ferrugem">Ninguém avaliou este item ainda.</p>
        {% endif %}
      </section>
```

O `{% if minha_review %}` faz o botão dizer "Editar minha avaliação" em vez de "Avaliar" — o usuário nunca é levado ao redirect do `dispatch` pela navegação normal. O redirect continua existindo para quem digitar a URL na mão.

- [ ] **Step 7: Rodar a suíte inteira**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 58 tests` / `OK` (55 + 3 novos)

---

## Task 6: Exclusão de conta

**Files:**
- Modify: `usuarios/views.py`, `usuarios/urls.py`, `usuarios/tests.py`, `templates/base.html`
- Create: `usuarios/templates/usuarios/conta_confirm_delete.html`

- [ ] **Step 1: Escrever os testes que falham**

No topo de `usuarios/tests.py`, acrescente aos imports existentes:

```python
from catalogo.models import Item, Review
```

E acrescente ao final do arquivo:

```python
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
```

O `test_exclusao_leva_itens_e_reviews_de_terceiros_em_cascata` é o mais importante da task: ele **torna visível o risco do CASCADE** que estava aceito no papel. O André não apagou nada e perdeu a review dele; a conta dele sobrevive, o trabalho não.

- [ ] **Step 2: Rodar para confirmar que falham**

Run: `.\venv\Scripts\python.exe manage.py test usuarios.tests.ContaDeleteViewTest -v 2`
Expected: FAIL — 404, porque a rota não existe.

- [ ] **Step 3: Escrever a view**

Substitua todo o conteúdo de `usuarios/views.py` por:

```python
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView

from catalogo.models import Review

from .forms import UsuarioCreationForm


class CadastroView(CreateView):
    form_class = UsuarioCreationForm
    template_name = 'usuarios/cadastro.html'
    success_url = reverse_lazy('login')


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

**O `get_object()` devolve `request.user` e a URL não tem `pk`.** Isso torna impossível apagar a conta de outra pessoa por essa rota — é mais forte que qualquer checagem de permissão, porque não há o que checar.

O `logout()` vem **antes** do `delete()` para encerrar a sessão de forma limpa, enquanto o usuário ainda existe.

**Acoplamento novo, deliberado:** `usuarios` passa a importar `catalogo.models.Review`. Não há ciclo em Python — o `catalogo` referencia o usuário por string via `AUTH_USER_MODEL` —, mas os dois apps passam a se conhecer. Está registrado no spec.

- [ ] **Step 4: Registrar a rota**

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
    path('conta/excluir/', views.ContaDeleteView.as_view(), name='conta_excluir'),
]
```

- [ ] **Step 5: Criar `usuarios/templates/usuarios/conta_confirm_delete.html`**

```html
{% extends 'base.html' %}

{% block titulo %}Excluir conta — Gostoteca{% endblock %}

{% block conteudo %}
<main class="mx-auto max-w-lg p-6">
  <div class="rounded-xl border border-red-200 bg-white p-6 shadow-sm">
    <h1 class="font-display text-2xl font-semibold text-cacau">Excluir minha conta</h1>

    <p class="mt-3 text-cacau/90">
      Você está prestes a apagar a conta <strong class="font-semibold">{{ user.username }}</strong>.
      Esta ação não pode ser desfeita.
    </p>

    <div class="mt-5 rounded-lg bg-red-50 p-4 text-sm text-red-800">
      <p class="font-semibold">Isto vai apagar junto:</p>
      <ul class="mt-2 list-disc space-y-1 pl-5">
        <li>
          {{ meus_itens }} {% if meus_itens == 1 %}item que você cadastrou{% else %}itens que você cadastrou{% endif %}
          no catálogo
        </li>
        <li>
          Todas as suas avaliações
        </li>
        <li>
          <strong class="font-semibold">
            {{ reviews_de_terceiros }}
            {% if reviews_de_terceiros == 1 %}avaliação de outra pessoa{% else %}avaliações de outras pessoas{% endif %}
          </strong>
          nos seus itens
        </li>
      </ul>
    </div>

    <form method="post" class="mt-6 flex gap-3 border-t border-areia pt-5">
      {% csrf_token %}
      <button type="submit"
              class="rounded-lg bg-red-700 px-4 py-2 font-semibold text-white transition-colors hover:bg-red-800">
        Excluir minha conta
      </button>
      <a href="{% url 'catalogo:lista' %}"
         class="rounded-lg px-4 py-2 font-medium text-ferrugem transition-colors hover:bg-areia/40">Cancelar</a>
    </form>
  </div>
</main>
{% endblock %}
```

O terceiro item da lista é o que importa: **avaliações de outras pessoas morrem junto**. É a consequência do CASCADE, dita na cara do usuário antes de ele confirmar.

- [ ] **Step 6: Adicionar o link na navbar**

Em `templates/base.html`, dentro do `<header>`, entre o `<span>` do username e o `<form>` do logout, acrescente:

```html
        <a href="{% url 'conta_excluir' %}"
           class="text-sm font-medium text-areia/70 underline decoration-ambar/60 underline-offset-4 hover:text-areia">
          Excluir conta
        </a>
```

- [ ] **Step 7: Rodar a suíte inteira**

Run: `.\venv\Scripts\python.exe manage.py test -v 2`
Expected: `Ran 62 tests` / `OK` (58 + 4 novos)

- [ ] **Step 8: Rodar os comandos do CI**

Run: `.\venv\Scripts\python.exe manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `.\venv\Scripts\python.exe manage.py test`
Expected: `OK`

- [ ] **Step 9: Confirmar que nada foi commitado**

Run: `git status --short`
Expected: **vários arquivos modificados e não rastreados.** É o resultado correto. Se a saída estiver vazia, alguém commitou — reporte.

---

## Verificação manual (ao final)

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

1. Entre e abra um item. Deve aparecer a seção "Avaliações (0)" com o botão "Avaliar".
2. Avalie com nota 9 e uma opinião. Volta ao item, a review aparece com **seu nome, a nota, e a opinião embaixo**.
3. O botão agora deve dizer "Editar minha avaliação". Clique — deve abrir a review preenchida, não um form vazio.
4. Volte ao catálogo: o card do item deve dizer "1 avaliação" (singular).
5. Tente `/catalogo/<pk>/avaliar/` na mão para o mesmo item: deve redirecionar para a edição, **não** dar erro 500.
6. Avalie sem opinião, só a nota. Deve funcionar.
7. Tente salvar sem nota: deve dar erro de campo.
8. Com outro usuário, abra a review do primeiro: **não deve ter "Editar" nem "Excluir"**. Acessar `/catalogo/review/<pk>/editar/` na mão deve dar **403**.
9. Com um usuário `is_staff`, abra a mesma review: deve ter **"Excluir" mas não "Editar"**. `/editar/` na mão deve dar **403**; `/excluir/` deve funcionar.
10. `/conta/excluir/` deve mostrar os números certos de itens e de avaliações de terceiros.

As telas só aparecem estilizadas **com internet** (Play CDN e Google Fonts).

## Contagem de testes

O spec previa ~22 novos. Este plano entrega **29** (62 no total, dos 33 atuais). Os extras apareceram ao decompor: notas das bordas (0 e 10), `usuario`/`item` forjados no POST, opinião vazia via HTTP, anônimo em cada rota, e a identificação da `minha_review` no detalhe. Nenhum teste do spec ficou de fora.
