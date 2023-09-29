import os
import datetime
import mimetypes

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
    if request.method == "POST":
        form = Newsletterform(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data

            for object in form_data[
                "announcements"
            ]:
                object.published = True
                object.save()

            forthcoming_events = (
                Event.objects.all().order_by(
                    "date"
                )
            )

            newsletter_body = (
                generate_newsletter_body(
                    form_data, forthcoming_events
                )
            )

            context = {
                "newsletter_body": newsletter_body
            }

            document = Document()
            new_parser = HtmlToDocx()

            new_parser.add_html_to_document(
                newsletter_body, document
            )
            document.save("newsletter.doc")

            try:
                form.save()
                messages.success(
                    request, "Newsletter Created!"
                )
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
    if request.method == "GET":
        directory = os.getcwd()
        filepath = directory + "/newsletter.doc"

        path = open(filepath, "rb")

        mime_type, _ = mimetypes.guess_type(
            filepath
        )

        response = HttpResponse(
            path, content_type=mime_type
        )

        response[
            "Content-Disposition"
        ] = "attachment; filename=newsletter.doc"

        return response


@login_required
def create_announcement(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        context = {"form": form}
        if form.is_valid():
            try:
                data = form.cleaned_data
                if data.get("date"):
                    created_object = (
                        Event.objects.create(
                            **data
                        )
                    )
                else:
                    del data["date"]
                    created_object = Announcement.objects.create(
                        **data
                    )
                    created_object.save()

                messages.success(
                    request,
                    mark_safe(
                        f"Announcement Created! Check the created announcement <a href=/announcement/{created_object.id} >here</a>"  # noqa
                    ),
                )

                context[
                    "form"
                ] = AnnouncementForm()

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
            messages.error(
                request, form.errors.as_text()
            )

    form = AnnouncementForm()
    context = {"form": form}
    return render(
        request,
        "cdt_newsletter/create_announcement.html",
        context,
    )


class NewsletterPreview(FormPreview):
    form_template = (
        "cdt_newsletter/create_newsletter.html"
    )
    preview_template = "cdt_newsletter/newsletter_visualization.html"

    def get_context(self, request, form):
        if form.is_valid():
            render_data = {
                "title": form.cleaned_data[
                    "title"
                ],
                "text": form.cleaned_data["text"],
                "announcements": form.cleaned_data[
                    "announcements"
                ],
                "events": Event.objects.all().order_by(
                    "date"
                ),
            }
            return {
                "render_data": render_data,
                "form": form,
                "stage_field": self.unused_name(
                    "stage"
                ),
                "state": self.state,
            }

    def process_preview(
        self, request, form, context
    ):
        forthcoming_events = (
            Event.objects.all().order_by("date")
        )

        if form.is_valid():
            cleaned_data = form.cleaned_data

            newsletter_body = (
                generate_newsletter_body(
                    cleaned_data,
                    forthcoming_events,
                )
            )

            document = Document()
            new_parser = HtmlToDocx()

            new_parser.add_html_to_document(
                newsletter_body, document
            )
            document.save("newsletter.doc")
        return context

    def done(self, request, cleaned_data):
        for object in cleaned_data[
            "announcements"
        ]:
            object.published = True
            object.save()

        newsletter_body = (
            generate_newsletter_body(
                cleaned_data, forthcoming_events
            )
        )
        parsed_body = parse_html_to_text(
            newsletter_body
        )

        newsletter = {
            "title": cleaned_data["title"],
            "text": parsed_body,
        }

        Newsletter.objects.create(**newsletter)
        return HttpResponseRedirect(
            "/newsletter_submission_success"
        )


@login_required
def newsletter_submission_success(request):
    context = {}
    return render(
        request,
        "cdt_newsletter/newsletter_submission_success.html",
        context,
    )


@login_required
def announcements(request):
    objects = Announcement.objects.all()

    context = {"announcements": objects}

    return render(
        request,
        "cdt_newsletter/announcements.html",
        context=context,
    )


@login_required
def announcement_detail(request, pk):
    announcement = Announcement.objects.get(pk=pk)

    context = {"announcement": announcement}

    return render(
        request,
        "cdt_newsletter/announcement_detail.html",
        context,
    )


@login_required
def edit_announcement(request, pk):
    data = Announcement.objects.get(id=int(pk))
    form = AnnouncementForm(instance=data)

    if request.method == "POST":
        print("post request")
        form = AnnouncementForm(
            request.POST, instance=data
        )

        if form.is_valid():
            form.save()
            return redirect(
                f"/announcements/{pk}/"
            )

    print("DEU GET")
    context = {"form": form}

    return render(
        request,
        "cdt_newsletter/update_announcement.html",
        context,
    )


@login_required
def delete_announcement(request, pk):
    announcement = Announcement.objects.get(id=pk)
    announcement.delete()

    return redirect("/announcements")
