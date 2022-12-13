from typing import Any, Dict
from django.urls import reverse_lazy, reverse
from django import views
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView
from django.views.generic.edit import CreateView
from django.views.generic.detail import DetailView
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from press.forms import FollowForm, PostLikeform, RegisterForm
from press.models import Follow, PostLike, Profile, Post
from press.services.rank import get_followed_posts_queryset, get_trending_posts_queryset


class RegisterView(FormView):
    template_name = "press/register.html"
    form_class = RegisterForm
    redirect_authenticated_user = True
    success_url = reverse_lazy("profile-update",)

    def form_valid(self, form):
        user = form.save()
        if user:
            Profile.objects.create(user=user)
            login(self.request, user)

        return super(RegisterView, self).form_valid(form)


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ["name", "pic", "description"]
    success_url = reverse_lazy("profile-update")

    def get_object(self):
        return Profile.objects.get(user=self.request.user)


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    fields = ["user", "name", "pic", "description"]

    def get_object(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        slug = self.kwargs.get(self.slug_url_kwarg)
        if pk is None and slug is None:
            return Profile.objects.get(user=self.request.user)
        else:
            return super().get_object()


class PostCreate(LoginRequiredMixin, CreateView):
    model = Post
    fields = ["title", "content"]

    def get(self, request, *args, **kwargs):
        if post := Post.objects.filter(user=self.request.user).first():
            return HttpResponseRedirect(post.get_absolute_url())

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())


class PostDetail(LoginRequiredMixin, DetailView):
    model = Post
    fields = ["user", "content"]

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
        like, _ = PostLike.objects.get_or_create(
            post=self.object, user=self.request.user, defaults={"active": False}
        )
        follow, _ = Follow.objects.get_or_create(
            user=like.user, post=like.post, defaults={"active": False},
        )
        like_form = PostLikeform(
            initial={"user": like.user, "post": like.post, "active": not like.active},
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

        context["like_form"] = like_form
        context["follow_form"] = follow_form
        return context

    def post(self, request, *args, **kwargs):
        if "like" in request.POST:
            like, _ = PostLike.objects.get_or_create(
                post=self.get_object(),
                user=self.request.user,
                defaults={"active": False},
            )
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
            follow, _ = Follow.objects.get_or_create(
                user=self.request.user,
                post=self.get_object(),
                defaults={"active": False},
            )
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


class PostUpdate(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ["content"]
    success_url = reverse_lazy("user-post-detail")

    def get(self, request, *args, **kwargs):
        if not Post.objects.filter(user=self.request.user).exists():
            return HttpResponseRedirect(reverse("post-create"))

        return super().get(request, *args, **kwargs)

    def get_object(self):
        return Post.objects.get(user=self.request.user)


class Home(views.View):
    def get(self, request, *args, **kwargs):
        trending = get_trending_posts_queryset()
        trending_paginator = Paginator(trending, 25)  # Show 25 contacts per page.
        trend_page_number = request.GET.get("trend_page")
        trend_page = trending_paginator.get_page(trend_page_number)

        follow = get_followed_posts_queryset(self.request.user)
        follow_paginator = Paginator(follow, 25)  # Show 25 contacts per page.
        follow_page_number = request.GET.get("follow_page")
        follow_page = follow_paginator.get_page(follow_page_number)

        return render(
            request,
            "press/home.html",
            {"trend_page_obj": trend_page, "follow_page_obj": follow_page},
        )
