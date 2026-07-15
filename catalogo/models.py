from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models
from django.urls import reverse


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

    def get_absolute_url(self):
        return reverse('catalogo:detalhe', kwargs={'pk': self.pk})


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
