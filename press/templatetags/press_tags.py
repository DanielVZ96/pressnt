import re
from django import template
from django.contrib.auth.models import User
from django.utils.html import format_html
from functools import lru_cache

register = template.Library()

MENTION_REGEX = r"@([\w\-\+\_\.\@]+)"


@lru_cache(maxsize=1)
def user_regex():
    return re.compile(MENTION_REGEX)


def replace_user_with_anchor(user_matchobj):
    username = user_matchobj.group(1)
    user = User.objects.filter(username=username).first()
    if user is None:
        return "@" + username
    else:
        link = user.profile.get_absolute_url()
        return format_html("<a href='{}'>@{}</a>", link, username)


@register.filter(is_safe=True)
def mentionify(content):
    return user_regex().sub(replace_user_with_anchor, content)
