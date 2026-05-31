# Конфигурация приложения с карточками.

from django.apps import AppConfig


class CardsConfig(AppConfig):
    """Настройки приложения cards."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cards'
