from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.ItemListView.as_view(), name='lista'),
    path('novo/', views.ItemCreateView.as_view(), name='novo'),
    path('<int:pk>/', views.ItemDetailView.as_view(), name='detalhe'),
    path('<int:pk>/editar/', views.ItemUpdateView.as_view(), name='editar'),
    path('<int:pk>/excluir/', views.ItemDeleteView.as_view(), name='excluir'),
]
