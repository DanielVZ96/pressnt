import bleach

from django_comments.models import Comment
from django_comments.forms import CommentForm, COMMENT_MAX_LENGTH
from mptt.models import MPTTModel, TreeForeignKey
from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from notifications.signals import notify

from press.utils import user_regex


class MPTTComment(MPTTModel, Comment):
    """ Threaded comments - Add support for the parent comment store and MPTT traversal"""

    # a link to comment that is being replied, if one exists
    parent = TreeForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )
    old = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if hasattr(self.content_object, "recount_comments"):
            self.content_object.recount_comments()
            self.notify_mentions()

    def _clean_fields(self, *args, **kwargs):
        super()._clean_fields(*args, **kwargs)
        for name, value in self.cleaned_data.items():
            self.cleaned_data[name] = bleach.clean(value)

    def get_mentions(self):
        usernames = [username for username in user_regex().findall(self.comment)]
        return User.objects.filter(username__in=usernames)

    def notify_mentions(self):
        for user in self.get_mentions():
            notify.send(
                self.user,
                recipient=user,
                verb="mentioned you in his comment",
                action_object=self,
            )

    def get_absolute_url(self, anchor_pattern="#c%(id)s"):
        content_url = self.content_object.get_absolute_url()
        return f"{content_url}{anchor_pattern % self.__dict__}"

    class MPTTMeta:
        # comments on one level will be ordered by date of creation
        order_insertion_by = ["-submit_date"]

    class Meta:
        ordering = ["submit_date", "lft"]


class MPTTCommentForm(CommentForm):
    parent = forms.ModelChoiceField(
        queryset=MPTTComment.objects.all(), required=False, widget=forms.HiddenInput
    )
    comment = forms.CharField(
        label=_("Comment"),
        widget=forms.Textarea(attrs={"placeholder": "Thoughts?"}),
        max_length=COMMENT_MAX_LENGTH,
    )

    def get_comment_model(self):
        # Use our custom comment model instead of the built-in one.
        return MPTTComment

    def get_comment_create_data(self, *args, **kwargs):
        # Use the data of the superclass, and add in the parent field field
        data = super(MPTTCommentForm, self).get_comment_create_data(*args, **kwargs)
        data["parent"] = self.cleaned_data["parent"]
        return data
