import os
import yaml

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
    with open(filepath, 'a') as fp:
        fp.write('\n# Posts \n')

        for post in content['posts']:
            fp.write(f"\n### [{post.get('title', '')}](https://delmirodaladier.github.io/icr/content/{post.get('slug', '')})\n")
            fp.write(f"\n{post.get('overview', '')}\n")
        
        fp.write('\n# Conferences \n')

        for conference in content['conferences']:
            print(conference)
            fp.write(f"\n### [{conference.get('name', '')}]({conference.get('link', '')})\n")
            fp.write(f"\n- Location:{conference.get('location', '')}\n")
            fp.write(f"\n- Start date:{conference.get('start_date', '')}\n")
            fp.write(f"\n- End date:{conference.get('end_date', '')}\n")
