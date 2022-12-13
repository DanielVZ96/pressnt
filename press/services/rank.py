from django.db.models import F, DateTimeField, ExpressionWrapper, FloatField
from django.db.models.functions import Cast
from django.utils import timezone

from press.models import Post

G = 1.8


def get_trending_posts_queryset():
    """
    Rank = (L-1) / (T+2)^G
    L = likes
    T = time since last update
    G = Gravity. Currently 1.8 but may change
    """
    now = timezone.now()
    return (
        Post.objects.annotate(
            duration=ExpressionWrapper(
                Cast(now, DateTimeField()) - F("created_at"), output_field=FloatField()
            )
        )
        .annotate(score=(F("like_count") - 1) / (F("duration") + 1) ** G)
        .order_by("score")
    )


def get_followed_posts_queryset(user):
    return Post.objects.filter(follows__user=user)
