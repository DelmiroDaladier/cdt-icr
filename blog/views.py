import os
import yaml
from django.core import serializers
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.defaultfilters import slugify
from django.contrib.auth.decorators import login_required

from .models import BlogPost
from dotenv import load_dotenv
from repository.models import Author, ResearchArea
from repository.forms import ResearchAreaForm
from repository.utils import update_repo_and_push
from .forms import BlogPostForm
from .utils import (
    generate_qmd_header,
    generate_page_content,
    create_push_request,
)


@login_required
def blog_homepage(request):
    load_dotenv()

    post_author = Author.objects.filter(member=request.user)

    if request.method == "POST":
        filled_form = BlogPostForm(request.POST)

        env_name = os.getenv("ENV_NAME")

        if filled_form.is_valid():
            form_data = filled_form.cleaned_data

            form_data['authors'] = post_author
            
            obj, created = ResearchArea.objects.get_or_create(title="blog post", slug='blog-post')
            form_data['categories'] = [obj]
            

            content = {}
            content = generate_qmd_header(content, form_data)

            folder_name = slugify(content.get("title", ""))

            current_path = os.getcwd()
            
            current_path = current_path + f"/icr_frontend/posts/{folder_name}/"

            file_path = f"{current_path}index.qmd"
            
            BlogPost.objects.create(**{
                'name': form_data['name'],
                'text': form_data['text']
            })

            if not os.path.exists(current_path):
                os.makedirs(current_path)

            with open(file_path, "w+") as fp:
                fp.write("---\n")
                yaml.dump(content, fp)
                fp.write("\n---")

            generate_page_content(content, file_path)

            relative_paths_list = [
                f"posts/{folder_name}/index.qmd"
            ]

            project_name = 'icr_frontend'
            repo = 'icr'

            if env_name == 'prod':
                update_repo_and_push(folder_name, relative_paths_list, project_name, repo)
            else:
                print('Run quarto preview command to check the local changes.')

            context = {"form": filled_form, "folder_name": folder_name}
        else:
            print(filled_form.errors)    

        return render(request, "blog/submission.html", context=context)

    else:
        filled_form = BlogPostForm()
        return render(
            request, "blog/new_blogpost.html", context={"form": filled_form}
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
        return JsonResponse(
            {"instance": instance}, status=200
        )
    else:
        messages.error(
            request,
            "The category is invalid,"
            " please review your submission.",
        )
        return render(
            request,
            "repository/add_category.html",
            context={},
        )