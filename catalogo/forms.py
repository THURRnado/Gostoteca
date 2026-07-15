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
