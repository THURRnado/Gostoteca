from django import forms

from usuarios.forms import FormEstilizado

from .models import Item


class ItemForm(FormEstilizado, forms.ModelForm):
    class Meta:
        model = Item
        fields = ('titulo', 'tipo', 'ano', 'criador', 'descricao', 'capa')
