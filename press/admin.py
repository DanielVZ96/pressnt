from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin

from press.models import Follow, Post, PostLike


@admin.register(Post)
class PostAdmin(MarkdownxModelAdmin):
    pass


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    pass


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    pass
