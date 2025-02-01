# myapp/context_processors.py
from .models import Question
from django.db.models import Count


def sidebar_data(request):
    # Fetch the latest 5 questions for "New Discussions"
    new_discussions = Question.objects.order_by('-created_at')[:3]

    # Fetch the top 5 questions with the highest view_count for "Popular Posts"
    popular_posts = Question.objects.order_by('-view_count')[:3]

    return {
        'new_discussions': new_discussions,
        'popular_posts': popular_posts,
    }

