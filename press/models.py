from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from django_resized import ResizedImageField
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify

from comments.models import MPTTComment


User._meta.get_field("email")._unique = True


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=255)
    pic = ResizedImageField(
        size=[300, 300], scale=True, default="default_pic.png", upload_to="profile_pic",
    )
    description = models.TextField()
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} (@{self.user.username})"

    def get_absolute_url(self):
        return reverse("profile-detail", kwargs={"pk": self.pk})

    @property
    def is_valid(self):
        return self.name != "" and self.description != 0


class Post(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="post")
    title = models.CharField(max_length=255)
    content = MarkdownxField(
        default="# Edit here to create your first and only post!\n[TOC]\n## Subtitle\n(you can edit it later if you want)"
    )
    created_at = models.DateField(auto_now_add=True, null=True)
    updated_at = models.DateField(auto_now=True, null=True)
    like_count = models.PositiveIntegerField(default=0)
    follow_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    def get_absolute_url(self):
        return reverse("post-detail", kwargs={"pk": self.pk})

    @property
    def markdown(self):
        return markdownify(self.content)

    def recount_likes(self):
        self.like_count = self.likes.filter(active=True).count()
        self.save()

    def recount_follows(self):
        self.follow_count = self.follows.filter(active=True).count()
        self.save()

    def recount_comments(self):
        self.comment_count = MPTTComment.objects.filter(
            content_type=ContentType.objects.get_for_model(self), object_pk=self.id,
        ).count()
        self.save()

    def save(self, *args, **kwargs):
        lines = self.content.strip().splitlines()
        if lines:
            self.title = lines[0]
        return super().save(*args, **kwargs)


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    active = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def save(self, *args, **kwargs):
        ret = super().save(*args, **kwargs)
        self.post.recount_likes()
        return ret


class Follow(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="follows")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follows")
    active = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def save(self, *args, **kwargs):
        ret = super().save(*args, **kwargs)
        self.post.recount_follows()
        return ret
