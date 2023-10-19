import os
import json
import requests

from dotenv import load_dotenv


def generate_qmd_header(content: dict, form_data: dict):
    """
    Generate a Quarto Markdown (QMD) header for a blog post.

    This function constructs a QMD header, including metadata for a blog post, based on the provided form data.

    Args:
        content (dict): An existing dictionary to which the QMD header metadata will be added.
        form_data (dict): A dictionary containing metadata for the blog post.

    Returns:
        dict: A dictionary representing the QMD header metadata for the blog post.

    Raises:
        None.
    """
    content = {
        "title": form_data.get("name", ""),
        "text": form_data.get("text", ""),
        "categories": [category.title for category in form_data["categories"]],
        "format": {"html": {"df-print": "paged", "toc": True}},
    }

    return content


def generate_page_content(content: str, file_path: str):
    """
    Append content to a markdown file.

    This function appends the provided content to the specified markdown file at the given file path.

    Args:
        content (str): The content to append to the markdown file.
        file_path (str): The path to the markdown file where the content will be appended.

    Returns:
        None.

    Raises:
        None.
    """
    with open(file_path, "a") as fp:
        fp.write("\n")
        overview = content["text"]
        fp.write(f"{overview}\n")


def create_push_request(file_path: str, folder_name: str):
    """
    Create and push changes to a GitHub repository.

    This function creates and pushes changes to a GitHub repository, including creating a new commit with changes to a
    specified file and updating the 'main' branch to reference the new commit.

    Args:
        file_path (str): The path to the file containing the changes to be pushed.
        folder_name (str): The name of the folder where the changes are made.

    Returns:
        None.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the HTTP requests to the GitHub API.
        KeyError: If the response JSON does not contain the expected structure.
    """
    load_dotenv()

    user = os.getenv("GH_USER")
    auth_token = os.getenv("GH_TOKEN")
    repo = os.getenv("GH_REPOSITORY")
    print(auth_token)
    print(repo)
    print(auth_token)
    header = {"Authorization": "Bearer " + auth_token}

    sha_last_commit_url = f"https://api.github.com/repos/{user}/{repo}/branches/main"
    print(f"https://api.github.com/repos/{user}/{repo}/branches/main")
    response = requests.get(sha_last_commit_url, headers=header)
    print(response.json())
    sha_last_commit = response.json()["commit"]["sha"]

    url = f"https://api.github.com/repos/{user}/{repo}/git/commits/{sha_last_commit}"
    response = requests.get(url, headers=header)
    sha_base_tree = response.json()["sha"]

    with open(file_path, "r") as fp:
        content = fp.read()

    data = {"content": content, "encoding": "utf-8"}

    header = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + auth_token,
    }

    url = "https://api.github.com/repos/DelmiroDaladier/icr/git/blobs"
    response = requests.post(url, json.dumps(data), headers=header)
    blob_sha = response.json()["sha"]

    data = {
        "base_tree": sha_base_tree,
        "tree": [
            {
                "path": f"posts/{folder_name}/index.qmd",
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            }
        ],
    }

    url = "https://api.github.com/repos/Delmirodaladier/icr/git/trees"
    response = requests.post(url, json.dumps(data), headers=header)
    tree_sha = response.json()["sha"]

    data = {
        "message": f"Add new files at posts/{folder_name}",
        "author": {
            "name": "Delmiro Daladier",
            "email": "daladiersampaio@gmail.com",
        },
        "parents": [sha_last_commit],
        "tree": tree_sha,
    }

    url = f"https://api.github.com/repos/DelmiroDaladier/icr/git/commits"
    response = requests.post(url, json.dumps(data), headers=header)
    new_commit_sha = response.json()["sha"]

    data = {"ref": "refs/heads/main", "sha": new_commit_sha}

    url = f"https://api.github.com/repos/DelmiroDaladier/icr/git/refs/heads/main"
    response = requests.post(url, json.dumps(data), headers=header)
