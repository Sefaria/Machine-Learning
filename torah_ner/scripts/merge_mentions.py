import django, json, srsly, csv

django.setup()
from sefaria.model import *
from tqdm import tqdm
from spacy.lang.he import Hebrew
from sefaria.spacy_function_registry import inner_punct_tokenizer_factory
from sefaria.model.linker.ref_part import span_inds
from util.library_exporter import create_normalizer

import typer
import subprocess
import yaml
import sys


if __name__ == "__main__":
    print("hello world")


    # get the names of the files to merge from command line arguments
    files = sys.argv[1:]

    merged = []

    # loop through the files and merge them
    for file in files:
        with open(file) as f:
            data = json.load(f)
            for item in data:
                merged.append(item)


    # write the merged data to a new file
    with open('merged.json', 'w') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

