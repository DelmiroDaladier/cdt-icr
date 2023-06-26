import os
import datetime
import mimetypes

from docx import Document
from htmldocx import HtmlToDocx

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper

from .models import Subscription, Newsletter, Announcement, Event
from .forms import Newsletterform, AnnouncementForm
from .utils import generate_page_content, create_qmd_file, generate_newsletter_body
from repository.utils import create_push_request


def review_newsletter(request):
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
    if request.method == 'GET':
        context = {}

        return render(request,
                      'cdt_newsletter/review_newsletter.html',
                      context=context)


def create_newsletter(request):

    if request.method == 'POST':
        form = Newsletterform(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data

            for object in form_data['announcements']:
                object.published = True
                object.save()
            
            now = datetime.datetime.now()
            delta = now - datetime.timedelta(days=-30)
            


            forthcoming_events = Event.objects.all().order_by('date')

            newsletter_body = generate_newsletter_body(form_data, forthcoming_events)
            
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
        else:
            print(form.errors)   

    data_dict = {
        'title': 'CDT Weekly Newsletter',
        'text': "Welcome to this week's issue of the newsletter."
    }

    form = Newsletterform(data_dict)
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

def create_announcement(request):
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        context = {
            'form': form
        }
        if form.is_valid():
            try:
                data = form.cleaned_data
                if data.get('date'):
                    Event.objects.create(**data)
                else:
                    del data['date']
                    Announcement.objects.create(**data)
                messages.success(request, "Announcement Created!")

                return render(request, 'cdt_newsletter/create_announcement.html', context) 
            except Exception as ex:
                print(ex)    
                messages.error(
                        request, "Oops! Something went wrong. Please check your input and try again.")
                
                return render(request, 'cdt_newsletter/create_announcement.html', context) 
        else:
            messages.error(request, form.errors.as_text())   


    form = AnnouncementForm()
    context = {
        'form': form
    }
    return render(
        request,
        'cdt_newsletter/create_announcement.html',
        context
    )