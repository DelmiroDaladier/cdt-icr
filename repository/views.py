import os
import yaml
import json
import requests
import urllib3

from dotenv import load_dotenv
from django.core import serializers
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse
from django.template.loader import (
    render_to_string,
)
from django.utils.encoding import (
    force_bytes,
    force_text,
)
from django.contrib.sites.shortcuts import (
    get_current_site,
)
from django.utils.http import (
    urlsafe_base64_encode,
    urlsafe_base64_decode,
)
from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.contrib.auth.decorators import (
    login_required,
)
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from .models import (
    Conference,
    Author,
    Publication,
    ResearchArea,
)
from .forms import (
    UpdateUserForm,
    PublicationForm,
    AuthorForm,
    VenueForm,
    ResearchAreaForm,
    ArxivForm,
    NewUserForm,
    ConferenceForm,
    SessionForm,
)
from .utils import (
    generate_qmd_header,
    generate_page_content,
    create_push_request,
    generate_qmd_header_for_arxiv,
    scrap_data_from_arxiv,
    get_conference_information,
    save_new_conference_data,
    generate_researcher_profile,
    update_repo_and_push,
    git_pull
)
from .tokens import account_activation_token

from django.db import IntegrityError


@login_required
def homepage(request):
    """
    This function generates a homepage view. It handles the request received through POST method, validates the data entered in the PostForm form, generates a QMD header and content for the post, creates a new folder and file in the repository, and pushes the changes to GitHub. If the request method is GET, it renders a new_post.html page with an empty form.

    Args:
    request (HttpRequest): A request object representing a HTTP request.

    Returns:
    If the request method is POST and the form data is valid, it renders a submission.html page with the new post's folder name and the form used to submit the post. If the form data is invalid, it redirects the user to the homepage. If an exception occurs during the process, it displays an error message and redirects the user to the homepage. If the request method is GET, it renders a new_post.html page with an empty form.
    # noqa
    """
    load_dotenv()
    env_name = os.getenv("ENV_NAME")

    if request.method == "POST":
        filled_form = PublicationForm(request.POST)
        context = {}

        try:
            if filled_form.is_valid():
                try:
                    filled_form.save()

                except ValidationError as validation_error:
                    print(validation_error)
                    messages.error(
                        request,
                        "Publication with this Name already exists.",
                    )
                    return redirect("")

                except IntegrityError as integrity:
                    print(f"Exeception: {integrity}")
                    messages.error(
                        request,
                        "Integrity error. Check the information submitted,"
                        " it could be redundant or missing some fields.",
                    )
                    return redirect("")

                except Exception as ex:
                    print(ex)
                    messages.error(
                        request,
                        "Please check the submitted information.",
                    )
                    return redirect("")

                form_data = filled_form.cleaned_data

                content = {}

                try:
                    content = generate_qmd_header(content, form_data)
                    folder_name = slugify(content.get("title", ""))
                    git_pull('icr_frontend')

                    current_path = os.getcwd()

                    current_path = (
                        current_path + f"/icr_frontend/content/{folder_name}/"
                    )

                    file_path = f"{current_path}index.qmd"

                    if not os.path.exists(current_path):
                        os.makedirs(current_path)

                    with open(file_path, "w+") as fp:
                        fp.write("---\n")
                        yaml.dump(content, fp)
                        fp.write("\n---")

                except Exception as ex:
                    print(ex)
                    messages.error(
                        request,
                        "We are experiencing problems when creating qmd"
                        " headers. Please try again later.",
                    )

                try:
                    generate_page_content(
                        content,
                        file_path,
                        arxiv=False,
                    )
                except Exception as ex:
                    print(ex)
                    messages.error(
                        request,
                        "We are experiencing problems when filling qmd"
                        " files. Please try again later.",
                    )

                try:
                    repo = "icr"
                    path = f"content/{folder_name}/index.qmd"

                    relative_path_list = [
                        f"content/{folder_name}/index.qmd",
                        "input.csv",
                    ]

                    project_name = "icr_frontend"

                    if env_name == "prod":
                        update_repo_and_push(
                            folder_name, relative_path_list, project_name, repo
                        )
                    else:
                        print("Run quarto preview command to check the local changes·")

                except Exception as ex:
                    print(ex)
                    messages.error(
                        request,
                        "We are experiencing some problems when"
                        "  communication with github."
                        " Please Try again later.",
                    )
                    return redirect("/")

                context = {
                    "folder_name": folder_name,
                    "form": filled_form,
                    "repo": "icr_frontend",
                }

                return render(
                    request,
                    "repository/submission.html",
                    context,
                )
            print(filled_form.errors.as_data())
            messages.error(
                request,
                "The form is invalid, please review your submission.",
            )
            return redirect("/")

        except Exception as ex:
            print(ex)
            filled_form.add_error(None, "Form validation error.")
            messages.error(
                request,
                "The form is invalid, please review your submission.",
            )
            return redirect("/")

    else:
        filled_form = PublicationForm()
        return render(
            request,
            "repository/new_post.html",
            context={"form": filled_form},
        )


def about(request):
    """
    Render the about page HTML content.

    Args:
        request (HttpRequest): An object containing metadata about the current request.

    Returns:
        HttpResponse: An HTTP response object that renders the 'about_page.html' template.
    # noqa
    """
    return render(request, "repository/about_page.html")


@login_required
def author_create(request):
    """
    Create a new Author instance and render the create_author HTML page.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: If the request method is GET, returns an HTTP response object
        that renders the 'create_author.html' template with an empty AuthorForm instance
        provided to the template context.

        JsonResponse: If the request method is POST and the submitted form data is valid,
        returns a JSON response object containing the serialized Author instance and an
        HTTP status code of 200.

        HttpResponse: If the request method is POST and the submitted form data is invalid,
        returns an HTTP response object that renders the 'create_author.html' template
        with the invalid form instance and an error message provided to the template context.
    # noqa
    """
    if request.method == "GET":
        form = AuthorForm()
        context = {"form": form}
        return render(
            request,
            "repository/create_author.html",
            context=context,
        )

    form = AuthorForm(request.POST)
    if form.is_valid():
        try:
            author_instance = form.save()
            instance = serializers.serialize(
                "json",
                [
                    author_instance,
                ],
            )
            return JsonResponse({"instance": instance}, status=200)
        except IntegrityError as integrity:
            messages.error(
                request,
                "IntegrityError: Something went wrong with"
                " the input data."
                "Please check your input and try again.",
            )
            return render(
                request,
                "repository/create_author.html",
                context=context,
            )
    else:
        messages.error(
            request,
            "The form data is invalid," "please review your submission.",
        )
        return render(
            request,
            "repository/create_author.html",
            context=context,
        )


@login_required
def add_venue(request):
    """
    Add a new venue to the system.

    If the request method is GET, a new VenueForm instance is created and rendered to a template.

    If the request method is POST, the VenueForm is populated with data from the request.POST, validated, and saved
    to the database if valid. If the form is not valid, an error message is displayed to the user.

    Args:
        request: HttpRequest object representing the current request.

    Returns:
        If the request method is GET, returns a rendered template with a new VenueForm instance.
        If the request method is POST and the VenueForm is valid, returns a JsonResponse with the saved venue instance
        in JSON format and a status code of 200. If the form is not valid, returns a rendered template with an error message.
    # noqa
    """
    if request.method == "GET":
        form = VenueForm()
        context = {"form": form}
        return render(
            request,
            "repository/add_venue.html",
            context=context,
        )

    form = VenueForm(request.POST)

    if form.is_valid():
        try:
            venue_instance = form.save()
            instance = serializers.serialize(
                "json",
                [
                    venue_instance,
                ],
            )
            return JsonResponse({"instance": instance}, status=200)
        except Exception as ex:
            messages.error(
                request,
                "IntegrityError: "
                "Something went wrong with the input data."
                "Please check your input and try again.",
            )
            return render(
                request,
                "repository/add_venue.html",
                context=context,
            )
    else:
        messages.error(
            request,
            "The venue form is invalid, please review your submission.",
        )
        return render(
            request,
            "repository/add_venue.html",
            context=context,
        )


@login_required
def add_category(request):
    """
    View function for adding a new category.

    If the request method is GET, the function renders a form for creating a new category.

    If the request method is POST, the function attempts to validate the form data. If the form is valid,
    a new category instance is created and returned as JSON in a 200 response. If the form is invalid,
    an error message is displayed and the form is re-rendered.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A rendered HTML template or JSON response.

    Raises:
        None
    # noqa
    """
    if request.method == "GET":
        form = ResearchAreaForm()

        context = {"form": form}
        return render(
            request,
            "repository/add_category.html",
            context=context,
        )

    form = ResearchAreaForm(request.POST)
    if form.is_valid():
        category_instance = form.save()
        instance = serializers.serialize(
            "json",
            [
                category_instance,
            ],
        )
        return JsonResponse({"instance": instance}, status=200)
    else:
        messages.error(
            request,
            "The category is invalid," " please review your submission.",
        )
        return render(
            request,
            "repository/add_category.html",
            context={},
        )


@login_required
def update_post(request, slug):
    """
    Update an existing post in the system.

    If the request method is GET, a PostForm instance is created with the current post's data and rendered to a template.

    If the request method is POST, the PostForm is populated with data from the request.POST, validated, and updated
    in the database if valid. If the form is not valid, an error message is displayed to the user.

    Args:
        request: HttpRequest object representing the current request.
        slug: The slug of the post to be updated.

    Returns:
        If the request method is GET, returns a rendered template with a PostForm instance populated with the current
        post's data.
        If the request method is POST and the PostForm is valid, returns a JsonResponse with the updated post instance
        in JSON format and a status code of 200. If the form is not valid, returns a JsonResponse with an error message
        and a status code of 200.
    # noqa
    """
    context = {}

    post = get_object_or_404(Publication, slug=slug)
    form = PublicationForm(request.POST or None, instance=post)

    if request.method == "GET":
        context = {"form": form}
        return render(
            request,
            "repository/update_post.html",
            context=context,
        )

    if form.is_valid():
        post_instance = Publication.objects.get(slug=slug)
        form = PublicationForm(request.POST, instance=post)
        form.save()
        instance = serializers.serialize(
            "json",
            [
                post_instance,
            ],
        )
        return JsonResponse({"instance": instance}, status=200)
    else:
        messages.error(
            request,
            "The form is invalid," "please review your submission.",
        )
        return JsonResponse({"instance": instance}, status=200)


@login_required
def arxiv_post(request):
    """
    Create a post from an Arxiv link.

    If the request method is GET, an ArxivForm instance is created and rendered to a template.

    If the request method is POST, the ArxivForm is populated with data from the request.POST, validated, and a post is
    created from the data. If the form is not valid, an error message is displayed to the user.

    Args:
        request: HttpRequest object representing the current request.

    Returns:
        If the request method is GET, returns a rendered template with an ArxivForm instance.
        If the request method is POST and the ArxivForm is valid, returns a rendered template with a success message and
        a folder name for the post. If the form is not valid, returns a rendered template with the form populated with
        the submitted data and any errors that occurred during validation.
    # noqa
    """
    load_dotenv()

    env_name = os.getenv("ENV_NAME")

    if request.method == "POST":
        context = {}

        filled_form = ArxivForm(request.POST)

        if filled_form.is_valid():
            form_data = filled_form.cleaned_data
            url = form_data.get("link", "")

            try:
                data = scrap_data_from_arxiv(url)

                entry_existis = Publication.objects.filter(name=data["citation_title"])

                if not entry_existis:
                    authors = []

                    for author, link in zip(
                        data["citation_author"],
                        data["links"],
                    ):
                        author = (
                            author.split(",")[1].strip()
                            + " "
                            + author.split(",")[0].strip()
                        )
                        author_obj = Author(
                            **{
                                "user_name": author,
                                "user_url": link,
                            }
                        )
                        try:
                            author_obj.save()
                            authors.append(author_obj)
                        except IntegrityError as integrity:
                            print(integrity)

                    if data["research_area"]:
                        research_area_obj = ResearchArea(
                            **{
                                "title": data["research_area"],
                            }
                        )
                        try:
                            research_area_obj.save()
                        except IntegrityError as integrity:
                            print(integrity)

                        research_Area_id = ResearchArea.objects.filter(
                            title=data["research_area"]
                        )[0].id

                    data_dict = {
                        "name": data["citation_title"],
                        "overview": data["citation_abstract"],
                        "pdf": data["citation_pdf"],
                    }

                    post_obj = Publication(**data_dict)

                    try:
                        post_obj.save()
                    except Exception as integrity:
                        messages.error(
                            request,
                            "IntegrityError: The input data you provided"
                            " already exists in the database. Please"
                            " review the existing records and ensure"
                            " that you are not duplicating data.",
                        )
                        return redirect("arxiv_post")

                    for author in authors:
                        post_obj.authors.add(author.user_id)

                    post_obj.research_area.add(research_Area_id)

                    post_obj.save()

                    try:
                        content = generate_qmd_header_for_arxiv(data)

                        folder_name = slugify(content.get("title", ""))

                        git_pull('icr_frontend')

                        current_path = os.getcwd()

                        current_path = (
                            current_path + f"/icr_frontend/content/{folder_name}/"
                        )
                        file_path = f"{current_path}index.qmd"

                        if not os.path.exists(current_path):
                            os.makedirs(current_path)

                        with open(file_path, "w+") as fp:
                            fp.write("---\n")
                            yaml.dump(content, fp)
                            fp.write("\n---")
                    except Exception as ex:
                        print(ex)
                        messages.error(
                            request,
                            "We are experiencing problems when creating qmd"
                            " headers. Please try again later.",
                        )

                    try:
                        generate_page_content(
                            content,
                            file_path,
                            arxiv=True,
                        )
                    except Exception as ex:
                        print(ex)
                        messages.error(
                            request,
                            "We are experiencing problems when filling qmd"
                            " files. Please try again later.",
                        )

                    try:
                        repo = "icr"
                        path = f"content/{folder_name}/index.qmd"

                        relative_path_list = [
                            f"content/{folder_name}/index.qmd",
                            "input.csv",
                        ]

                        project_name = "icr_frontend"

                        if env_name == "prod":
                            update_repo_and_push(
                                folder_name, relative_path_list, project_name, repo
                            )
                        else:
                            print(
                                "Run quarto preview command to check the local changes·"
                            )

                    except Exception as ex:
                        messages.error(
                            request,
                            "We are experiencing some problems "
                            "when communication with github."
                            " Please Try again later.",
                        )
                        return redirect("arxiv_post")

                    context = {
                        "folder_name": folder_name,
                        "form": filled_form,
                        "repo": "icr_frontend",
                    }

                    return render(
                        request,
                        "repository/submission.html",
                        context=context,
                    )

                else:
                    messages.error(
                        request,
                        "Integrity Error: The input data you provided"
                        " already exists in the database. "
                        "Please review the existing records and ensure"
                        " that you are not duplicating data.",
                    )
                    return redirect("arxiv_post")

            except Exception as ex:
                print(ex)
                messages.error(
                    request,
                    "We are experiencing some problems when fetching "
                    "information from the link. Please Try again later ",
                    "or check the link provided.",
                )
                return redirect("arxiv_post")

        messages.error(request, filled_form.errors.as_data())

    form = ArxivForm()
    context = {"form": form}
    return render(
        request,
        "repository/arxiv_post.html",
        context=context,
    )


def email_check(user):
    """
    Check if the user's email is from the University of Bristol domain.

    Parameters:
    user (django.contrib.auth.models.User): A user object.

    Returns:
    bool: True if the email is from the University of Bristol domain, False otherwise.
    # noqa
    """
    if user.is_authenticated:
        return user.email.endswith("@bristol.ac.uk")
    return False


def signup(request):
    """
    View function for user registration.

    Handles user registration by processing the submitted form data. If the HTTP request method is POST,
    it validates the form data, creates a new user account, and sends an activation email. If the registration
    is successful, it redirects to a confirmation page. If any errors occur during the registration process,
    appropriate error messages are displayed, and the user is redirected back to the signup page.

    Args:
        request (HttpRequest): The HTTP request object containing user data.

    Returns:
        HttpResponse: A response object rendered with the registration form or a confirmation page.

    Raises:
        IntegrityError: If an integrity error occurs during database operations.
        Exception: If any unexpected exception occurs during registration.
    """
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            try:
                load_dotenv()

                env_name = os.getenv("ENV_NAME")

                form_data = form.cleaned_data
                user = form.save(commit=False)
                user.is_active = False
                user.set_password(form.cleaned_data.get("password"))

                author_data = {
                    "user_name": form_data["first_name"] + " " + form_data["last_name"],
                    "member": user,
                    "bio": form_data["short_bio"],
                }
                author_obj = Author(**author_data)

                if Author.objects.filter(user_name=author_data["user_name"]):
                    print("Integrity error")
                    raise IntegrityError

                user.save()
                author_obj.save()

                input_data = {
                    "title": author_data.get("user_name", ""),
                    "user_bio": author_data.get("bio", ""),
                    "project_folder": "icr_frontend",
                    "sub_project_folder": "researchers",
                }

                generate_researcher_profile(input_data)

                current_site = get_current_site(request)

                mail_subject = "Activate your account."
                message = render_to_string(
                    "registration/acc_active_email.html",
                    {
                        "user": user,
                        "domain": current_site.domain,
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "token": account_activation_token.make_token(user),
                    },
                )
                to_email = form.cleaned_data.get("email")
                email = EmailMessage(
                    mail_subject,
                    message,
                    to=[to_email],
                )
                email.send()
                return render(
                    request,
                    "registration/confirm_registration.html",
                )
            except ValueError as value:
                print(value)
                messages.error(request, value)
                return redirect("signup")
            except IntegrityError as integrity_error:
                print(integrity_error)
                messages.error(
                    request,
                    "Integrity error. Check the information submitted,"
                    " it could be redundant or missing some fields.",
                )
                return redirect("signup")
            except Exception as ex:
                print(ex)
                messages.error(
                    request,
                    "Something went wrong with your submission."
                    " Try again later, please.",
                )
                return redirect("signup")

    else:
        form = NewUserForm()
    return render(
        request,
        "registration/signup.html",
        {"form": form},
    )


def activate(request, uidb64, token):
    """
    View function for activating a user account.

    This function handles the activation of a user account by verifying the provided UID and token.
    If the UID and token are valid, it activates the user's account and logs them in. If the activation
    is successful, it redirects to a success page. If the activation link is invalid, it displays an
    error message.

    Args:
        request (HttpRequest): The HTTP request object.
        uidb64 (str): The UID encoded in base64.
        token (str): The activation token for the user account.

    Returns:
        HttpResponse: A response object that either indicates a successful activation or an error message.

    Raises:
        None.
    """
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist,
    ):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)

        return render(
            request,
            "registration/activation_successfull.html",
        )
    else:
        return HttpResponse("Activation link is invalid!")


@login_required
def submit_conference(request):
    """
    Submits conference information to the website and saves it to the database and a file on GitHub.

    Args:
    request (HttpRequest): The HTTP request object.

    Returns:
    HttpResponse: The HTTP response object containing the rendered template and/or a JSON response.

    Raises:
    Exception: An exception is raised if there is an error fetching conference information or communicating with GitHub.
    # noqa
    """
    if request.method == "POST":
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            url = request.body.decode("UTF-8")
            if url != "":
                try:
                    response = get_conference_information(url)
                except Exception as ex:
                    messages.error(
                        request,
                        f"We are experiencing some problems when fetching"
                        f"when communication with {url}. "
                        "Please Try again later.",
                    )

                    return redirect("submit_conference")

                return JsonResponse(
                    response,
                    status=200,
                    safe=False,
                )
            else:
                response = {
                    "title": "",
                    "dates": [["", ""]],
                    "places": "",
                }
                return JsonResponse(
                    response,
                    status=200,
                    safe=False,
                )

        form = ConferenceForm(request.POST)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError as integrity:
                print(f"Exeception: {integrity}")
                messages.error(
                    request,
                    "Integrity error. Check the information submitted,"
                    " it could be redundant or missing some fields.",
                )
                return redirect("submit_conference")

            except ValueError as value_error:
                print(value_error)
                messages.error(request, value_error)
                return redirect("submit_conference")

            except Exception as ex:
                print(ex)
                messages.error(
                    request,
                    "Please check the submitted information.",
                )
                return redirect("submit_conference")

            conferences = Conference.objects.order_by("start_date")

            current_path = os.getcwd()

            load_dotenv()
            filepath = current_path + f"/conference_calendar/input.csv"

            relative_path_list = ["input.csv"]

            project_name = "conference_calendar"
            repo = "conference_calendar"
            folder_name = ""
            env_name = os.getenv("ENV_NAME")

            save_new_conference_data(conferences, filepath)

            try:
                if env_name == "prod":
                    update_repo_and_push(
                        folder_name, relative_path_list, project_name, repo
                    )
                else:
                    print("Run quarto preview command to check the local changes·")

            except Exception as ex:
                print(ex)
                messages.error(
                    request,
                    "We are experiencing some problems when fetching when "
                    "communication with github. Please Try again later.",
                )
                return redirect("submit_conference")

            context = {
                "form": form,
                "repo": "conference_calendar",
            }

            return render(
                request,
                "repository/submission.html",
                context,
            )
        messages.error(
            request,
            "Please review your submission. Form seems to be invalid.",
        )
        return redirect("submit_conference")
    form = ConferenceForm()

    context = {"form": form}

    return render(
        request,
        "repository/submit_conference.html",
        context=context,
    )


@login_required
def submit_session(request):
    """
    Handle the submission of a session form.

    This view function handles the submission of a session form through
    an HTTP POST request.If the request method is POST and the submitted
    form is valid, it saves the form data. Regardless of the request
    method, it renders the session submission page with an empty form
    for GET requests.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A rendered HTML response containing the session
        submission form.

    Example Usage:
        To use this view, include it in your Django URL configuration
        and map it to a URL pattern.
        For example:
        ```
        path('submit_session/', views.submit_session, name='submit_session'),
        ```
    #noqa
    """
    if request.method == "POST":
        form = SessionForm(request.POST)
        if form.is_valid():
            try:
                print(form.cleaned_data)
                form.save()

            except IntegrityError as integrity:
                print(f"Exeception: {integrity}")
                messages.error(
                    request,
                    "Integrity error. Check the information submitted,"
                    " it could be redundant or missing some fields.",
                )
                return redirect("submit_session")

            except ValueError as value_error:
                print(value_error)
                messages.error(request, value_error)
                return redirect("submit_session")

            except Exception as ex:
                print(ex)
                messages.error(
                    request,
                    "Please check the submitted information.",
                )
                return redirect("submit_session")
            
            messages.success(
                request,
                "Session successfully submited!",
            )
            return redirect("submit_session")

        print(f"form errors: {form.errors.as_data()}")
        messages.error(
            request,
            "Please review your submission. Form seems to be invalid.",
        )
        return redirect("submit_session")

    form = SessionForm()
    context = {"form": form}
    return render(
        request,
        "repository/submit_session.html",
        context=context,
    )


@login_required
def help_page(request):
    """
    Render the help page.

    This view function renders the help page of the application, which provides
    information and assistance to users.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse:
        A rendered HTML response containing the help page content.

    Example Usage:
        To use this view, include it in your Django URL configuration
        and map it to a URL pattern.
        For example:
        ```
        path('help/', views.help_page, name='help_page'),
        ```
    """
    context = {}
    return render(
        request,
        "repository/help.html",
        context=context,
    )


@login_required
def user_profile(request, username):
    """
    View function for displaying a user's profile.

    This function is decorated with @login_required to ensure that only authenticated users can access it.
    It retrieves the user and author objects associated with the given username and renders a profile page
    with the user's information.

    Args:
        request (HttpRequest): The HTTP request object.
        username (str): The username of the user whose profile is being viewed.

    Returns:
        HttpResponse: A response object that displays the user's profile page.

    Raises:
        User.DoesNotExist: If the specified user does not exist in the database.
        Author.DoesNotExist: If the author associated with the user does not exist in the database.
    """
    user = User.objects.get(username=username)
    author = Author.objects.get(member=user)

    context = {"user": user, "author": author}

    return render(
        request,
        "repository/profile.html",
        context=context,
    )


@login_required
def edit_profile(request, pk):
    """
    View function for editing a user's profile.

    This function is decorated with @login_required to ensure that only authenticated users can access it.
    It allows a user to edit their profile information, including first name, last name, and short bio.
    When the form is submitted, it updates the user and author objects in the database accordingly.

    Args:
        request (HttpRequest): The HTTP request object.
        pk (int): The primary key of the user whose profile is being edited.

    Returns:
        HttpResponse: A response object that renders the profile editing page or redirects to the user's profile page upon successful update.

    Raises:
        User.DoesNotExist: If the specified user does not exist in the database.
        Author.DoesNotExist: If the author associated with the user does not exist in the database.
    """
    user = User.objects.get(id=int(pk))
    form = UpdateUserForm(instance=user)

    author = Author.objects.get(member=user)

    if request.method == "POST":
        form = UpdateUserForm(request.POST, instance=user)
        if form.is_valid():
            if form.cleaned_data["first_name"]:
                User.objects.filter(pk=pk).update(
                    first_name=form.cleaned_data["first_name"]
                )
            if form.cleaned_data["last_name"]:
                User.objects.filter(pk=pk).update(
                    last_name=form.cleaned_data["last_name"]
                )
            if form.cleaned_data["short_bio"]:
                Author.objects.filter(pk=author.pk).update(
                    bio=form.cleaned_data.get("short_bio")
                )
            return redirect(f"/profile/{pk}/")
        print("form not valid")
        print(form.errors.as_data())

    context = {"form": form}

    return render(
        request,
        "repository/update_profile.html",
        context,
    )
