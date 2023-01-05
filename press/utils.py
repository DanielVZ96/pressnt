import re
from functools import lru_cache

MENTION_REGEX = r"@([\w\-\+\_\.\@]+)"


@lru_cache(maxsize=1)
def user_regex():
    return re.compile(MENTION_REGEX)
