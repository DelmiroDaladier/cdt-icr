import os
import datetime
import mimetypes
from itertools import chain

from docx import Document
from htmldocx import HtmlToDocx

from django.contrib import messages
from django.utils.safestring import mark_safe
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper

from formtools.preview import FormPreview
from repository.utils import create_push_request
from .forms import (
    Newsletterform,
    AnnouncementForm,
)
from .models import (
    Newsletter,
    Announcement,
    Event,
)
from .utils import (
    generate_newsletter_body,
    parse_html_to_text,
    create_newsletter_file_and_push,
)
from django.contrib.auth.decorators import (
    login_required,
)


@login_required
def review_newsletter(request):
    """
    Handle subscription form submissions and render the subscription page.

    If the request method is POST, process the
    form data and create a new subscription
    if the form is valid. Then redirect the
    user to the subscription page with a
    success message.

    If the request method is not POST, or if the form
    is invalid, render the subscription
    page with an empty subscription form.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object with the subscription page.
    """
    if request.method == "GET":
        context = {}

        return render(
            request,
            "cdt_newsletter/newsletter_visualization.html",
            context=context,
        )


@login_required
def create_newsletter(request):
    """
    Create a weekly newsletter and provide a visualization.

    This view function handles the creation of a weekly newsletter. It processes a submitted form, updates the state
    of announcements, generates the newsletter content, saves it as a document, and renders it for visualization.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A response object rendered with the newsletter content or the newsletter creation form.

    Raises:
        None.
    """
    if request.method == "POST":
        form = Newsletterform(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data

            for object in form_data["announcements"]:
                object.published = True
                object.save()

            forthcoming_events = Event.objects.all().order_by("date")

            newsletter_body = generate_newsletter_body(form_data, forthcoming_events)

            context = {"newsletter_body": newsletter_body}

            document = Document()
            new_parser = HtmlToDocx()

            new_parser.add_html_to_document(newsletter_body, document)
            document.save("newsletter.doc")

            try:
                form.save()
                messages.success(request, "Newsletter Created!")
            except Exception as ex:
                messages.error(
                    request,
                    "Oops! Something went wrong."
                    "Please check your input and try again.",
                )

            return render(
                request,
                "cdt_newsletter/newsletter_visualization.html",
                context=context,
            )
        else:
            print(form.errors)

    data_dict = {
        "title": "CDT Weekly Newsletter",
        "text": "Welcome to this week's issue of the newsletter.",
    }

    form = Newsletterform(initial=data_dict)
    context = {"form": form}
    return render(
        request,
        "cdt_newsletter/create_newsletter.html",
        context,
    )


@login_required
def download_newsletter(request):
    """
    Download a newsletter document.

    This view function allows authenticated users to download a newsletter document in 'doc' format.

    Args:
        request (HttpRequest): The HTTP GET request object.

    Returns:
        HttpResponse: A response object that serves the newsletter document as a downloadable attachment.

    Raises:
        None.
    """
    if request.method == "GET":
        directory = os.getcwd()
        filepath = directory + "/newsletter.doc"

        path = open(filepath, "rb")

        mime_type, _ = mimetypes.guess_type(filepath)

        response = HttpResponse(path, content_type=mime_type)

        response["Content-Disposition"] = "attachment; filename=newsletter.doc"

        return response


@login_required
def create_announcement(request):
    """
    Create an announcement or event and provide a link to the created item.

    This view function handles the creation of announcements or events based on a submitted form. It saves the
    created object, displays a success message with a link to the created item, and handles errors or invalid input.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A response object rendered with the form or a success message.

    Raises:
        None.
    """
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        context = {"form": form}
        if form.is_valid():
            try:
                data = form.cleaned_data
                if data.get("date"):
                    created_object = Event.objects.create(**data)
                else:
                    del data["date"]
                    created_object = Announcement.objects.create(**data)
                    created_object.save()

                messages.success(
                    request,
                    mark_safe(
                        f"Announcement Created! Check the created announcement <a href=/announcement/{created_object.id} >here</a>"  # noqa
                    ),
                )

                context["form"] = AnnouncementForm()

                return render(
                    request,
                    "cdt_newsletter/create_announcement.html",
                    context,
                )
            except Exception as ex:
                print(ex)
                messages.error(
                    request,
                    "Oops! Something went wrong."
                    "Please check your input and try again.",
                )

                return render(
                    request,
                    "cdt_newsletter/create_announcement.html",
                    context,
                )
        else:
            messages.error(request, form.errors.as_text())

    form = AnnouncementForm()
    context = {"form": form}
    return render(
        request,
        "cdt_newsletter/create_announcement.html",
        context,
    )


class NewsletterPreview(FormPreview):
    """
    Custom form preview class for newsletter creation.

    This custom form preview class is used to create and preview newsletters. It inherits from Django's FormPreview
    class and provides methods for generating a preview, processing form data, and finalizing newsletter creation.

    Attributes:
        form_template (str): The path to the template used for the form.
        preview_template (str): The path to the template used for the preview.

    Methods:
        get_context(self, request, form): Get the context data for rendering the preview.
        process_preview(self, request, form, context): Process the newsletter preview.
        done(self, request, cleaned_data): Finalize newsletter creation.

    Raises:
        None.
    """

    form_template = "cdt_newsletter/create_newsletter.html"
    preview_template = "cdt_newsletter/newsletter_visualization.html"

    def get_context(self, request, form):
        if form.is_valid():
            render_data = {
                "title": form.cleaned_data["title"],
                "text": form.cleaned_data["text"],
                "announcements": form.cleaned_data["announcements"],
                "events": Event.objects.all().order_by("date"),
            }
            return {
                "render_data": render_data,
                "form": form,
                "stage_field": self.unused_name("stage"),
                "state": self.state,
            }

    def process_preview(self, request, form, context):
        today = datetime.datetime.today()
        forthcoming_events = Event.objects.filter(date__gte=today).order_by("date")

        if form.is_valid():
            cleaned_data = form.cleaned_data

            newsletter_body = generate_newsletter_body(
                cleaned_data,
                forthcoming_events,
            )

            document = Document()
            new_parser = HtmlToDocx()

            new_parser.add_html_to_document(newsletter_body, document)
            document.save("newsletter.doc")

        return context

    def done(self, request, cleaned_data):
        today = datetime.datetime.today()
        forthcoming_events = Event.objects.filter(date__gte=today).order_by("date")

        for object in cleaned_data["announcements"]:
            object.published = True
            object.save()

        newsletter_body = generate_newsletter_body(cleaned_data, forthcoming_events)

        parsed_body = parse_html_to_text(newsletter_body)

        newsletter = {
            "title": cleaned_data["title"],
            "text": parsed_body,
        }

        try:
            Newsletter.objects.create(**newsletter)
        except Exception as ex:
            print(ex)
            messages.error(
                request,
                "Please check the submitted information.",
            )
            return redirect("create_newsletter")

        try:
            folder_name = cleaned_data["title"]
            folder_name = folder_name.lower()
            folder_name = folder_name.replace(" ", "_")
            today_str = today.strftime("%d-%m-%Y")
            if folder_name == "cdt_weekly_newsletter":
                folder_name = f"{folder_name}-{today_str}"

            relative_path_list = [f"{folder_name}/index.qmd"]
            project_name = "newsletter_frontend"
            repo = "newsletter_frontend"

            create_newsletter_file_and_push(
                folder_name,
                relative_path_list,
                project_name,
                repo,
                newsletter_body,
                today_str,
            )

        except Exception as ex:
            print(ex)
            messages.error(
                request,
                "Please check the submitted information.",
            )
            return redirect("create_newsletter")

        return HttpResponseRedirect("/newsletter_submission_success")


@login_required
def newsletter_submission_success(request):
    """
    Render a success page for newsletter submission.

    This view function renders a success page to inform users that their newsletter submission was successful.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A response object rendering the success page.

    Raises:
        None.
    """
    context = {}
    return render(
        request,
        "cdt_newsletter/newsletter_submission_success.html",
        context,
    )


@login_required
def announcements(request):
    """
    Display a list of announcements.

    This view function retrieves a list of announcements from the database and displays them on a webpage.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A response object rendered with the list of announcements.

    Raises:
        None.
    """

    all_announcements = Announcement.objects.all()
    events = Event.objects.all()  # Filtra apenas os eventos
    announcements = all_announcements.exclude(pk__in=events.values_list("pk", flat=True))

    context = {
        "announcements": announcements,
        "events": events}

    return render(
        request,
        "cdt_newsletter/announcements.html",
        context=context,
    )


@login_required
def announcement_detail(request, pk):
    """
    Display details of a specific announcement.

    This view function retrieves the details of a specific announcement from the database and displays them on a webpage.

    Args:
        request (HttpRequest): The HTTP request object.
        pk (int): The primary key of the announcement to be displayed.

    Returns:
        HttpResponse: A response object rendered with the details of the specific announcement.

    Raises:
        Announcement.DoesNotExist: If the specified announcement does not exist in the database.
    """
    announcement = Announcement.objects.get(pk=pk)

    event = Event.objects.filter(pk=pk).first()

    if event:
        announcement = event

    context = {"announcement": announcement}

    return render(request, "cdt_newsletter/announcement_detail.html", context)

@login_required
def edit_announcement(request, pk):
    """
    Edit an existing announcement.

    This view function allows users to edit an existing announcement. It retrieves the announcement's data from the
    database, pre-fills the form with the existing data, and updates the announcement if the submitted form is valid.

    Args:
        request (HttpRequest): The HTTP request object.
        pk (int): The primary key of the announcement to be edited.

    Returns:
        HttpResponse: A response object that renders the form for editing the announcement or redirects to the announcement detail page.

    Raises:
        Announcement.DoesNotExist: If the specified announcement does not exist in the database.
    """
    data = Announcement.objects.get(id=int(pk))
    form = AnnouncementForm(instance=data)

    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=data)

        if form.is_valid():
            form.save()
            return redirect(f"/announcements/{pk}/")

    context = {"form": form}

    return render(
        request,
        "cdt_newsletter/update_announcement.html",
        context,
    )


@login_required
def delete_announcement(request, pk):
    """
    Delete an existing announcement.

    This view function allows users to delete an existing announcement from the database.

    Args:
        request (HttpRequest): The HTTP request object.
        pk (int): The primary key of the announcement to be deleted.

    Returns:
        HttpResponseRedirect: A redirection to the announcements page after the announcement is deleted.

    Raises:
        Announcement.DoesNotExist: If the specified announcement does not exist in the database.
    """
    announcement = Announcement.objects.get(id=pk)
    announcement.delete()

    return redirect("/announcements")
