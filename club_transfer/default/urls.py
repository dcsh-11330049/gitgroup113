from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/clubs/', views.clubs_api, name='clubs_api'),
]