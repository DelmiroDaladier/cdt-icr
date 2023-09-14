import os
import yaml

from django.shortcuts import render, redirect
from django.template.defaultfilters import slugify
from django.contrib.auth.decorators import login_required

from dotenv import load_dotenv
from .forms import BlogPostForm
from .utils import (
    generate_qmd_header,
    generate_page_content,
    create_push_request,
)


@login_required
def blog_homepage(request):
    load_dotenv()
    print(request.user)

    if request.method == "POST":
        filled_form = BlogPostForm(request.POST)

        enviroment_name = os.getenv("ENV_NAME")

        if filled_form.is_valid():
            form_data = filled_form.cleaned_data

            content = {}
            content = generate_qmd_header(content, form_data)

            folder_name = slugify(content.get("title", ""))

            current_path = os.getcwd()
            
            current_path = current_path + f"/icr_frontend/posts/{folder_name}/"

            file_path = f"{current_path}index.qmd"

            if not os.path.exists(current_path):
                os.makedirs(current_path)

            with open(file_path, "w+") as fp:
                fp.write("---\n")
                yaml.dump(content, fp)
                fp.write("\n---")

            generate_page_content(content, file_path)
            create_push_request(file_path, folder_name)

            context = {"form": filled_form, "folder_name": folder_name}

        return render(request, "blog/submission.html", context=context)

    else:
        filled_form = BlogPostForm()
        return render(
            request, "blog/new_blogpost.html", context={"form": filled_form}
        )
