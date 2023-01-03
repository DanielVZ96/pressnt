from django.urls import path

from press.views import (
    Home,
    PostCreate,
    PostDetail,
    UserPostDetail,
    PostUpdate,
    RegisterView,
    UpdateProfileView,
    ProfileDetailView,
    EmailSentView,
    VerifyView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", UpdateProfileView.as_view(), name="profile-update"),
    path("profile/preview/", ProfileDetailView.as_view(), name="profile-preview"),
    path("profile/<int:pk>/", ProfileDetailView.as_view(), name="profile-detail"),
    path("post/create/", PostCreate.as_view(), name="post-create"),
    path("post/<int:pk>/", PostDetail.as_view(), name="post-detail"),
    path("post/me/", UserPostDetail.as_view(), name="user-post-detail"),
    path("post/", PostUpdate.as_view(), name="post-update"),
    path("sent/", EmailSentView.as_view(), name="email-sent"),
    path("verify/<str:token>/", VerifyView.as_view(), name="verify-email"),
    path("", Home.as_view(), name="home"),
]
