import os
from datetime import datetime

from django.conf import settings
import requests
import json
import random

from cdt_newsletter.utils import generate_page_content, create_qmd_file
from repository.utils import create_push_request
from repository.models import Publication, Conference
from cdt_newsletter.models import Newsletter


def schedule_api():
    """
    Retrieve the latest newsletter and filter posts and conferences updated since then.
    Generate a QMD file with the filtered content and create a push request for it.

    Returns:
        None
    """
    newsletter_objects = Newsletter.objects.all()
    latest_newsletter = newsletter_objects.latest("modified_at")

    latest_date = latest_newsletter.modified_at

    posts = Publication.objects.filter(
        updated_at__range=(latest_date, datetime.now())
    )
    posts = list(posts.values())

    conferences = Conference.objects.filter(
        updated_at__range=(latest_date, datetime.now())
    )
    conferences = list(conferences.values())

    content = {"posts": posts, "conferences": conferences}

    current_path = os.getcwd()
    filepath = current_path + f"/newsletter_frontend/index.qmd"

    create_qmd_file(filepath)

    generate_page_content(filepath, content)

    repo = "newsletter_frontend"
    path = "index.qmd"
    print("creating push request")
    create_push_request(
        file_path=filepath, folder_name="", repo=repo, path=path
    )
