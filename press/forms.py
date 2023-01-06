from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.core.mail import send_mail

from press.models import Follow, PostLike, Profile


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


class PictureWidget(forms.widgets.FileInput):
    def render(self, *args, **kwargs):
        return format_html(
            """
            <img width="128px" height="128px" class="w-4/5 border-black border dark:bg-sky-100 rounded-lg aspect-1 apect object-cover" id="img_pic" src="/media/{}"/></td></tr>
            <tr><td class="flex justify-center w-full">
            <input  class="p-2 block w-full text-sm text-gray-900 border border-black  rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400" type="file" id="id_pic" name="pic" accept="image/*">
            </td>""",
            kwargs.get("value"),
        )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("pic", "name", "description")
        widgets = {
            "pic": PictureWidget(),
        }


class ContactForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email_address = forms.EmailField(max_length=150)
    message = forms.CharField(widget=forms.Textarea, max_length=2000)

    def send_email(self):
        message = "\n".join(
            [f"{k.replace('_', ' ')}: {v}" for k, v in self.cleaned_data.items()]
        )
        send_mail(
            "Pressn't Contact", message, "noreply@pressnt.net", ["dsvalenzuela@uc.cl"]
        )
