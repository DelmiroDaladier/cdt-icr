import os
import yaml
from datetime import datetime

from .models import Newsletter

from bs4 import BeautifulSoup


def create_qmd_file(filepath: str):
    """
    Create a new QuickMark data file at the specified filepath.

    If a file already exists at the filepath, it will be deleted before creating the new file.

    The file will contain a YAML header with metadata about the file, including the title, page
    layout, title block banner, and comments. The metadata will be formatted according to the
    QuickMark data file specification.

    Args:
        filepath (str): The path and filename for the new QuickMark data file.

    Raises:
        OSError: If an error occurs while deleting the existing file, or while creating the new file.

    Returns:
        None
    """
    if os.path.exists(filepath):
        os.remove(filepath)

    header = {
        "title": "Interactive AI CDT Newsletter",
        "page-layout": "full",
        "title-block-banner": True,
        "comments": False,
    }

    with open(filepath, "w+") as fp:
        fp.write("---\n")
        yaml.dump(header, fp)
        fp.write("\n---")


def generate_page_content(filepath: str, content: dict):
    """
    Generate page content for a newsletter and write it to a file at the specified path.

    Args:
        filepath (str): The path to the file where the page content will be written.
        content (dict): A dictionary containing the content to be included in the page.

    Returns:
        None

    Raises:
        TypeError: If filepath is not a string or content is not a dictionary.

    """
    title = "CDT Newsletter"
    text = ""

    with open(filepath, "a") as fp:
        text += "\n# Posts \n"

        for post in content["posts"]:
            text += f"\n### [{post.get('title', '')}](https://delmirodaladier.github.io/icr/content/{post.get('slug', '')})\n"
            text += f"\n{post.get('overview', '')}\n"

        text += "\n# Conferences \n"

        for conference in content["conferences"]:
            text += f"\n### [{conference.get('name', '')}]({conference.get('link', '')})\n"
            text += f"\n- Location:{conference.get('location', '')}\n"
            text += f"\n- Start date:{conference.get('start_date', '')}\n"
            text += f"\n- End date:{conference.get('end_date', '')}\n"

        fp.write(text)

    data_dict = {"title": title, "text": text, "sent": True}

    object = Newsletter(**data_dict)
    object.save()


def generate_newsletter_body(form_data: dict, forthcoming_events):
    newsletter_body = ""
    newsletter_items = [item for item in form_data["announcements"]]
    events = [item for item in forthcoming_events]

    if not form_data.get("title", ""):
        newsletter_body += "<h2>CDT Weekly Newsletter</h2>"
    else:
        newsletter_body = f"<h2>{form_data.get('title')}</h2><br>"

    newsletter_body += "<ul>"

    for item in newsletter_items:
        newsletter_body += f"<li>{item.title}</li>"

    newsletter_body += "</ul>"

    if not form_data.get("text", ""):
        newsletter_body += f""
    else:
        newsletter_body += f"<p>{form_data.get('text', '')}</p><br><br>"

    for announcement in newsletter_items:
        newsletter_body += f"<b>{announcement.title}</b><br>"
        newsletter_body += f"{announcement.text}<br><br>"

    newsletter_body += "<h2>Forthcoming Calendar of Events<br><br></h2>"

    for event in events:
        newsletter_body += f"<b>{event.title} - {event.date}</b><br>"

    return newsletter_body


def parse_html_to_text(newsletter_body: str):
    newsletter_body = newsletter_body.replace("<br>", "\n")

    soup = BeautifulSoup(newsletter_body, "html.parser")

    return soup.text
