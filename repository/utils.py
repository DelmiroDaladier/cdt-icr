import os
import re
import json
import yaml
import requests
from dateutil.parser import parse
from collections import defaultdict
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

import spacy
import pandas as pd
import en_core_web_sm
from spacy import displacy
from bs4 import BeautifulSoup
from dotenv import load_dotenv


def generate_qmd_header(content: dict, form_data: dict):

    if form_data['thumbnail'] is None:
        form_data['thumbnail'] = 'https://upload.wikimedia.org/wikipedia/commons/5/59/Empty.png'

    content = {
        'title': form_data.get(
            'title',
            ''),
        'description': form_data.get(
            'overview',
            ''),
        'image': form_data.get(
            'thumbnail',
            'https://upload.wikimedia.org/wikipedia/commons/5/59/Empty.png'),
        'categories': [
            category.title for category in form_data['categories']],
        'format': {
            'html': {
                'df-print': 'paged',
                            'toc': True}}}

    content['params'] = {
        'overview': form_data['overview'],

        'scholar_url': form_data.get('citation', ''),

        'pdf_url': form_data.get('pdf', ''),

        'poster_url': form_data.get('poster', ''),

        'code_url': form_data.get('code', ''),

        'supplement_url': form_data.get('supplement', ''),

        'slides_url': form_data.get('slides', '')
    }

    for idx, author in enumerate(form_data['authors'], 1):
        content['params'][f'author_{idx}'] = {
            'name': author.user,
            'url': author.user_url
        }

    return content

def save_new_conference_data(conference_objects, filepath: str):
    
    os.remove(filepath)

    df = pd.DataFrame(list(conference_objects.values()))
    print(df)
    df.to_csv(filepath)


def generate_page_content(content, filepath: str):

    with open(filepath, 'a') as fp:
        fp.write('\n## Tldr \n')
        overview = content['params']['overview']
        fp.write(f'{overview}\n')
        fp.write('\n## Paper-authors\n')
        for param in content['params']:
            if param.startswith('author'):
                fp.write(
                    f'- [{{{{< meta params.{param}.name >}}}}]({{{{< meta params.{param}.url >}}}})\n')

        fp.write('\n## More Resources\n')

        if 'scholar_url' in content['params']:
            fp.write(
                '[![](https://img.shields.io/badge/citation-scholar-9cf?style=flat.svg)]({{< meta params.scholar_url >}})\n')

        if 'pdf_url' in content['params'].keys():
            fp.write(
                '[![](https://img.shields.io/badge/PDF-green?style=flat)]({{< meta params.pdf_url >}})\n')
        if 'supplement_url' in content['params'].keys():
            fp.write(
                '[![](https://img.shields.io/badge/supplement-yellowgreen?style=flat)]({{< meta params.supplement_url >}})\n')
        if 'slides_url' in content['params'].keys():
            fp.write(
                '[![](https://img.shields.io/badge/blog-blue?style=flat)]({{< meta params.slides_url >}}\n')
        if 'poster_url' in content['params'].keys():
            fp.write(
                '[![](https://img.shields.io/badge/poster-yellow?style=flat)]({{< meta params.poster_url >}})\n')
        if 'code_url' in content['params'].keys():
            fp.write(
                '[![](https://img.shields.io/badge/code-blueviolet?style=flat)]({{< meta params.code_url >}})\n')


def create_push_request(file_path: str, folder_name: str, repo: str):

    
    load_dotenv(override=True)

    user = os.getenv('GH_USER')
    auth_token = os.getenv('GH_TOKEN')

    header = {
        'Authorization': 'Bearer ' + auth_token
    }

    

    sha_last_commit_url = f'https://api.github.com/repos/{user}/{repo}/branches/main'
    response = requests.get(sha_last_commit_url, headers=header)
   
    sha_last_commit = response.json()['commit']['sha']

    url = f'https://api.github.com/repos/{user}/{repo}/git/commits/{sha_last_commit}'
    response = requests.get(url, headers=header)

    sha_base_tree = response.json()['sha']

    with open(file_path, 'r') as fp:
        content = fp.read()

    data = {
        "content": content,
        "encoding": 'utf-8'
    }

    header = {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer ' + auth_token
    }

    url = f'https://api.github.com/repos/DelmiroDaladier/{repo}/git/blobs'
    response = requests.post(url, json.dumps(data), headers=header)
    blob_sha = response.json()['sha']

    path = ''

    if folder_name == '':
        path = 'index.qmd'
    else:
        path = f'content/{folder_name}/index.qmd'

    print(path)

    data = {
        'base_tree': sha_base_tree,
        'tree': [
            {
                'path': path,
                'mode': '100644',
                'type': 'blob',
                'sha': blob_sha
            }
        ]
    }

    print(data)

    url = f'https://api.github.com/repos/Delmirodaladier/{repo}/git/trees'
    response = requests.post(url, json.dumps(data), headers=header)

    tree_sha = response.json()['sha']

    data = {
        "message": f"Add new files at content/{folder_name}",
        "author": {
            "name": "Delmiro Daladier",
            "email": "daladiersampaio@gmail.com"
        },
        "parents": [
            sha_last_commit
        ],
        "tree": tree_sha
    }

    url = f'https://api.github.com/repos/DelmiroDaladier/{repo}/git/commits'
    response = requests.post(url, json.dumps(data), headers=header)
    new_commit_sha = response.json()['sha']

    data = {
        "ref": "refs/heads/main",
        "sha": new_commit_sha
    }

    url = f'https://api.github.com/repos/DelmiroDaladier/{repo}/git/refs/heads/main'
    response = requests.post(url, json.dumps(data), headers=header)


def generate_qmd_header_for_arxiv(data: dict):
    content = {
        'title': data.get('citation_title', ''),
        'description': data.get('citation_abstract', ''),
        'image': 'https://upload.wikimedia.org/wikipedia/commons/5/59/Empty.png',
        'format': {
            'html': {
                'df-print': 'paged',
                'toc': True
            }
        }
    }

    content['params'] = {
        'overview': data.get('citation_abstract', ''),

        'pdf_url': data.get('citation_pdf_url', ''),
    }

    for idx, author in enumerate(data['citation_author'], 1):
        content['params'][f'author_{idx}'] = {
            'name': author,
        }

    return content


def scrap_data_from_arxiv(url: str):
    url_first_part, url_second_part = tuple(url.split('://'))
    url = f"{url_first_part}://export.{url_second_part}"

    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    soup = BeautifulSoup(session.get(url).content, "html.parser")

    meta_tags = list(soup.find_all("meta"))
    tags = list(meta_tags)
    names = [
        'citation_author',
        'citation_title',
        'citation_pdf_url']
    selected_tags = [tag for tag in tags if tag.get('name') in names]

    data = defaultdict(list)

    data['citation_abstract'] = soup.select('.abstract')[0].text.replace(
        '\n', '').replace('Abstract:', '').strip()

    for tag in selected_tags:
        if tag.get('name') == 'citation_author':
            data[tag.get('name')].append(tag.get('content'))
        else:
            data[tag.get('name')] = tag.get('content')

    return data

def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False

def remove_years_strings(dates):
    return [date for date in dates if not re.fullmatch('[0-9]+', date[0])]

def text_preprocess(text: str, nlp):
    
    sentences = [sentence.replace('\xa0', '').replace('\u200b', '').replace('\n', ' ') for sentence in text.split('\n') if sentence != '']
    processed_sentences =[]
    for sentence in sentences:
        doc = nlp(sentence)
        processed_sentences.append([(X.text, X.label_) for X in doc.ents])
    sentences = []
    sentences = sum(processed_sentences, [])
    return sentences

def fetch_data(url: str):
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    return soup.text, soup.title.text

def get_days(date: str):
    candidates = re.findall('[0-9]+', date)
    candidates = [candidate for candidate in candidates if not re.fullmatch('\d\d\d\d', candidate)]
    
    return candidates 

def get_years(date: str):
    candidates = re.findall('[0-9]+', date)
    candidates = [candidate for candidate in candidates if re.fullmatch('\d\d\d\d', candidate)]

    return candidates

def get_month(date: str):
    candidates = re.findall('[A-Za-z]+', date)

    return [candidate for candidate in candidates if candidate not in ('st', 'nd', 'rd', 'th')]

def get_dates_from_text(sentences: list):
    dates = [(X[0], X[1]) for X in sentences if X[1]=='DATE']
    dates = remove_years_strings(dates)
    dates = [date[0] for date in dates]
    
    dates = [date for date in dates if re.fullmatch('(\w+\s)*\d+(st|nd|rd|th)*\s(-|to|—|–|through)\s(\w+\s)*\d+(st|nd|rd|th)*(\s\w+)*(,\s\d\d\d\d)*', date)]

    year = [get_years(date) for date in dates]
    year = [list(set(item)) for item in year]
    year = year[0][0]

    months = [get_month(date) for date in dates]
    months = [list(set(item)) for item in months]

    days = [get_days(date) for date in dates]
    days = [list(set(item)) for item in days]

    dates = []
    for candidate_day, candidate_month in zip(days, months):
        dates.append([f"{day} {month} {year}" for day in candidate_day for month in candidate_month if month not in ('to', 'of', 'through')])

    dates = [sorted(date, key=lambda x: parse(x)) for date in dates]

    return dates

def get_places_from_text(sentences: list):
    places = [X[0] for X in sentences if X[1]=='GPE']    
    return places



def get_conference_information(url: str):

    text, title = fetch_data(url)
    nlp = en_core_web_sm.load()
    sentences = text_preprocess(text, nlp)

    dates = get_dates_from_text(sentences)
    places = get_places_from_text(sentences)

    context = {
        'dates': dates,
        'places': places,
        'title': title 
    }

    return context