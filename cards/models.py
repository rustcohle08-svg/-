"""
Модели для исторических карточек.
"""

from django.db import models


class Topic(models.Model):
    name = models.CharField('название темы', max_length=150)

    def __str__(self):
        return self.name


class HistoryCard(models.Model):
    """
    Карточка: термин.
    """

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='cards',
        verbose_name='тема',
    )
    term = models.CharField('термин (лицевая сторона)', max_length=250)
    translation = models.TextField('пояснение')


    class Meta:
        verbose_name = 'историческая карточка'
        verbose_name_plural = 'исторические карточки'
        ordering = ['id']

    def __str__(self):
        short = self.term[:40]
        if len(self.term) > 40:
            short = short + '...'
        return short
