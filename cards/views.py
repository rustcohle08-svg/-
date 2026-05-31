"""
Простые функции-представления .
"""

from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import HistoryCardForm, TopicForm
from .models import HistoryCard, Topic
from . import quiz_session as qs


def index_page(request):
    """Главная страница с описанием сервиса."""
    topics_count = Topic.objects.count()
    cards_count = HistoryCard.objects.count()
    return render(
        request,
        'cards/index.html',
        {
            'topics_count': topics_count,
            'cards_count': cards_count,
        },
    )


def topics_list_page(request):
    """Список всех тем (страница вывода информации)."""
    all_topics = Topic.objects.annotate(num_cards=Count('cards')).order_by('name')
    return render(
        request,
        'cards/topics_list.html',
        {'topics': all_topics},
    )


def topic_detail_page(request, topic_id):
    """
    Одна тема: таблица карточек.
    Это тоже страница вывода информации.
    """
    topic = get_object_or_404(Topic, pk=topic_id)
    cards_in_topic = HistoryCard.objects.filter(topic=topic).order_by('id')
    return render(
        request,
        'cards/topic_detail.html',
        {
            'topic': topic,
            'cards': cards_in_topic,
        },
    )


def card_detail_page(request, card_id):
    """Детальная страница одной карточки."""
    card = get_object_or_404(HistoryCard, pk=card_id)
    return render(request, 'cards/card_detail.html', {'card': card})


def topic_add_page(request):
    """Форма добавления темы."""
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('topics_list')
    else:
        form = TopicForm()
    return render(request, 'cards/topic_form.html', {'form': form})


def card_add_page(request):
    """Форма добавления карточки."""
    if request.method == 'POST':
        form = HistoryCardForm(request.POST)
        if form.is_valid():
            form.save()
            topic = form.cleaned_data['topic']
            return redirect('topic_detail', topic_id=topic.id)
    else:
        form = HistoryCardForm()
    return render(request, 'cards/card_form.html', {'form': form, 'title': 'Новая карточка'})


def card_edit_page(request, card_id):
    """Форма редактирования карточки."""
    card = get_object_or_404(HistoryCard, pk=card_id)
    if request.method == 'POST':
        form = HistoryCardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            return redirect('card_detail', card_id=card.id)
    else:
        form = HistoryCardForm(instance=card)
    return render(
        request,
        'cards/card_form.html',
        {'form': form, 'title': 'Редактирование карточки', 'card': card},
    )


def _quiz_context(request, topics_with_cards, error_message=None):
    """Общий контекст для шаблона quiz.html."""
    selected_topic = None
    quiz_card = None
    phase = qs.PHASE_QUESTION
    total_cards = 0
    cards_left = 0
    cards_done = 0
    stats = {'correct': 0, 'incorrect': 0}
    mistakes = []
    show_results = False
    all_correct = False

    if qs.quiz_is_finished(request):
        show_results = True
        topic_id = request.session.get(qs.SESSION_TOPIC)
        if topic_id:
            selected_topic = Topic.objects.filter(pk=topic_id).first()
        stats = request.session.get(qs.SESSION_STATS, {'correct': 0, 'incorrect': 0})
        mistakes = request.session.get(qs.SESSION_MISTAKES, [])
        incorrect = stats.get('incorrect', 0)
        all_correct = incorrect == 0 and stats.get('correct', 0) > 0
    elif qs.quiz_is_active(request):
        topic_id = request.session.get(qs.SESSION_TOPIC)
        selected_topic = get_object_or_404(Topic, pk=topic_id)
        phase = qs.get_phase(request)
        total_cards, cards_left, cards_done = qs.queue_progress(request)
        card_id = qs.get_current_card_id(request)
        if card_id:
            quiz_card = get_object_or_404(
                HistoryCard,
                pk=card_id,
                topic=selected_topic,
            )

    return {
        'topics': topics_with_cards,
        'selected_topic': selected_topic,
        'card': quiz_card,
        'phase': phase,
        'quiz_active': qs.quiz_is_active(request),
        'show_results': show_results,
        'all_correct': all_correct,
        'stats': stats,
        'mistakes': mistakes,
        'has_mistakes': len(mistakes) > 0,
        'total_cards': total_cards,
        'cards_left': cards_left,
        'cards_done': cards_done,
        'error_message': error_message,
    }


@require_http_methods(['GET', 'POST'])
def quiz_page(request):
    """
    Тест по одной теме: очередь без повторов, оценка ответа, итоги сессии.
    """
    topics_with_cards = Topic.objects.annotate(n=Count('cards')).filter(n__gt=0)
    error_message = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'start':
            qs.clear_quiz_session(request)
            try:
                topic_id = int(request.POST.get('topic_id', ''))
            except (TypeError, ValueError):
                error_message = 'Выберите тему для теста.'
            else:
                topic = get_object_or_404(Topic, pk=topic_id)
                card_ids = list(
                    HistoryCard.objects.filter(topic=topic).values_list('id', flat=True)
                )
                if not card_ids:
                    error_message = 'В этой теме пока нет карточек.'
                else:
                    qs.start_quiz_session(request, topic.id, card_ids)
                    return redirect('quiz')

        elif action == 'exit':
            qs.clear_quiz_session(request)
            return redirect('quiz')

        elif action == 'finish':
            qs.clear_quiz_session(request)
            return redirect('topics_list')

        elif action == 'retry_mistakes':
            if qs.start_mistakes_round(request):
                return redirect('quiz')
            return redirect('quiz')

        elif action == 'show_answer':
            if qs.quiz_is_active(request) and qs.get_phase(request) == qs.PHASE_QUESTION:
                qs.set_phase(request, qs.PHASE_ANSWER)
            return redirect('quiz')

        elif action == 'rate':
            if qs.quiz_is_active(request):
                rating = request.POST.get('rating')
                try:
                    card_id = int(request.POST.get('card_id', ''))
                except (TypeError, ValueError):
                    card_id = None
                current_id = qs.get_current_card_id(request)
                topic_id = request.session.get(qs.SESSION_TOPIC)
                if (
                    card_id
                    and card_id == current_id
                    and qs.get_phase(request) == qs.PHASE_ANSWER
                ):
                    get_object_or_404(HistoryCard, pk=card_id, topic_id=topic_id)
                    if rating == 'correct':
                        qs.record_rating(request, card_id, correct=True)
                    elif rating == 'incorrect':
                        qs.record_rating(request, card_id, correct=False)
            return redirect('quiz')

        elif action == 'next':
            if qs.quiz_is_active(request) and qs.get_phase(request) == qs.PHASE_RATED:
                qs.advance_to_next_card(request)
            return redirect('quiz')

    return render(
        request,
        'cards/quiz.html',
        _quiz_context(request, topics_with_cards, error_message),
    )
