from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('book/<int:pk>/', views.book, name='book'),
    path('nlpbook/<int:pk>/', views.nlpbook, name='nlpbook'),
    path('search/', views.search, name='search'),
    path('nlpsearch/', views.nlpsearch, name='nlpsearch'),
    path('about/', views.about, name='about')
]
