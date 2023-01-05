from django import template
from django.contrib.auth.models import User
from django.utils.html import format_html

from press.utils import user_regex

register = template.Library()


def replace_user_with_anchor(user_matchobj):
    username = user_matchobj.group(1)
    user = User.objects.filter(username=username).first()
    if user is None:
        return "@" + username
    else:
        link = user.profile.get_absolute_url()
        return format_html("<a class='mention bold' href='{}'>@{}</a>", link, username)


@register.filter(is_safe=True)
def mentionify(content):
    return user_regex().sub(replace_user_with_anchor, content)
