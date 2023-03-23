import os
from datetime import datetime

from django.conf import settings
import requests
import json
import random

from cdt_newsletter.utils import generate_page_content, create_qmd_file
from repository.utils import create_push_request
from repository.models import Post, Conference
from cdt_newsletter.models import Newsletter

def schedule_api():
    newsletter_objects = Newsletter.objects.all()
    latest_newsletter = newsletter_objects.latest('modified_at')

    latest_date = latest_newsletter.modified_at

    posts = Post.objects.filter(updated_at__range=(latest_date, datetime.now()))
    posts = list(posts.values())

    conferences = Conference.objects.filter(updated_at__range=(latest_date, datetime.now()))
    conferences = list(conferences.values())

    content = {
        'posts': posts,
        'conferences': conferences
    }

    current_path = os.getcwd()
    filepath = current_path + \
                        f'/newsletter_frontend/index.qmd'

    create_qmd_file(filepath)
    
    generate_page_content(filepath, content)

    repo = 'newsletter_frontend'
    path = 'index.qmd'
    print('creating push request')
    create_push_request(file_path=filepath, folder_name='', repo=repo, path=path)