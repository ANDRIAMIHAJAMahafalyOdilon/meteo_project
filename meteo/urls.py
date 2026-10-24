from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('historique/', views.historique, name='historique'),
    path('historique/<int:recherche_id>/', views.detail_historique, name='detail_historique'),
    path('historique/<int:recherche_id>/supprimer/', views.supprimer_historique, name='supprimer_historique'),
]
