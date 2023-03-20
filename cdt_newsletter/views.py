import os
from django.contrib import messages
from django.shortcuts import render, redirect

from .models import Subscription
from repository.models import Post, Conference
from .forms import Subscriptionform, Newsletterform
from .utils import generate_page_content, create_qmd_file
from repository.utils import create_push_request

def newsletter_subscription(request):
    if request.method == 'POST':
        form = Subscriptionform(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subscription Successful')
            return redirect('newsletter_subscription')
    
    form = Subscriptionform()
    context = {
        'form': form
    }
    return render(request, 'cdt_newsletter/newsletter_subscription.html', context)

def generate_newsletter(request):
    emails = Subscription.objects.all()
    email_list = list(emails.values())
    email_list = [item['email'] for item in email_list]

    posts = Post.objects.all()
    posts = list(posts.values())

    conferences = Conference.objects.all()
    conferences = list(conferences.values())

    content = {
        'posts': posts,
        'conferences': conferences
    }

    current_path = os.getcwd()
    filepath = current_path + \
                        f'/newsletter_frontend/index.qmd'

    create_qmd_file(filepath)
    
    generate_page_content(filepath, content)

    repo = 'newsletter_frontend'
    path = 'index.qmd'
    create_push_request(file_path=filepath, folder_name='', repo=repo, path=path)


    if request.method == 'POST':
        form = Newsletterform(request.POST)
        if form.is_valid():
            form.save()

            return redirect('generate_newsletter')
    form = Newsletterform()
    context = {
        'form': form
    }
    return render(request, 'cdt_newsletter/mail_newsletter.html', context=context)
