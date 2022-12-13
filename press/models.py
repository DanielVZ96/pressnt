from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=255)
    pic = models.ImageField(default="default_pic.png", upload_to="profile_pic")
    description = models.TextField()
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} (@{self.user.username})"

    def get_absolute_url(self):
        return reverse("profile-detail", kwargs={"pk": self.pk})


class Post(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="post")
    title = models.CharField(max_length=255)
    content = MarkdownxField()
    created_at = models.DateField(auto_now_add=True, null=True)
    updated_at = models.DateField(auto_now=True, null=True)
    like_count = models.PositiveIntegerField(default=0)
    follow_count = models.PositiveIntegerField(default=0)

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
