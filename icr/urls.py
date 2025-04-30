from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.i18n import JavaScriptCatalog

from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from blog.views import blog_homepage
from cdt_newsletter.views import (
    review_newsletter,
    create_newsletter,
    download_newsletter,
    create_announcement,
    NewsletterPreview,
    newsletter_submission_success,
    announcements,
    edit_announcement,
    announcement_detail,
    delete_announcement,
)
from cdt_newsletter.forms import Newsletterform
from repository.views import (
    homepage,
    about,
    signup,
    activate,
    help_page,
    user_profile,
    edit_profile,
    author_create,
    add_category,
    add_venue,
    update_post,
    arxiv_post,
    submit_conference,
    submit_session,
)

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path("admin/", admin.site.urls),
    path("", homepage, name="homepage"),
    path("about/", about, name="about"),
    path("signup/", signup, name="signup"),
    path("activate/<slug:uidb64>/<slug:token>/", activate, name="activate"),
    path('profile/<str:username>/', user_profile, name='profile'),
    path('edit_profile/<int:pk>/', edit_profile, name='edit_profile'),
    path("update_post/<slug>/", update_post, name="update_post"),
    path("author_create/", author_create, name="author_create"),
    path("add_category/", add_category, name="add_category"),
    path("add_venue/", add_venue, name="add_venue"),
    path("blog/", blog_homepage, name="blog_homepage"),
    path("arxiv_post/", arxiv_post, name="arxiv_post"),
    path("submit_conference/", submit_conference, name="submit_conference"),
    path("submit_session/", submit_session, name="submit_session"),
    path("review_newsletter", review_newsletter, name="review_newsletter"),
    path("create_newsletter", create_newsletter, name="create_newsletter"),
    path("download_newsletter", download_newsletter, name="download_newsletter"),
    path("create_announcement", create_announcement, name="create_announcement"),
    path(
        "newsletter_preview",
        NewsletterPreview(Newsletterform),
        name="newsletter_preview",
    ),
    path(
        "newsletter_submission_success",
        newsletter_submission_success,
        name="newsletter_submission_success",
    ),
    path("announcements", announcements, name="announcements"),
    path(
        "announcement/<int:pk>",
        announcement_detail,
        name="announcement_detail",
    ),
    path(
        "edit_announcement/<int:pk>/",
        edit_announcement,
        name="edit_announcement",
    ),
    path(
        "delete_announcement/<int:pk>/",
        delete_announcement,
        name="delete_announcement",
    ),
    path("help", help_page, name="help"),
    re_path(
        r"^jsi18n/$",
        JavaScriptCatalog.as_view(),
        name="jsi18n",
    ),
    path('tinymce/', include('tinymce.urls'))
]

urlpatterns += [
    path("accounts/", include("django.contrib.auth.urls")),
]
