from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('book/<int:pk>/', views.book, name='book'),
    path('search/', views.search, name='search'),
    path('about/', views.about, name='about')
]
