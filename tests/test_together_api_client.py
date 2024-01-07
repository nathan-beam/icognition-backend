import os
import json
from app.together_api_client import TogetherMixtralClient
from app.together_api_client import InclusiveTemplate


# Get working directory
cwd = os.getcwd()
directory = os.path.join(cwd, "tests/data/")


def read_txt_files(directory):
    txt_files = []
    for file in os.listdir(directory):
        if file.endswith(".txt"):
            file_path = os.path.join(directory, file)
            with open(file_path, "r") as f:
                txt_files.append(f.read())
    return txt_files


txt_files = read_txt_files(directory)


def test_three_in_one_summary():
    template = InclusiveTemplate()
    client = TogetherMixtralClient()
    for text in txt_files:
        res = client.generate(body_text=text.encode(), template=template)
        assert res is not None
