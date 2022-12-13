from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from press.models import Follow, PostLike


class RegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=254)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )


class PostLikeform(forms.ModelForm):
    class Meta:
        model = PostLike
        fields = ("post", "user", "active")
        widgets = {
            "post": forms.HiddenInput(),
            "user": forms.HiddenInput(),
            "active": forms.HiddenInput(),
        }


class FollowForm(forms.ModelForm):
    class Meta:
        model = Follow
        fields = ("follower", "target", "active")
        fields = ("post", "user", "active")
        widgets = {
            "post": forms.HiddenInput(),
            "user": forms.HiddenInput(),
            "active": forms.HiddenInput(),
        }
