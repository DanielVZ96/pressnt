from django_comments.models import Comment
from django_comments.forms import CommentForm, COMMENT_MAX_LENGTH
from mptt.models import MPTTModel, TreeForeignKey
from django.db import models
from django import forms
from django.utils.translation import gettext_lazy as _


class MPTTComment(MPTTModel, Comment):
    """ Threaded comments - Add support for the parent comment store and MPTT traversal"""

    # a link to comment that is being replied, if one exists
    parent = TreeForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if hasattr(self.content_object, "recount_comments"):
            self.content_object.recount_comments()

    class MPTTMeta:
        # comments on one level will be ordered by date of creation
        order_insertion_by = ["submit_date"]

    class Meta:
        ordering = ["tree_id", "lft"]


class MPTTCommentForm(CommentForm):
    parent = forms.ModelChoiceField(
        queryset=MPTTComment.objects.all(), required=False, widget=forms.HiddenInput
    )
    comment = forms.CharField(
        label=_("Comment"),
        widget=forms.Textarea(attrs={"placeholder": "Thougths?"}),
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
