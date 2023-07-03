from django.conf import settings 
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django import views as django_views

from blog.views import blog_homepage
from cdt_newsletter.views import review_newsletter, create_newsletter, download_newsletter, create_announcement, NewsletterPreview, newsletter_submission_success, announcements, edit_announcement, announcement_detail
from cdt_newsletter.forms import Newsletterform
from repository.views import homepage, about, author_create, add_category, add_venue, update_post, arxiv_post, register_request, submit_conference, submit_session


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', homepage, name = 'homepage'),
    path('about/', about, name = 'about'),
    path('update_post/<slug>/', update_post, name='update_post'),
    path('author_create/', author_create, name='author_create'),
    path('add_category/', add_category, name='add_category'),
    path('add_venue/', add_venue, name='add_venue'),
    path('blog/', blog_homepage, name='blog_homepage'),
    path('arxiv_post/', arxiv_post, name='arxiv_post'),
    path('register/', register_request, name='register'),
    path('submit_conference/', submit_conference, name='submit_conference'),
    path('submit_session/', submit_session, name='submit_session'),
    path('review_newsletter', review_newsletter, name='review_newsletter'),
    path('create_newsletter', create_newsletter, name='create_newsletter'),
    path('download_newsletter', download_newsletter, name='download_newsletter'),
    path('create_announcement', create_announcement, name='create_announcement'),
    path('newsletter_preview', NewsletterPreview(Newsletterform), name='newsletter_preview'),
    path('newsletter_submission_success', newsletter_submission_success, name='newsletter_submission_success'),
    path('announcements', announcements, name='announcements'),
    path('announcement/<int:pk>', announcement_detail, name='announcement_detail'),
    path('edit_announcement/<int:pk>', edit_announcement, name='edit_announcement'),
    url(r'^jsi18n/$', django_views.i18n.JavaScriptCatalog.as_view(), name='jsi18n'),
]

urlpatterns += [
    path('accounts/', include('django.contrib.auth.urls')),
]