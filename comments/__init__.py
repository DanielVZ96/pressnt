def get_model():
    from comments.models import MPTTComment

    return MPTTComment


def get_form():
    from comments.models import MPTTCommentForm

    return MPTTCommentForm
