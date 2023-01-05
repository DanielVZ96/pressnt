from typing import Any, Dict
from django.urls import reverse_lazy, reverse
from django import views
from django.conf import settings
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView
from django.views.generic.edit import CreateView
from django.views.generic.detail import DetailView
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.http import HttpResponseRedirect
from press.forms import FollowForm, PostLikeform, ProfileForm, RegisterForm
from press.models import Follow, PostLike, Profile, Post
from press.services.rank import get_followed_posts_queryset, get_trending_posts_queryset
from press.verification import send_verification, verify_user_token

PAGING = 15


class EmailSentView(TemplateView):
    template_name = "press/email_sent.html"


class ProfileRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.profile.is_valid:
            return redirect("profile-update")
        if (
            request.user.is_authenticated
            and not Post.objects.filter(user=request.user).exists()
        ):
            return redirect("post-create")
        return super().dispatch(request, *args, **kwargs)


class RegisterView(FormView):
    template_name = "press/register.html"
    form_class = RegisterForm
    redirect_authenticated_user = True
    success_url = reverse_lazy("email-sent",)

    def form_invalid(self, form):
        email = form.data.get("email")
        user = User.objects.filter(email=email, is_active=False).first()
        if user is not None:
            send_verification(user)
            form.add_error("email", "We sent another confirmation email just in case!")
        return super().form_invalid(form)

    def form_valid(self, form):
        user = form.save()
        if user:
            Profile.objects.create(user=user)
            login(self.request, user)

        ret = super(RegisterView, self).form_valid(form)
        if not settings.DEBUG:
            user.is_active = False
            send_verification(user)
        return ret


class VerifyView(views.View):
    def get(self, request, *args, **kwargs):
        token = kwargs.get("token")
        success, user = verify_user_token(token)
        return render(
            request, settings.EMAIL_PAGE_TEMPLATE, {"user": user, "success": success}
        )


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    success_url = reverse_lazy("profile-update")
    form_class = ProfileForm

    def get_object(self):
        return Profile.objects.get(user=self.request.user)

    def post(self, *args, **kwargs):
        resp = super().post(*args, **kwargs)
        if not Post.objects.filter(user=self.request.user).exists():
            return redirect("post-create")
        return resp


class ProfileDetailView(ProfileRequiredMixin, DetailView):
    model = Profile
    fields = ["user", "name", "pic", "description"]

    def get_object(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        slug = self.kwargs.get(self.slug_url_kwarg)
        if pk is None and slug is None:
            return Profile.objects.get(user=self.request.user)
        else:
            return super().get_object()

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            follow, _ = Follow.objects.get_or_create(
                user=self.request.user,
                post=self.get_object().user.post,
                defaults={"active": False},
            )
            follow_form = FollowForm(
                initial={
                    "user": follow.user,
                    "post": follow.post,
                    "active": not follow.active,
                },
                instance=follow,
            )
        else:
            follow_form = FollowForm()
        context["follow_form"] = follow_form
        return context

    def post(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect("login")
        follow, _ = Follow.objects.get_or_create(
            user=self.request.user,
            post=self.get_object().user.post,
            defaults={"active": False},
        )
        form = FollowForm(
            data=request.POST,
            initial={
                "user": self.request.user,
                "post": self.get_object().user.post,
                "active": not follow.active,
            },
            instance=follow,
        )
        form.is_valid()
        form.save()
        return HttpResponseRedirect(self.get_object().get_absolute_url())


class PostCreate(LoginRequiredMixin, CreateView):
    model = Post
    fields = ["content"]

    def get(self, request, *args, **kwargs):
        if post := Post.objects.filter(user=self.request.user).first():
            return HttpResponseRedirect(post.get_absolute_url())

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())


class PostDetail(ProfileRequiredMixin, DetailView):
    model = Post
    fields = ["user", "title", "content"]

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Post.DoesNotExist:
            return redirect("post-create")

    def get_object(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        slug = self.kwargs.get(self.slug_url_kwarg)
        if pk is None and slug is None:
            return Post.objects.get(user=self.request.user)
        else:
            return super().get_object()

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["markdown"] = self.object.markdown
        if self.request.user.is_authenticated:
            try:
                like, _ = PostLike.objects.get_or_create(
                    post=self.object, user=self.request.user, defaults={"active": False}
                )
            except PostLike.MultipleObjectsReturned:
                like = PostLike.objects.filter(
                    post=self.object, user=self.request.user
                ).first()
                PostLike.objects.filter(user=like.user, post=like.post).exclude(
                    pk=like.id
                ).delete()
            try:
                follow, _ = Follow.objects.get_or_create(
                    user=like.user, post=like.post, defaults={"active": False},
                )
            except Follow.MultipleObjectsReturned:
                follow = Follow.objects.filter(user=like.user, post=like.post).first()
                Follow.objects.filter(user=like.user, post=like.post).exclude(
                    pk=follow.id
                ).delete()
            like_form = PostLikeform(
                initial={
                    "user": like.user,
                    "post": like.post,
                    "active": not like.active,
                },
                instance=like,
            )
            follow_form = FollowForm(
                initial={
                    "user": like.user,
                    "post": like.post,
                    "active": not follow.active,
                },
                instance=follow,
            )
        else:
            like_form = PostLikeform()
            follow_form = FollowForm()

        context["like_form"] = like_form
        context["follow_form"] = follow_form
        return context

    def post(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect("login")
        if "like" in request.POST:
            try:
                like, _ = PostLike.objects.get_or_create(
                    post=self.get_object(),
                    user=self.request.user,
                    defaults={"active": False},
                )
            except PostLike.MultipleObjectsReturned:
                like = PostLike.objects.filter(
                    post=self.object, user=self.request.user
                ).first()
                PostLike.objects.filter(user=like.user, post=like.post).exclude(
                    pk=like.id
                ).delete()
            form = PostLikeform(
                data=request.POST,
                initial={
                    "post": like.post,
                    "user": like.user,
                    "active": not like.active,
                },
                instance=like,
            )
            form.is_valid()
            form.save()
            return HttpResponseRedirect(like.post.get_absolute_url())
        elif "follow" in request.POST:
            try:
                follow, _ = Follow.objects.get_or_create(
                    user=self.request.user,
                    post=self.get_object(),
                    defaults={"active": False},
                )
            except Follow.MultipleObjectsReturned:
                follow = Follow.objects.filter(
                    user=self.request.user, post=self.get_object()
                ).first()
                Follow.objects.filter(user=follow.user, post=follow.post).exclude(
                    pk=follow.id
                ).delete()
            form = FollowForm(
                data=request.POST,
                initial={
                    "user": self.request.user,
                    "post": self.get_object(),
                    "active": not follow.active,
                },
                instance=follow,
            )
            form.is_valid()
            form.save()
            return HttpResponseRedirect(self.get_object().get_absolute_url())


class UserPostDetail(LoginRequiredMixin, PostDetail):
    pass


class PostUpdate(ProfileRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Post
    fields = ["content"]
    success_url = reverse_lazy("user-post-detail")

    def get(self, request, *args, **kwargs):
        if not Post.objects.filter(user=self.request.user).exists():
            return HttpResponseRedirect(reverse("post-create"))

        return super().get(request, *args, **kwargs)

    def get_object(self):
        return Post.objects.get(user=self.request.user)

    def post(self, *args, **kwargs):
        response = super().post(*args, **kwargs)
        self.get_object().notify_mentions()
        self.get_object().make_comments_old()
        return response


class Home(ProfileRequiredMixin, views.View):
    def get(self, request, *args, **kwargs):
        trending = get_trending_posts_queryset()
        trending_paginator = Paginator(trending, PAGING)
        trend_page_number = request.GET.get("trend_page")
        trend_page = trending_paginator.get_page(trend_page_number)

        if not request.user.is_authenticated:
            follow = Follow.objects.none()
        else:
            follow = get_followed_posts_queryset(self.request.user)
        follow_paginator = Paginator(follow, PAGING)
        follow_page_number = request.GET.get("follow_page")
        follow_page = follow_paginator.get_page(follow_page_number)

        return render(
            request,
            "press/home.html",
            {
                "trend_page_obj": trend_page,
                "follow_page_obj": follow_page,
                "has_follows": follow.exists(),
            },
        )


class News(ProfileRequiredMixin, LoginRequiredMixin, views.View):
    def get(self, request, *args, **kwargs):
        notifications = request.user.notifications.all()
        pages = Paginator(notifications, PAGING)
        page = request.GET.get("page")
        notifications_page = pages.get_page(page)
        response = render(
            request, "press/news.html", {"notifications_page": notifications_page},
        )
        notifications.mark_all_as_read()
        return response
