"""
Формы с валидацией и понятными сообщениями об ошибках.
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import HistoryCard, Topic


class TopicForm(forms.ModelForm):
    """Форма для добавления новой темы."""

    class Meta:
        model = Topic
        fields = ['name']
        labels = {'name': 'Название темы'}
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'inp', 'placeholder': 'Например: Древняя Русь'}
            ),
        }
        error_messages = {
            'name': {
                'required': 'Нужно ввести название темы',
            },
        }

    def __init__(self, *args, **kwargs):
        """Задаём ограничения длины для названия темы."""
        super().__init__(*args, **kwargs)
        field = self.fields['name']
        field.min_length = 3
        field.max_length = 150
        field.error_messages['min_length'] = (
            'Слишком короткое название, минимум %(limit_value)d символа'
        )
        field.error_messages['max_length'] = (
            'Слишком длинное название, максимум %(limit_value)d символов'
        )

    def clean_name(self):
        """Убираем пробелы, проверяем уникальность названия темы."""
        name = self.cleaned_data.get('name', '')
        name_stripped = name.strip()
        if len(name_stripped) == 0:
            raise ValidationError('Нельзя ввести одни только пробелы')
        qs = Topic.objects.filter(name__iexact=name_stripped)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Тема с таким названием уже есть')
        return name_stripped


class HistoryCardForm(forms.ModelForm):
    """Форма создания и редактирования карточки."""

    class Meta:
        model = HistoryCard
        fields = ['topic', 'term', 'translation']
        labels = {
            'topic': 'Тема',
            'term': 'Термин (слово на лицевой стороне)',
            'translation': 'Пояснение',
        }
        widgets = {
            'topic': forms.Select(attrs={'class': 'inp'}),
            'term': forms.TextInput(attrs={'class': 'inp'}),
            'translation': forms.Textarea(
                attrs={'class': 'inp', 'rows': 4, 'cols': 40}
            ),
        }
        error_messages = {
            'topic': {'required': 'Выберите тему из списка'},
            'term': {'required': 'Введите термин для карточки'},
            'translation': {'required': 'Напишите пояснение к термину'},
        }

    def clean_term(self):
        """Проверяем длину термина после обрезки пробелов."""
        term = self.cleaned_data.get('term', '')
        t = term.strip()
        if len(t) < 2:
            raise ValidationError('Термин должен быть хотя бы из 2 символов')
        if len(t) > 100:
            raise ValidationError('Термин слишком длинный')
        return t

    def clean_translation(self):
        """Проверяем длину пояснения."""
        text = self.cleaned_data.get('translation', '')
        text_stripped = text.strip()
        if len(text_stripped) < 5:
            raise ValidationError('Пояснение слишком короткое, напишите хотя бы 5 символов')
        if len(text_stripped) > 700:
            raise ValidationError('Пояснение слишком длинное, сократите до 700 символов')
        return text_stripped

    def clean(self):
        """Не допускаем двух карточек с одним термином в одной теме."""
        cleaned_data = super().clean()
        topic = cleaned_data.get('topic')
        term = cleaned_data.get('term')
        if topic is None or term is None:
            return cleaned_data
        duplicates = HistoryCard.objects.filter(
            topic=topic,
            term__iexact=term,
        )
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise ValidationError(
                'В выбранной теме уже есть карточка с таким термином. '
                'Укажите другой термин или выберите другую тему.'
            )
        return cleaned_data
