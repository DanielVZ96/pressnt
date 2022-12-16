from django.db.models import (
    F,
    DateTimeField,
    ExpressionWrapper,
    FloatField,
    IntegerField,
    expressions,
)
from django.db.models.functions import Cast
from django.utils import timezone
from django.conf import settings

from press.models import Post, User

G = 1.8


class Epoch(expressions.Func):
    template = "EXTRACT(epoch FROM %(expressions)s)::INTEGER"
    output_field = IntegerField()


def get_trending_posts_queryset():
    """
    Rank = (L-1) / (T+2)^G
    L = likes
    T = time since last update
    G = Gravity. Currently 1.8 but may change
    """
    now = timezone.now()
    if settings.DEBUG:
        return (
            Post.objects.annotate(
                duration=ExpressionWrapper(
                    Cast(now, DateTimeField()) - F("updated_at"),
                    output_field=FloatField(),
                )
            )
            .annotate(score=(F("like_count") - 1.0) / (F("duration") + 1.0) ** G)
            .order_by("-score")
        )
    else:
        return (
            Post.objects.annotate(
                duration=ExpressionWrapper(
                    Cast(
                        Epoch(Cast(now, DateTimeField()) - F("updated_at")),
                        FloatField(),
                    ),
                    output_field=FloatField(),
                )
            )
            .annotate(score=(F("like_count") - 1.0) / (F("duration") + 1.0) ** G)
            .order_by("-score")
        )


def get_followed_posts_queryset(user: User):
    return user.follows.filter(active=True)
