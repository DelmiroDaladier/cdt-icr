import os
import yaml
from datetime import datetime 

from .models import Newsletter

def create_qmd_file(filepath: str):
    if os.path.exists(filepath):
        os.remove(filepath)

    header = {
        "title": "Interactive AI CDT Newsletter",
        "page-layout": "full",
        "title-block-banner": True,
        "comments": False   
    }

    with open(filepath, 'w+') as fp:
        fp.write('---\n')
        yaml.dump(header, fp)
        fp.write('\n---')

def generate_page_content(filepath: str, content:dict):
    
    title = 'CDT Newsletter'
    text = ''

    with open(filepath, 'a') as fp:
        text += '\n# Posts \n' 

        for post in content['posts']:
            text += f"\n### [{post.get('title', '')}](https://delmirodaladier.github.io/icr/content/{post.get('slug', '')})\n" 
            text += f"\n{post.get('overview', '')}\n"

        text += '\n# Conferences \n'         

        for conference in content['conferences']:
            
            text += f"\n### [{conference.get('name', '')}]({conference.get('link', '')})\n"
            text += f"\n- Location:{conference.get('location', '')}\n"
            text += f"\n- Start date:{conference.get('start_date', '')}\n"
            text += f"\n- End date:{conference.get('end_date', '')}\n" 

        fp.write(text)

    data_dict = {
        'title' : title,
        'text' : text,
        'sent': True
    }

    object = Newsletter(**data_dict)
    object.save()

    


        