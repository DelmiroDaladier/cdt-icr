import os
import json
import requests

from dotenv import load_dotenv


def generate_qmd_header(content: dict, form_data: dict):
    content = {
        "title": form_data.get("title", ""),
        "text": form_data.get("text", ""),
        "categories": [category.title for category in form_data["categories"]],
        "format": {"html": {"df-print": "paged", "toc": True}},
    }

    return content


def generate_page_content(content: str, file_path: str):
    with open(file_path, "a") as fp:
        print(content)
        fp.write("\n")
        overview = content["text"]
        fp.write(f"{overview}\n")


def create_push_request(file_path: str, folder_name: str):
    load_dotenv()

    user = os.getenv("GH_USER")
    auth_token = os.getenv("GH_TOKEN")
    repo = os.getenv("GH_REPOSITORY")

    header = {"Authorization": "Bearer " + auth_token}

    sha_last_commit_url = (
        f"https://api.github.com/repos/{user}/{repo}/branches/main"
    )
    response = requests.get(sha_last_commit_url, headers=header)

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

    url = (
        f"https://api.github.com/repos/DelmiroDaladier/icr/git/refs/heads/main"
    )
    response = requests.post(url, json.dumps(data), headers=header)
