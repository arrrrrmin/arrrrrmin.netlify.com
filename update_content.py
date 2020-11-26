#!/usr/bin/env python3

import os
import argparse
import datetime

name_config = {
    "Let me introduce myself": "Intro",
    "Libs and Tools": "Skills",
    "Work Experience": "Work Experience",
    "Previous Projects": "Projects",
}

def get_page_meta(key) -> str:
    return f"--- \ntitle: {key} \ndate: {datetime.datetime.utcnow()}\ndraft: false\n---\n\n"

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--source_markdown", type=str, required=True,
        help="Pass a path to source markdown file to parse information from")
    args = arg_parser.parse_args()

    if not os.path.exists("content/posts"):
        os.mkdir("content/posts")
    assert os.path.exists(args.source_markdown), "Source not found"

    contents = {}
    raw = open(args.source_markdown, "r").read()

    for section in raw.split("## "):
        for key in name_config.keys():
            if section.split("\n")[0].endswith(key):
                with open(f"content/posts/{name_config[key].replace(' ', '_')}.md", "w") as content_file:
                    page_meta = get_page_meta(name_config[key])
                    page_content = '\n'.join(line for line in section.split('\n')[1:])
                    content_file.write(f"{page_meta}{page_content}")




