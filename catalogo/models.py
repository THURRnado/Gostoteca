from django.conf import settings
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
