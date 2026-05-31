"""
Маршруты приложения карточек.
"""

from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_page, name='index'),
    path('topics/', views.topics_list_page, name='topics_list'),
    path('topics/add/', views.topic_add_page, name='topic_add'),
    path('topics/<int:topic_id>/', views.topic_detail_page, name='topic_detail'),
    path('cards/<int:card_id>/', views.card_detail_page, name='card_detail'),
    path('cards/add/', views.card_add_page, name='card_add'),
    path('cards/<int:card_id>/edit/', views.card_edit_page, name='card_edit'),
    path('quiz/', views.quiz_page, name='quiz'),
]
