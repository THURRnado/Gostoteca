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
