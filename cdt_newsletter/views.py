import os
from django.contrib import messages
from django.shortcuts import render, redirect

from .models import Subscription, Newsletter
from repository.models import Post, Conference
from .forms import Subscriptionform, Newsletterform
from .utils import generate_page_content, create_qmd_file
from repository.utils import create_push_request

def newsletter_subscription(request):
    """
    Handle subscription form submissions and render the subscription page.

    If the request method is POST, process the form data and create a new subscription
    if the form is valid. Then redirect the user to the subscription page with a success
    message.

    If the request method is not POST, or if the form is invalid, render the subscription
    page with an empty subscription form.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object with the subscription page.
    """
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