import os
import yaml
from datetime import datetime
from dotenv import load_dotenv

from .models import Newsletter

from bs4 import BeautifulSoup

from repository.utils import update_repo_and_push, git_pull


def create_qmd_file(filepath: str):
    """
    Create a new QuickMark data file at the specified filepath.

    If a file already exists at the filepath,
    it will be deleted before creating the new file.

    The file will contain a YAML header with metadata
    about the file, including the title, page
    layout, title block banner, and comments.
    The metadata will be formatted according to the
    QuickMark data file specification.

    Args:
        filepath (str): The path and filename
        for the new QuickMark data file.

    Raises:
        OSError: If an error occurs while
        deleting the existing file, or while creating the new file.

    Returns:
        None
    #noqa
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
    Generate page content for a newsletter and write
    it to a file at the specified path.

    Args:
        filepath (str): The path to the file where
        the page content will be written.
        content (dict): A dictionary containing
        the content to be included in the page.

    Returns:
        None

    Raises:
        TypeError: If filepath is not a string or content is not a dictionary.
    #noqa
    """
    title = "CDT Newsletter"
    text = ""

    with open(filepath, "a") as fp:
        text += "\n# Posts \n"

        for post in content["posts"]:
            text += f"\n### [{post.get('title', '')}](https://delmirodaladier.github.io/icr/content/{post.get('slug', '')})\n"  # noqa
            text += f"\n{post.get('overview', '')}\n"

        text += "\n# Conferences \n"

        for conference in content["conferences"]:
            text += f"\n### [{conference.get('name', '')}]({conference.get('link', '')})\n"  # noqa
            text += f"\n- Location:{conference.get('location', '')}\n"
            text += f"\n- Start date:{conference.get('start_date', '')}\n"
            text += f"\n- End date:{conference.get('end_date', '')}\n"

        fp.write(text)

    data_dict = {
        "title": title,
        "text": text,
        "sent": True,
    }

    object = Newsletter(**data_dict)
    object.save()


def generate_newsletter_body(form_data: dict, forthcoming_events):
    """
    Generate the content for a newsletter.

    This function takes a dictionary of form data and a list of forthcoming events and generates the content
    for a newsletter. It includes a title, announcements, a newsletter text, and a calendar of forthcoming events.

    Args:
        form_data (dict): A dictionary containing form data, including the newsletter title, announcements, and text.
        forthcoming_events (QuerySet): A queryset containing forthcoming events.

    Returns:
        str: The generated content for the newsletter in HTML format.

    Raises:
        None.
    """
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

    newsletter_body += "<h2>Forthcoming Calendar of Events</h2><br><br>"

    for event in events:
        newsletter_body += f"<b>{event.title} - {event.date}</b><br>"

    return newsletter_body


def parse_html_to_text(newsletter_body: str):
    """
    Parse HTML content to plain text.

    This function takes HTML content as input, removes HTML tags, and converts it to plain text.

    Args:
        newsletter_body (str): HTML content to be parsed.

    Returns:
        str: The plain text extracted from the HTML content.

    Raises:
        None.
    """
    newsletter_body = newsletter_body.replace("<br>", "\n")

    soup = BeautifulSoup(newsletter_body, "html.parser")

    return soup.text


def create_newsletter_file_and_push(
    folder_name: str,
    relative_path_list: str,
    project_name: str,
    repo: str,
    newsletter_body: str,
    today_str,
):
    """
    Create a newsletter file, save it, and push changes to a repository.

    This function creates a newsletter file with the provided content, saves it to the specified folder, and
    pushes changes to a version control repository.

    Args:
        folder_name (str): The name of the folder where the newsletter file should be saved.
        relative_path_list (list): A list of relative file paths for the newsletter files.
        project_name (str): The name of the project where the newsletter file should be saved.
        repo (str): The name of the repository to push changes to.
        newsletter_body (str): The content of the newsletter in HTML format.
        today_str (str): The formatted date string for the newsletter issue.

    Returns:
        None.

    Raises:
        None.
    """
    load_dotenv()
    git_pull('newsletter_frontend')
    print(relative_path_list)
    file_list = [os.getcwd() + f"/{project_name}/newsletter_issues/{path}" for path in relative_path_list]

    content = {
        "title": f"Newsletter Issue - {today_str}",
        "execute": {"echo": False},
        "format": {"html": {"df-print": "paged", "toc": True}},
    }

    for file in file_list:
        print(f"File:{file}")
        folder_path = (
            os.getcwd()
            + f"/{project_name}/newsletter_issues/{folder_name.replace(' ', '_')}"
        )
        print(f"Folder path:{folder_path}")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        with open(file, "w+") as fp:
            fp.write("---\n")
            yaml.dump(content, fp)
            fp.write("\n---\n")
            fp.write(newsletter_body)

    env_name = os.getenv("ENV_NAME")

    relative_path_list = ['newsletter_issues/'+path for path in relative_path_list]

    if env_name == "prod":
        update_repo_and_push(folder_name, relative_path_list, project_name, repo)
    else:
        print(
            "Please run the command quarto preview in the icr_frontend folder."
        )
