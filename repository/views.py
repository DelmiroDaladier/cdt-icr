import os
import yaml
import json
import requests
import urllib3

from .models import Post
from dotenv import load_dotenv
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth import login
from django.template.defaultfilters import slugify
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Conference
from .forms import PostForm, AuthorForm, VenueForm, CategoryForm, ArxivForm, NewUserForm, ConferenceForm
from .utils import generate_qmd_header, generate_page_content, create_push_request, generate_qmd_header_for_arxiv, scrap_data_from_arxiv, get_conference_information, save_new_conference_data


@login_required
def homepage(request):

    load_dotenv()

    if request.method == 'POST':
        filled_form = PostForm(request.POST)

        if filled_form.is_valid():
            filled_form.save()
            form_data = filled_form.cleaned_data

            content = {}
            content = generate_qmd_header(content, form_data)

            folder_name = slugify(content.get('title', ''))

            current_path = os.getcwd()

            current_path = current_path + \
                f'/icr_frontend/content/{folder_name}/'

            file_path = f'{current_path}index.qmd'

            if not os.path.exists(current_path):
                os.makedirs(current_path)

            with open(file_path, 'w+') as fp:
                fp.write('---\n')
                yaml.dump(content, fp)
                fp.write('\n---')

            generate_page_content(content, file_path)

            repo = 'icr'

            try:
                create_push_request(file_path, folder_name, repo)
            except Exception as ex:
                messages.error(
                    request,
                    "We are experiencing some problems when fetching when communication with github. Please Try again later.")
                return redirect("")

            context = {
                'folder_name': folder_name,
                'form': filled_form
            }

            print(context)
        else:
            messages.error(request, filled_form.errors.as_data().title)

        return render(request, 'repository/submission.html', context)
    else:
        filled_form = PostForm()
        return render(
            request,
            'repository/new_post.html',
            context={
                'form': filled_form})


def about(request):
    return render(request, 'repository/about_page.html')


def author_create(request):

    if request.method == 'GET':
        form = AuthorForm()
        context = {'form': form}
        return render(
            request,
            'repository/create_author.html',
            context=context)

    form = AuthorForm(request.POST)

    if form.is_valid():
        author_instance = form.save()
        instance = serializers.serialize('json', [author_instance, ])
        return JsonResponse({"instance": instance}, status=200)
    else:
        messages.error(request, form.errors.as_data().title)


def add_venue(request):

    if request.method == 'GET':
        form = VenueForm()
        context = {'form': form}
        return render(request, 'repository/add_venue.html', context=context)

    form = VenueForm(request.POST)

    if form.is_valid():
        venue_instance = form.save()
        instance = serializers.serialize('json', [venue_instance, ])
        return JsonResponse({"instance": instance}, status=200)
    else:
        messages.error(request, form.errors.as_data().title)


def add_category(request):

    if request.method == 'GET':
        form = CategoryForm()
        context = {'form': form}
        return render(request, 'repository/add_category.html', context=context)

    form = CategoryForm(request.POST)
    if form.is_valid():
        category_instance = form.save()
        instance = serializers.serialize('json', [category_instance, ])
        return JsonResponse({"instance": instance}, status=200)
    else:
        messages.error(request, form.errors.as_data().title)


def update_post(request, slug):

    context = {}

    post = get_object_or_404(Post, slug=slug)

    form = PostForm(request.POST or None, instance=post)

    if request.method == 'GET':
        context = {'form': form}
        return render(request, "repository/update_post.html", context=context)

    if form.is_valid():
        post_instance = Post.objects.get(slug=slug)
        form = PostForm(request.POST, instance=post)
        form.save()
        instance = serializers.serialize('json', [post_instance, ])
        return JsonResponse({"instance": instance}, status=200)
    else:
        messages.error(request, form.errors.as_data().title)


def arxiv_post(request):

    load_dotenv()

    if request.method == 'POST':
        context = {}

        enviroment_name = os.getenv('ENV_NAME')
        filled_form = ArxivForm(request.POST)

        if filled_form.is_valid():
            # filled_form.save()
            form_data = filled_form.cleaned_data

            url = form_data.get('link', '')

            try:
                data = scrap_data_from_arxiv(url)
            except Exception as ex:
                messages.error(
                    request,
                    "We are experiencing some problems when fetching information from Arxiv. Please Try again later.")
                return redirect("arxiv_post")

            content = generate_qmd_header_for_arxiv(data)

            folder_name = slugify(content.get('title', ''))

            current_path = os.getcwd()

            current_path = current_path + \
                f'/icr_frontend/content/{folder_name}/'
            file_path = f'{current_path}index.qmd'

            if not os.path.exists(current_path):
                os.makedirs(current_path)

            with open(file_path, 'w+') as fp:
                fp.write('---\n')
                yaml.dump(content, fp)
                fp.write('\n---')

            generate_page_content(content, file_path)

            try:
                repo = 'icr'
                create_push_request(file_path, folder_name, repo=repo)
            except Exception as ex:
                messages.error(
                    request,
                    "We are experiencing some problems when fetching when communication with github. Please Try again later.")
                return redirect("arxiv_post")

            context = {
                'folder_name': folder_name,
                'form': filled_form
            }

            return render(
                request,
                'repository/submission.html',
                context=context)

        messages.error(request, filled_form.errors.as_data().title)

    form = ArxivForm()
    context = {
        'form': form
    }
    return render(request, 'repository/arxiv_post.html', context=context)


def email_check(user):
    if user.is_authenticated:
        return user.email.endswith('@bristol.ac.uk')
    print('Fudeu')
    return False


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            email = form_data['email']

            if email.endswith('@bristol.ac.uk'):
                user = form.save()
                login(request, user)
                messages.success(request, "Registration successfull.")
                return redirect("homepage")
            messages.error(
                request, "Email should belong to @bristol.ac.uk domain.")
            return render(
                request,
                'registration/register.html',
                context={
                    "register_form": form,
                    "message": "Email should belong to @bristol.ac.uk domain."})

        messages.error(
            request,
            "Uncessfull registration. Invalid information.")

    form = NewUserForm()
    return render(
        request,
        'registration/register.html',
        context={
            "register_form": form})


@login_required
def submit_conference(request):

    if request.method == 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            url = request.body.decode('UTF-8')
            if url != '':
                response = get_conference_information(url)

                return JsonResponse(response, status=200, safe=False)
            else:
                response = {
                    'title': '',
                    'dates': [['', '']],
                    'places': '',

                }
                return JsonResponse(response, status=200, safe=False)

        form = ConferenceForm(request.POST)

        if form.is_valid():
            form.save()

            conferences = Conference.objects.order_by('start_date')

            current_path = os.getcwd()

            filepath = current_path + f'/conference_calendar/input.csv'

            save_new_conference_data(conferences, filepath)

            repo = 'conference_calendar'
            print('Ready to make a push request')
            create_push_request(file_path=filepath, folder_name='', repo=repo)

    form = ConferenceForm()

    context = {
        "form": form
    }

    return render(
        request,
        'repository/submit_conference.html',
        context=context
    )
