"""
URL configuration for histsite project.
"""

from django.urls import include, path

urlpatterns = [
    path('', include('cards.urls')),
]
