from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.signals import notify

from press.models import PostLike, Follow


@receiver(post_save, sender=PostLike)
def like_notification(sender, instance: PostLike, *args, **kwargs):
    if instance.active:
        notify.send(
            instance.user,
            recipient=instance.post.user,
            verb="liked your post",
            action_object=instance.post,
        )


@receiver(post_save, sender=Follow)
def follow_notification(sender, instance: Follow, *args, **kwargs):
    if instance.active:
        notify.send(
            instance.user,
            recipient=instance.post.user,
            verb="followed your post",
            action_object=instance.post,
        )
