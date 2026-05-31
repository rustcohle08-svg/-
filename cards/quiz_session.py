"""
Состояние теста по карточкам в request.session.
"""

import random

SESSION_TOPIC = 'current_topic_id'
SESSION_QUEUE = 'queue'
SESSION_MISTAKES = 'mistakes'
SESSION_STATS = 'stats'
SESSION_PHASE = 'quiz_phase'
SESSION_FINISHED = 'quiz_finished'

PHASE_QUESTION = 'question'
PHASE_ANSWER = 'answer'
PHASE_RATED = 'rated'


def _empty_stats():
    return {'correct': 0, 'incorrect': 0}


def clear_quiz_session(request):
    """Сброс всех данных теста."""
    for key in (
        SESSION_TOPIC,
        SESSION_QUEUE,
        SESSION_MISTAKES,
        SESSION_STATS,
        SESSION_PHASE,
        SESSION_FINISHED,
    ):
        request.session.pop(key, None)
    request.session.modified = True


def quiz_is_active(request):
    return SESSION_TOPIC in request.session and not request.session.get(
        SESSION_FINISHED, False
    )


def quiz_is_finished(request):
    return request.session.get(SESSION_FINISHED, False)


def get_current_card_id(request):
    queue = request.session.get(SESSION_QUEUE, [])
    if not queue:
        return None
    return queue[0]


def start_quiz_session(request, topic_id, card_ids):
    """Новая сессия: перемешанная очередь без повторов."""
    shuffled = list(card_ids)
    random.shuffle(shuffled)
    request.session[SESSION_TOPIC] = topic_id
    request.session[SESSION_QUEUE] = shuffled
    request.session[SESSION_MISTAKES] = []
    request.session[SESSION_STATS] = _empty_stats()
    request.session[SESSION_PHASE] = PHASE_QUESTION
    request.session[SESSION_FINISHED] = False
    request.session.modified = True


def start_mistakes_round(request):
    """Повторный раунд только по ошибочным карточкам."""
    mistake_ids = list(request.session.get(SESSION_MISTAKES, []))
    if not mistake_ids:
        return False
    random.shuffle(mistake_ids)
    request.session[SESSION_QUEUE] = mistake_ids
    request.session[SESSION_MISTAKES] = []
    request.session[SESSION_STATS] = _empty_stats()
    request.session[SESSION_PHASE] = PHASE_QUESTION
    request.session[SESSION_FINISHED] = False
    request.session.modified = True
    return True


def set_phase(request, phase):
    request.session[SESSION_PHASE] = phase
    request.session.modified = True


def get_phase(request):
    return request.session.get(SESSION_PHASE, PHASE_QUESTION)


def record_rating(request, card_id, *, correct):
    """Фиксируем ответ пользователя (до перехода «Далее»)."""
    stats = request.session.get(SESSION_STATS, _empty_stats())
    mistakes = request.session.get(SESSION_MISTAKES, [])
    if correct:
        stats['correct'] = stats.get('correct', 0) + 1
    else:
        stats['incorrect'] = stats.get('incorrect', 0) + 1
        if card_id not in mistakes:
            mistakes.append(card_id)
    request.session[SESSION_STATS] = stats
    request.session[SESSION_MISTAKES] = mistakes
    request.session[SESSION_PHASE] = PHASE_RATED
    request.session.modified = True


def advance_to_next_card(request):
    """Убираем текущую карточку из очереди; при пустой очереди — финал."""
    queue = request.session.get(SESSION_QUEUE, [])
    if queue:
        queue.pop(0)
    request.session[SESSION_QUEUE] = queue
    if queue:
        request.session[SESSION_PHASE] = PHASE_QUESTION
        request.session[SESSION_FINISHED] = False
    else:
        request.session[SESSION_FINISHED] = True
    request.session.modified = True


def queue_progress(request):
    """Сколько карточек всего в раунде и сколько осталось (включая текущую)."""
    queue = request.session.get(SESSION_QUEUE, [])
    stats = request.session.get(SESSION_STATS, _empty_stats())
    done = stats.get('correct', 0) + stats.get('incorrect', 0)
    remaining = len(queue)
    total = done + remaining
    return total, remaining, done
