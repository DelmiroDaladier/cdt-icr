import os
from django.contrib import messages
from django.shortcuts import render, redirect

from .models import Subscription, Newsletter
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