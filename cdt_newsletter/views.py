import os
import mimetypes

from docx import Document
from htmldocx import HtmlToDocx

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper

from .models import Subscription, Newsletter
from .forms import Subscriptionform, Newsletterform
from .utils import generate_page_content, create_qmd_file, generate_newsletter_body
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
    return render(
        request,
        'cdt_newsletter/newsletter_subscription.html',
        context)

def create_newsletter(request):

    if request.method == 'POST':
        form = Newsletterform(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data

            newsletter_body = generate_newsletter_body(form_data)
            context = {
                'newsletter_body' : newsletter_body
            }

            document = Document()
            new_parser = HtmlToDocx()

            new_parser.add_html_to_document(newsletter_body, document)
            document.save('newsletter.doc')

            try: 
                form.save()
                messages.success(request, "Newsletter Created!")
            except Exception as ex:
                messages.error(
                        request, "Oops! Something went wrong. Please check your input and try again.")
                
            return render(request, 'cdt_newsletter/newsletter_visualization.html', context)
            

    form = Newsletterform()
    context = {
        'form' : form
    }
    return render(
        request,
        'cdt_newsletter/create_newsletter.html',
        context
    )

def download_newsletter(request):

    if request.method == 'GET':
            directory = os.getcwd()
            filepath = directory + '/newsletter.doc'

            path = open(filepath, 'rb')
            
            mime_type, _ = mimetypes.guess_type(filepath)
            
            response = HttpResponse(path, content_type=mime_type)
            
            response['Content-Disposition'] = "attachment; filename=newsletter.doc"

            return response