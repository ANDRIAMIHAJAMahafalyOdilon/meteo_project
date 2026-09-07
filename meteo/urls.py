from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('historique/', views.historique, name='historique'),
]