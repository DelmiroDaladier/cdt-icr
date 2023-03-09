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
    """

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
    """
    if os.path.exists(filepath):
        os.remove(filepath)

    df = pd.DataFrame(list(conference_objects.values()))
    df.drop('conference_id', axis=1)

    df.to_csv(filepath, index=False)


def generate_page_content(content, filepath: str):
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
    """
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
    """
    Creates and pushes a new file with the content of a given file path to the specified GitHub repository.

    Args:
        file_path (str): The path of the file to be uploaded.
        folder_name (str): The name of the folder where the file will be stored.
        repo (str): The name of the GitHub repository.

    Returns:
        None
    """
    load_dotenv()

    user = os.getenv('GH_USER')
    auth_token = os.getenv('GH_TOKEN')

    header = {
        'Authorization': 'Bearer ' + auth_token
    }

    sha_last_commit_url = f'https://api.github.com/repos/{user}/{repo}/branches/main'
    response = requests.get(sha_last_commit_url, headers=header)
    print(response)
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
        path = 'input.csv'
    else:
        path = f'content/{folder_name}/index.qmd'

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
    """
    Generate QMD header for Arxiv post.

    This function takes a dictionary of data related to an Arxiv paper and generates a QMD header for it. The header contains metadata about the paper, such as the title, abstract, and author information.

    :param data: A dictionary containing data related to an Arxiv paper.
    :type data: dict
    :return: A dictionary containing the QMD header for the paper.
    :rtype: dict
    """
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
    """
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
    """
    return [date for date in dates if not re.fullmatch('[0-9]+', date[0])]


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
    """

    sentences = [
        sentence.replace(
            '\xa0',
            '').replace(
            '\u200b',
            '').replace(
                '\n',
            ' ') for sentence in text.split('\n') if sentence != '']
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
    """
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    return soup.text, soup.title.text


def get_days(date: str):
    """
    Extracts day numbers from a string representing a date.

    Args:
        date (str): A string representing the date from which to extract the day numbers.

    Returns:
        A list of strings representing the day numbers found in the date string.
    """
    candidates = re.findall('[0-9]+', date)
    candidates = [
        candidate for candidate in candidates if not re.fullmatch(
            '\\d\\d\\d\\d', candidate)]

    return candidates


def get_years(date: str):
    """
    Extracts year numbers from a string representing a date.

    Args:
        date (str): A string representing the date from which to extract the year numbers.

    Returns:
        A list of strings representing the year numbers found in the date string.
    """

    candidates = re.findall('[0-9]+', date)
    candidates = [
        candidate for candidate in candidates if re.fullmatch(
            '\\d\\d\\d\\d', candidate)]

    return candidates


def get_month(date: str):
    """
    Extracts month names from a string representing a date.

    Args:
        date (str): A string representing the date from which to extract the month names.

    Returns:
        A list of strings representing the month names found in the date string.
    """
    candidates = re.findall('[A-Za-z]+', date)

    return [
        candidate for candidate in candidates if candidate not in (
            'st',
            'nd',
            'rd',
            'th')]


def get_dates_from_text(sentences: list):
    """
    Extracts dates from a list of sentences that have been annotated with part-of-speech tags.

    Args:
        sentences (list): A list of sentences represented as lists of (word, tag) tuples.

    Returns:
        A list of lists of strings, where each inner list represents the dates found in a single sentence,
        and each string represents a date in the format "Day Month Year".
    """
    dates = [(X[0], X[1]) for X in sentences if X[1] == 'DATE']
    dates = remove_years_strings(dates)
    dates = [date[0] for date in dates]

    dates = [
        date for date in dates if re.fullmatch(
            '(\\w+\\s)*\\d+(st|nd|rd|th)*\\s(-|to|—|–|through)\\s(\\w+\\s)*\\d+(st|nd|rd|th)*(\\s\\w+)*(,\\s\\d\\d\\d\\d)*',
            date)]

    year = [get_years(date) for date in dates]
    year = [list(set(item)) for item in year]
    year = year[0][0]

    months = [get_month(date) for date in dates]
    months = [list(set(item)) for item in months]

    days = [get_days(date) for date in dates]
    days = [list(set(item)) for item in days]

    dates = []
    for candidate_day, candidate_month in zip(days, months):
        dates.append(
            [
                f"{day} {month} {year}" for day in candidate_day for month in candidate_month if month not in (
                    'to',
                    'of',
                    'through')])

    dates = [sorted(date, key=lambda x: parse(x)) for date in dates]

    return dates


def get_places_from_text(sentences: list):
    """
    Extracts the list of geographical places from a given list of tagged sentences.

    Args:
    sentences (list): A list of tuples, where each tuple contains a sentence and its corresponding named entities.

    Returns:
    list: A list of geographical places (as identified by the 'GPE' named entity tag) extracted from the input sentences.
    """
    places = [X[0] for X in sentences if X[1] == 'GPE']
    return places


def get_conference_information(url: str):
    """
    Extracts information related to a conference from a given URL.

    Args:
    url (str): The URL of the conference website.

    Returns:
    dict: A dictionary containing the extracted information, including dates, places, and title.
    """
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
