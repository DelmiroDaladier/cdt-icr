import os
import re
import json
import yaml
import requests
import subprocess
from dateutil.parser import parse
from collections import defaultdict
from urllib3.util.retry import Retry
from requests.adapters import (
    HTTPAdapter,
)
from django.template.defaultfilters import (
    slugify,
)

import spacy
import pandas as pd
import en_core_web_sm
from spacy import displacy
from bs4 import BeautifulSoup
from dotenv import load_dotenv


def generate_qmd_header(content: dict, form_data: dict):
    """Generate a Quick Markup Description header based on form data.

    Args:
        content (dict): The content of the QMD header to be generated. It should
            have the following keys:
            - 'title' (str): the title of the content.
            - 'description' (str): the description of the content.
            - 'image' (str): the URL of the thumbnail image of the content.
            - 'categories' (list): a list of strings representing the categories
              of the content.
            - 'format' (dict): a dictionary specifying the format of the content.
              It should have the following keys:
              - 'html' (dict): a dictionary specifying the HTML format of the content.
                It should have the following keys:
                - 'df-print' (str): the format of the printed version of the content.
                - 'toc' (bool): whether to include a table of contents in the content.

        form_data (dict): The form data used to generate the QMD header. It should have
            the following keys:
            - 'title' (str): the title of the content.
            - 'overview' (str): the overview of the content.
            - 'thumbnail' (str): the URL of the thumbnail image of the content.
            - 'categories' (list): a list of Category objects representing the categories
              of the content.
            - 'authors' (list): a list of Author objects representing the authors of the content.
            - 'citation' (str): the URL of the citation of the content.
            - 'pdf' (str): the URL of the PDF version of the content.
            - 'poster' (str): the URL of the poster of the content.
            - 'code' (str): the URL of the source code of the content.
            - 'supplement' (str): the URL of the supplementary material of the content.
            - 'slides' (str): the URL of the slides of the content.

    Returns:
        dict: The QMD header generated based on the form data. It has the same structure
        as the `content` parameter.
    # noqa
    """

    if form_data["thumbnail"] is None:
        form_data[
            "thumbnail"
        ] = "https://upload.wikimedia.org/wikipedia/commons/5/59/Empty.png"

    param_keys = [
        "overview",
        "citation",
        "pdf_url",
        "poster_url",
        "code_url",
        "supplement_url",
        "slides_url",
        "research_area",
    ]

    content = {
        "title": form_data.get("name", ""),
        "description": form_data.get("overview", ""),
        "image": form_data.get(
            "thumbnail",
            "https://upload.wikimedia.org/wikipedia/commons/5/59/Empty.png",
        ),
        "categories": [category.title for category in form_data["research_area"]],
        "format": {
            "html": {
                "df-print": "paged",
                "toc": True,
            }
        },
        "execute": {"echo": False},
    }

    content["params"] = {}

    for param_key in param_keys:
        key = form_data.get(param_key, "")
        print(f"Param key:{param_key}")
        print(f"key:{type(key)}")

        if key != "":
            if isinstance(key, str):
                content["params"][param_key] = key
            else:
                content["params"][param_key] = key[0].title

    for idx, author in enumerate(form_data["authors"], 1):
        content["params"][f"author_{idx}"] = {
            "name": author.user_name,
            "url": author.user_url,
        }

    return content


def save_publication_data(
    publication_title: str,
    authors: str,
    links: str,
    research_area: str,
    filepath: str,
):
    data = {
        "publication": publication_title,
        "authors": authors,
        "publication_url": "content/" + slugify(publication_title),
        "authors_link": links,
        "research_area": research_area,
    }

    if not os.path.exists(filepath):
        df = pd.DataFrame(
            columns=[
                "publication",
                "authors",
                "publication_url",
                "authors_link",
                "research_area",
            ]
        )
        df.to_csv(filepath, index=False)

    df = pd.read_csv(filepath)
    df = df.append(data, ignore_index=True)
    df.drop_duplicates(
        subset=[
            "publication",
            "authors",
        ],
        inplace=True,
    )
    df.to_csv(filepath, index=False)


def save_new_conference_data(conference_objects, filepath: str):
    """Save a dictionary of conference objects to a CSV file.

    The conference objects are converted to a pandas DataFrame and saved to the specified
    file path. If the file already exists, it will be deleted first.

    Args:
        conference_objects (dict): A dictionary where the keys are conference IDs and the
            values are dictionaries representing conference objects. Each dictionary should
            have the following keys:
            - 'name' (str): the name of the conference.
            - 'start_date' (str): the start date of the conference in 'YYYY-MM-DD' format.
            - 'end_date' (str): the end date of the conference in 'YYYY-MM-DD' format.
            - 'location' (str): the location of the conference.
            - 'url' (str): the URL of the conference website.

        filepath (str): The file path of the CSV file to be saved.

    Returns:
        None. The function does not return anything, but saves the data to the specified file path.
    # noqa
    """
    if os.path.exists(filepath):
        os.remove(filepath)

    df = pd.DataFrame(list(conference_objects.values()))
    if "id" in df.columns:
        df.drop("id", axis=1)

    df.to_csv(filepath, index=False)


def generate_page_content(
    content: dict,
    filepath: str,
    arxiv: bool,
):
    """Generate a markdown file with the content of a conference paper.

    This function generates a markdown file with the content of a conference paper based
    on the specified content dictionary. The file is saved to the specified file path.

    Args:
        content (dict): A dictionary containing the content of a conference paper. The dictionary
            should have the following keys:
            - 'params' (dict): A dictionary containing the parameters of the paper, such as
              the overview, citation URL, PDF URL, etc.
            - 'title' (str): The title of the paper.
            - 'description' (str): A brief description of the paper.
            - 'image' (str): The URL of an image representing the paper.
            - 'categories' (list): A list of categories for the paper.
            - 'format' (dict): A dictionary specifying the format of the paper.

        filepath (str): The file path of the markdown file to be generated.

    Returns:
        None. The function does not return anything, but generates the markdown file at
        the specified file path.
    # noqa
    """

    with open(filepath, "a") as fp:
        authors = [
            '"' + content["params"][param].get("name") + '"'
            for param in content["params"]
            if param.startswith("author")
        ]
        links = []
        if content["params"]["author_1"].get("link", None):
            links = [
                '"' + content["params"][param].get("link", None) + '"'
                for param in content["params"]
                if param.startswith("author")
            ]

        if arxiv:
            aux = []
            for author in authors:
                author_list = author.replace('"', "").split(",")
                aux.append(
                    '"' + " ".join(author_list[-1:] + author_list[:-1]).strip() + '"'
                )
            authors = aux

        authors_string = ",".join(authors)
        links_string = ",".join(links)

        if len(links) == 0:
            links_string = "NONE"

        fp.write("\n```{ojs} \n")
        fp.write(f"\n names = [{authors_string}] \n")
        fp.write("\n``` \n")

        fp.write("\n## Tldr \n")
        overview = content["params"]["overview"]
        fp.write(f"{overview}\n")
        fp.write("\n## Paper-authors\n")

        fp.write("\n```{ojs} \n")
        fp.write(
            '\n html`<ul>${names.map(name => html`<li><a href="../../'
            'posts_by_author.html?name=${name}" >${name}</a></li>`)}</ul>` \n'
        )
        fp.write("\n``` \n")

        fp.write("\n```{ojs} \n")
        fp.write('\n htl = require("htl@0.2") \n')
        fp.write("\n``` \n")

        fp.write("\n```{ojs} \n")
        fp.write("\n html = htl.html \n")
        fp.write("\n``` \n")

        fp.write("\n## More Resources\n")

        if "citation" in content["params"]:
            fp.write(
                "[![](https://img.shields.io/badge/"
                "citation-scholar-9cf?style=flat.svg)]"
                "({{< meta params.citation >}})\n"
            )

        if "pdf_url" in content["params"].keys():
            fp.write(
                "[![](https://img.shields.io/badge"
                "/PDF-green?style=flat)]({{< meta params.pdf_url >}})\n"
            )
        if "supplement_url" in content["params"].keys():
            fp.write(
                "[![](https://img.shields.io/badge/supplement"
                "-yellowgreen?style=flat)]"
                "({{< meta params.supplement_url >}})\n"
            )
        if "slides_url" in content["params"].keys():
            fp.write(
                "[![](https://img.shields.io/badge/blog-"
                "blue?style=flat)]"
                "({{< meta params.slides_url >}}\n"
            )
        if "poster_url" in content["params"].keys():
            fp.write(
                "[![](https://img.shields.io/badge/poster"
                "-yellow?style=flat)]"
                "({{< meta params.poster_url >}})\n"
            )
        if "code_url" in content["params"].keys():
            fp.write(
                "[![](https://img.shields.io/badge/code-"
                "blueviolet?style=flat)]({{< meta params.code_url >}})\n"
            )

        current_path = os.getcwd()

        filepath = f"{current_path}/icr_frontend/input.csv"
        authors_string = authors_string.replace('"', "")
        links_string = links_string.replace('"', "")

        save_publication_data(
            content["title"],
            authors_string,
            links_string,
            content["params"]["research_area"],
            filepath,
        )


def create_push_request(
    file_path: str,
    folder_name: str,
    repo: str,
    path: str,
):
    """
    Creates and pushes a new file with the content of a given file path to the specified GitHub repository.

    Args:
        file_path (str): The path of the file to be uploaded.
        folder_name (str): The name of the folder where the file will be stored.
        repo (str): The name of the GitHub repository.

    Returns:
        None
    # noqa
    """
    load_dotenv()

    user = os.getenv("GH_USER")
    auth_token = os.getenv("GH_TOKEN")

    header = {"Authorization": "Bearer " + auth_token}

    sha_last_commit_url = f"https://api.github.com/repos/{user}/{repo}/branches/main"
    response = requests.get(
        sha_last_commit_url,
        headers=header,
    )

    sha_last_commit = response.json()["commit"]["sha"]

    url = (
        f"https://api.github.com/repos/" f"{user}/{repo}/git/commits/{sha_last_commit}"
    )
    response = requests.get(url, headers=header)

    sha_base_tree = response.json()["sha"]

    with open(file_path, "r") as fp:
        content = fp.read()

    data = {
        "content": content,
        "encoding": "utf-8",
    }

    header = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + auth_token,
    }

    url = f"https://api.github.com/repos/DelmiroDaladier/{repo}/git/blobs"
    response = requests.post(
        url,
        json.dumps(data),
        headers=header,
    )

    blob_sha = response.json()["sha"]

    current_directory = os.getcwd()
    input_absolute_path = current_directory + f"/icr_frontend/input.csv"
    input_relative_path = "input.csv"

    print(current_directory)
    print(input_absolute_path)
    print(input_relative_path)

    with open(input_absolute_path, "r") as fp:
        content = fp.read()

    data = {"content": content, "encoding": "utf-8"}

    url = f"https://api.github.com/repos/DelmiroDaladier/{repo}/git/blobs"
    response = requests.post(
        url,
        json.dumps(data),
        headers=header,
    )

    blob_sha_input_csv = response.json()["sha"]

    data = {
        "base_tree": sha_base_tree,
        "tree": [
            {
                "path": path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            },
            {
                "path": input_relative_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha_input_csv,
            },
        ],
    }

    url = f"https://api.github.com/repos/Delmirodaladier/{repo}/git/trees"
    response = requests.post(
        url,
        json.dumps(data),
        headers=header,
    )

    tree_sha = response.json()["sha"]

    data = {
        "message": f"Add new files at content/{folder_name}",
        "author": {
            "name": "Delmiro Daladier",
            "email": "daladiersampaio@gmail.com",
        },
        "parents": [sha_last_commit],
        "tree": tree_sha,
    }

    url = f"https://api.github.com/repos/" f"DelmiroDaladier/{repo}/git/commits"
    response = requests.post(
        url,
        json.dumps(data),
        headers=header,
    )
    new_commit_sha = response.json()["sha"]

    data = {
        "ref": "refs/heads/main",
        "sha": new_commit_sha,
    }

    url = f"https://api.github.com/repos" f"/DelmiroDaladier/{repo}/git/refs/heads/main"
    response = requests.post(
        url,
        json.dumps(data),
        headers=header,
    )


def _get_sha_last_commit(user: str, auth_token: str, repo: str):
    """
    Get the SHA of the last commit in a GitHub repository's 'main' branch.

    This function sends an HTTP GET request to the GitHub API to retrieve information about the 'main' branch of
    the specified repository. It extracts and returns the SHA (hash) of the last commit in that branch.

    Args:
        user (str): The GitHub username or organization name.
        auth_token (str): The authentication token to access the GitHub API.
        repo (str): The name of the GitHub repository.

    Returns:
        str: The SHA of the last commit in the 'main' branch of the repository.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP request to the GitHub API.
        KeyError: If the response JSON does not contain the expected structure.
    """
    header = {"Authorization": "Bearer " + auth_token}

    sha_last_commit_url = f"https://api.github.com/repos/{user}/{repo}/branches/main"
    response = requests.get(
        sha_last_commit_url,
        headers=header,
    )
    print("******")
    print(sha_last_commit_url)
    print(response)
    sha_last_commit = response.json()["commit"]["sha"]

    return sha_last_commit


def _get_sha_base_tree(user: str, repo: str, auth_token: str, sha_last_commit: str):
    """
    Get the SHA of the base tree associated with a specific commit in a GitHub repository.

    This function sends an HTTP GET request to the GitHub API to retrieve information about the specified commit,
    including the SHA of the associated base tree.

    Args:
        user (str): The GitHub username or organization name.
        repo (str): The name of the GitHub repository.
        auth_token (str): The authentication token to access the GitHub API.
        sha_last_commit (str): The SHA (hash) of the commit for which the base tree SHA is required.

    Returns:
        str: The SHA of the base tree associated with the specified commit.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP request to the GitHub API.
        KeyError: If the response JSON does not contain the expected structure.
    """
    header = {"Authorization": "Bearer " + auth_token}

    url = (
        f"https://api.github.com/repos/" f"{user}/{repo}/git/commits/{sha_last_commit}"
    )
    response = requests.get(url, headers=header)

    sha_base_tree = response.json()["sha"]

    return sha_base_tree


def _read_files_and_create_blob(user: str, repo: str, auth_token: str, files: list):
    """
    Read files and create blob objects in a GitHub repository.

    This function reads a list of files and creates blob objects in the specified GitHub repository for each file's content.

    Args:
        user (str): The GitHub username or organization name.
        repo (str): The name of the GitHub repository.
        auth_token (str): The authentication token to access the GitHub API.
        files (list): A list of file paths to read and create blobs for.

    Returns:
        list: A list of SHA (hash) values for the created blob objects.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP requests to the GitHub API.
        KeyError: If the response JSON does not contain the expected structure.
    """
    blob_sha_list = []

    for file in files:
        with open(file, "r") as fp:
            content = fp.read()

            data = {
                "content": content,
                "encoding": "utf-8",
            }

            header = {
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer " + auth_token,
            }

            url = f"https://api.github.com/repos/{user}/{repo}/git/blobs"
            response = requests.post(
                url,
                json.dumps(data),
                headers=header,
            )

            blob_sha = response.json()["sha"]
            blob_sha_list.append(blob_sha)

    return blob_sha_list


def _post_sha_blob_list(
    user: str,
    repo: str,
    auth_token: str,
    sha_base_tree: str,
    blob_sha_list: list,
    file_path_list: list,
):
    """
    Create and post a new tree object in a GitHub repository.

    This function creates a new tree object in the specified GitHub repository, referencing blob objects created for
    a list of files. The new tree is based on a provided base tree SHA and includes information about the blob objects.

    Args:
        user (str): The GitHub username or organization name.
        repo (str): The name of the GitHub repository.
        auth_token (str): The authentication token to access the GitHub API.
        sha_base_tree (str): The SHA (hash) of the base tree to build upon.
        blob_sha_list (list): A list of SHA values for the blob objects to be included in the new tree.
        file_path_list (list): A list of file paths corresponding to the blob objects.

    Returns:
        str: The SHA of the new tree object created in the GitHub repository.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP request to the GitHub API.
        KeyError: If the response JSON does not contain the expected structure.
    """

    header = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + auth_token,
    }

    data = {
        "base_tree": sha_base_tree,
        "tree": [],
    }

    for blob_sha, file_path in zip(blob_sha_list, file_path_list):
        blob_obj = {
            "path": file_path,
            "mode": "100644",
            "type": "blob",
            "sha": blob_sha,
        }
        data["tree"].append(blob_obj)

    url = f"https://api.github.com/repos/{user}/{repo}/git/trees"
    response = requests.post(
        url,
        json.dumps(data),
        headers=header,
    )
    new_tree_sha = response.json()["sha"]

    return new_tree_sha


def _commit_changes(
    user: str,
    repo: str,
    auth_token: str,
    folder_name: str,
    sha_last_commit: str,
    new_tree_sha: str,
):
    """
    Create a new commit with changes in a GitHub repository.

    This function creates a new commit in the specified GitHub repository with changes based on a new tree object,
    and it updates the 'main' branch to reference the new commit.

    Args:
        user (str): The GitHub username or organization name.
        repo (str): The name of the GitHub repository.
        auth_token (str): The authentication token to access the GitHub API.
        folder_name (str): The name of the folder where changes were made.
        sha_last_commit (str): The SHA (hash) of the last commit on the 'main' branch.
        new_tree_sha (str): The SHA of the new tree object containing the changes.

    Returns:
        None.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP requests to the GitHub API.
        KeyError: If the response JSON does not contain the expected structure.
    """

    header = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + auth_token,
    }

    data = {
        "message": f"Add new files at content/{folder_name}",
        "author": {
            "name": "Delmiro Daladier",
            "email": "daladiersampaio@gmail.com",
        },
        "parents": [sha_last_commit],
        "tree": new_tree_sha,
    }

    url = f"https://api.github.com/repos/" f"{user}/{repo}/git/commits"
    response = requests.post(
        url,
        json.dumps(data),
        headers=header,
    )
    new_commit_sha = response.json()["sha"]

    data = {
        "ref": "refs/heads/main",
        "sha": new_commit_sha,
    }

    url = f"https://api.github.com/repos" f"/{user}/{repo}/git/refs/heads/main"
    response = requests.post(
        url,
        json.dumps(data),
        headers=header,
    )

def git_pull(repo_path):
    try:
        os.chdir(repo_path)
        
        subprocess.run(['git', 'pull', 'origin', 'main'], check=True)
        
        print("Git pull successfull.")
    except subprocess.CalledProcessError as e:
        print(f"Erro when performing git pull: {e}")
    finally:
        os.chdir('..')

def update_repo_and_push(
    folder_name: str, relative_path_list: list, project_name: str, repo: str
):
    """
    Update files in a GitHub repository and push changes to the 'main' branch.

    This function automates the process of updating files in a GitHub repository. It loads user and authentication
    token information from environment variables, retrieves the necessary SHA values, creates blob objects for the
    updated files, constructs a new tree, and commits the changes to the 'main' branch.

    Args:
        folder_name (str): The name of the folder where the changes are made.
        relative_path_list (list): A list of relative paths to the files to be updated.
        project_name (str): The name of the project containing the files.
        repo (str): The name of the GitHub repository.

    Returns:
        None.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP requests to the GitHub API.
        KeyError: If the response JSON does not contain the expected structure.
    """
    load_dotenv()

    file_list = [os.getcwd() + f"/{project_name}/{path}" for path in relative_path_list]

    user = os.getenv("GH_USER")
    auth_token = os.getenv("GH_TOKEN")

    sha_last_commit = _get_sha_last_commit(user, auth_token, repo)
    sha_base_tree = _get_sha_base_tree(user, repo, auth_token, sha_last_commit)
    blob_sha_list = _read_files_and_create_blob(user, repo, auth_token, file_list)
    new_tree_sha = _post_sha_blob_list(
        user, repo, auth_token, sha_base_tree, blob_sha_list, relative_path_list
    )
    _commit_changes(user, repo, auth_token, folder_name, sha_last_commit, new_tree_sha)


def generate_qmd_header_for_arxiv(
    data: dict,
):
    """
    Generate QMD header for Arxiv post.

    This function takes a dictionary of data related to an Arxiv paper and generates a QMD header for it. The header contains metadata about the paper, such as the title, abstract, and author information.

    :param data: A dictionary containing data related to an Arxiv paper.
    :type data: dict
    :return: A dictionary containing the QMD header for the paper.
    :rtype: dict
    # noqa
    """
    content = {
        "title": data.get("citation_title", ""),
        "description": data.get("citation_abstract", ""),
        "image": "https://upload.wikimedia." "org/wikipedia/commons/5/59/Empty.png",
        "categories": data.get("research_area", ""),
        "format": {
            "html": {
                "df-print": "paged",
                "toc": True,
            }
        },
        "execute": {"echo": False},
    }

    content["params"] = {
        "overview": data.get("citation_abstract", ""),
        "pdf_url": data.get("citation_pdf_url", ""),
    }

    for idx, pair in enumerate(
        zip(
            data["citation_author"],
            data["links"],
        ),
        1,
    ):
        content["params"][f"author_{idx}"] = {
            "name": pair[0],
            "link": pair[1],
        }

    if data["research_area"]:
        content["params"]["research_area"] = data["research_area"]

    return content


def scrap_data_from_arxiv(url: str):
    """
    Scrapes metadata from an arXiv article and returns it as a dictionary.

    Args:
        url (str): The URL of the arXiv article to scrape.

    Returns:
        dict: A dictionary containing the scraped data. The keys are:
            - 'citation_author': a list of author names
            - 'citation_title': the title of the article
            - 'citation_pdf_url': the URL of the article's PDF
            - 'citation_abstract': the article's abstract

    Raises:
        This function does not raise any exceptions, but it may fail if the arXiv website
        changes its HTML structure or if the function is used on a different website with a
        different structure.

    Note:
        This function modifies the input URL to include the "export" subdomain, which is
        necessary for accessing the metadata of the article.
    # noqa
    """
    (
        url_first_part,
        url_second_part,
    ) = tuple(url.split("://"))
    url = f"{url_first_part}://export.{url_second_part}"

    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    soup = BeautifulSoup(
        session.get(url).content,
        "html.parser",
    )

    meta_tags = list(soup.find_all("meta"))
    tags = list(meta_tags)
    names = [
        "citation_author",
        "citation_title",
        "citation_pdf_url",
    ]
    selected_tags = [tag for tag in tags if tag.get("name") in names]

    data = defaultdict(list)

    data["citation_abstract"] = (
        soup.select(".abstract")[0]
        .text.replace("\n", "")
        .replace("Abstract:", "")
        .strip()
    )

    for tag in selected_tags:
        if tag.get("name") == "citation_author":
            data[tag.get("name")].append(tag.get("content"))
        else:
            data[tag.get("name")] = tag.get("content")

    if soup.find_all("div", class_="subheader"):
        subheader = list(
            soup.find_all(
                "div",
                class_="subheader",
            )
        )
        data["research_area"] = subheader[-1].h1.text.split(">")[-1].strip().lower()

    else:
        data["research_area"] = None

    if soup.find("div", {"class": "authors"}):
        authors = soup.find("div", {"class": "authors"})
        data["links"] = [
            "https://arxiv.org" + author["href"] for author in authors.find_all("a")
        ]
    else:
        data["links"] = None

    return data


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    # noqa
    """
    try:
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


def remove_years_strings(dates):
    """
    Removes date strings that consist entirely of digits from a list of dates.

    Args:
        dates (list): A list of date strings.

    Returns:
        list: A new list containing only the date strings that do not consist entirely
            of digits.

    Raises:
        This function does not raise any exceptions.

    Note:
        This function uses a regular expression to match date strings consisting entirely of
        digits. Date strings with other characters, such as hyphens or slashes, will not be
        removed by this function.
    # noqa
    """
    return [date for date in dates if not re.fullmatch("[0-9]+", date[0])]


def text_preprocess(text: str, nlp):
    """
    Preprocesses text by removing certain characters and extracting named entities.

    Args:
        text (str): The input text to preprocess.
        nlp: A spaCy NLP model object.

    Returns:
        list: A list of tuples, where each tuple contains a named entity string and its label.

    Raises:
        This function does not raise any exceptions.

    Note:
        This function first splits the input text into sentences, removes certain characters
        (such as non-breaking spaces and zero-width spaces), and then uses a spaCy NLP model
        to extract named entities from each sentence. The resulting named entities are then
        flattened into a list and returned.
    # noqa
    """

    sentences = [
        sentence.replace("\xa0", "").replace("\u200b", "").replace("\n", " ")
        for sentence in text.split("\n")
        if sentence != ""
    ]
    processed_sentences = []
    for sentence in sentences:
        doc = nlp(sentence)
        processed_sentences.append([(X.text, X.label_) for X in doc.ents])
    sentences = []
    sentences = sum(processed_sentences, [])
    return sentences


def fetch_data(url: str):
    """
    Fetches and parses data from a web page.

    Args:
        url (str): A string representing the URL of the web page to fetch.

    Returns:
        A tuple containing the text content of the web page and the text content of the title tag of the web page.
    # noqa
    """
    soup = BeautifulSoup(
        requests.get(url).content,
        "html.parser",
    )
    return soup.text, soup.title.text


def get_days(date: str):
    """
    Extracts day numbers from a string representing a date.

    Args:
        date (str): A string representing the date from which to extract the day numbers.

    Returns:
        A list of strings representing the day numbers found in the date string.
    # noqa
    """
    candidates = re.findall("[0-9]+", date)
    candidates = [
        candidate
        for candidate in candidates
        if not re.fullmatch("\\d\\d\\d\\d", candidate)
    ]

    return candidates


def get_years(date: str):
    """
    Extracts year numbers from a string representing a date.

    Args:
        date (str): A string representing the date from which to extract the year numbers.

    Returns:
        A list of strings representing the year numbers found in the date string.
    # noqa
    """

    candidates = re.findall("[0-9]+", date)
    candidates = [
        candidate for candidate in candidates if re.fullmatch("\\d\\d\\d\\d", candidate)
    ]

    return candidates


def get_month(date: str):
    """
    Extracts month names from a string representing a date.

    Args:
        date (str): A string representing the date from which to extract the month names.

    Returns:
        A list of strings representing the month names found in the date string.
    # noqa
    """
    candidates = re.findall("[A-Za-z]+", date)

    return [
        candidate
        for candidate in candidates
        if candidate not in ("st", "nd", "rd", "th")
    ]


def get_dates_from_text(
    sentences: list,
):
    """
    Extracts dates from a list of sentences that have been annotated with part-of-speech tags.

    Args:
        sentences (list): A list of sentences represented as lists of (word, tag) tuples.

    Returns:
        A list of lists of strings, where each inner list represents the dates found in a single sentence,
        and each string represents a date in the format "Day Month Year".
    # noqa
    """
    dates = [(X[0], X[1]) for X in sentences if X[1] == "DATE"]
    dates = remove_years_strings(dates)
    dates = [date[0] for date in dates]

    dates = [
        date
        for date in dates
        if re.fullmatch(
            "(\\w+\\s)*\\d+(st|nd|rd|th)*\\s(-|to|—|–|through)"
            "\\s(\\w+\\s)*\\d+(st|nd|rd|th)*(\\s\\w+)*(,\\s\\d\\d\\d\\d)*",
            date,
        )
    ]

    year = [get_years(date) for date in dates]
    year = [list(set(item)) for item in year]
    year = year[0][0]

    months = [get_month(date) for date in dates]
    months = [list(set(item)) for item in months]

    days = [get_days(date) for date in dates]
    days = [list(set(item)) for item in days]

    dates = []
    for (
        candidate_day,
        candidate_month,
    ) in zip(days, months):
        dates.append(
            [
                f"{day} {month} {year}"
                for day in candidate_day
                for month in candidate_month
                if month
                not in (
                    "to",
                    "of",
                    "through",
                )
            ]
        )

    dates = [sorted(date, key=lambda x: parse(x)) for date in dates]

    return dates


def get_places_from_text(
    sentences: list,
):
    """
    Extracts the list of geographical places from a given list of tagged sentences.

    Args:
    sentences (list): A list of tuples, where each tuple contains a sentence and its corresponding named entities.

    Returns:
    list: A list of geographical places (as identified by the 'GPE' named entity tag) extracted from the input sentences.
    # noqa
    """
    places = [X[0] for X in sentences if X[1] == "GPE"]
    return places


def get_conference_information(
    url: str,
):
    """
    Extracts information related to a conference from a given URL.

    Args:
    url (str): The URL of the conference website.

    Returns:
    dict: A dictionary containing the extracted information, including dates, places, and title.
    # noqa
    """
    text, title = fetch_data(url)
    nlp = en_core_web_sm.load()
    sentences = text_preprocess(text, nlp)

    dates = get_dates_from_text(sentences)
    places = get_places_from_text(sentences)

    context = {
        "dates": dates,
        "places": places,
        "title": title,
    }

    return context


def _generate_researcher_qmd_header(input_data: dict):
    """
    Generate a Quarto Markdown (QMD) header for a researcher profile.

    This function generates a QMD header with metadata for a researcher profile, including title, description, image,
    and formatting options.

    Args:
        input_data (dict): A dictionary containing metadata for the researcher profile.

    Returns:
        dict: A dictionary representing the QMD header.

    Raises:
        None.
    """
    header = {
        "title": input_data.get("title", ""),
        "description": "",
        "image": "https://upload.wikimedia.org/wikipedia/commons/5/59/Empty.png",
        "format": {
            "html": {
                "df-print": "paged",
                "toc": True,
            }
        },
        "execute": {"echo": False},
    }

    return header


def _generate_author_page_content(input_data: dict, file_path: str):
    """
    Append author's bio content to a markdown file.

    This function appends the author's bio content, retrieved from the input_data dictionary, to the specified markdown file.

    Args:
        input_data (dict): A dictionary containing metadata for the author's page content.
        file_path (str): The path to the markdown file where the bio content will be appended.

    Returns:
        None.

    Raises:
        None.
    """
    with open(file_path, "a") as fp:
        fp.write("\n## Bio \n")
        fp.write(f"{input_data.get('user_bio', '')}\n")


def generate_researcher_profile(input_data: dict):
    """
    Generate a researcher profile in Quarto Markdown (QMD) format.

    This function generates a researcher profile by creating a QMD file with metadata specified in the input_data
    dictionary, including the profile header and bio content. The QMD file is saved in the appropriate directory
    structure based on the provided project and sub-project folders.

    Args:
        input_data (dict): A dictionary containing metadata for the researcher profile.

    Returns:
        None.

    Raises:
        None.
    """
    header = _generate_researcher_qmd_header(input_data)

    folder_name = slugify(header.get("title", "researcher"))

    current_path = os.getcwd()

    current_path = (
        current_path
        + f"/{input_data.get('project_folder', '')}/{input_data.get('sub_project_folder', '')}/{folder_name}/"
    )

    file_path = f"{current_path}index.qmd"

    if not os.path.exists(current_path):
        os.makedirs(current_path)

    with open(file_path, "w+") as fp:
        fp.write("---\n")
        yaml.dump(header, fp)
        fp.write("\n---")

    _generate_author_page_content(input_data, file_path)

    load_dotenv()

    env_name = os.getenv("ENV_NAME")

    if env_name == "prod":

        git_pull('icr_frontend')    

        project_name = input_data.get('project_folder', '')
        relative_path_list = [
            f"researchers/{folder_name}/index.qmd"
        ]
        repo = 'icr'

        update_repo_and_push(folder_name, relative_path_list, project_name, repo)