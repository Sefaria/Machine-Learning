import django, json, srsly, csv

django.setup()
# from sefaria.model import *
from tqdm import tqdm
from spacy.lang.he import Hebrew
from sefaria.spacy_function_registry import inner_punct_tokenizer_factory
from sefaria.model.linker.ref_part import span_inds
from util.library_exporter import create_normalizer
import random
import sys
import spacy


def is_bavli(mention):
    if "Mishnah" not in mention['meta']['ref'] and "Jerusalem" not in mention['meta']['ref']:
        return True
    else:
        return False


def is_yerushalmi(mention):
    if "Jerusalem" in mention['meta']['ref']:
        return True
    else:
        return False


def is_mishna(mention):
    if "Mishnah" in mention['meta']['ref']:
        return True
    else:
        return False


basic_par_pattern = '<figure style="margin-bottom: 6rem"><div class="entities" style="line-height: 2.5; direction: ltr">{}</figure>'


entity_open = '<mark class="entity" style="background: #aa9cfc; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">'
entity_close = '<span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; vertical-align: middle; margin-left: 0.5rem">Person</span></mark>'


def wrap_string_with_html_tag(base_string, tag_tuples, html_tag_open, html_tag_close):
    # Sort the tag tuples in descending order of end index
    tag_tuples = sorted(tag_tuples, key=lambda x: x[1], reverse=True)

    # Iterate over each tag tuple
    for start_index, end_index in tag_tuples:
        # Construct the opening and closing tags
        opening_tag = html_tag_open
        closing_tag = html_tag_close

        # Insert the closing tag at the end index, and the opening tag at the start index
        base_string = base_string[:end_index] + closing_tag + base_string[end_index:]
        base_string = base_string[:start_index] + opening_tag + base_string[start_index:]

    # Return the modified string
    return base_string


def create_html_table(data):
    """
    Converts a list of tuples into a beautiful HTML table.

    Parameters:
    data (list): A list of tuples where each tuple represents a row in the table.

    Returns:
    str: A string containing the HTML code for the table.
    """
    # Create the header row
    header_row = "<tr>{}</tr>".format("".join(["<th>{}</th>".format(col) for col in data[0]]))

    # Create the data rows
    data_rows = "".join(
        ["<tr>{}</tr>".format("".join(["<td>{}</td>".format(cell) for cell in row])) for row in data[1:]])

    # Create the table
    html_table = "<table>{}</table>".format(header_row + data_rows)

    return html_table

def wrap_html(inner_html):
    if '_he' in test_mentions_file:
        return '<html lang="he"> <body style="font-size: 16px; padding: 4rem 2rem; direction: rtl">{}</html>'.format(inner_html)
    else:
        return '<html lang="en"> <body style="font-size: 16px; padding: 4rem 2rem;">{}</html>'.format(inner_html)

def instantiate_patterns(file_name):
    global basic_par_pattern
    if "_he" in file_name:
        basic_par_pattern = '<figure style="margin-bottom: 6rem"><div class="entities" style="line-height: 2.5; direction: rtl">{}</figure>'
    else:
        basic_par_pattern = '<figure style="margin-bottom: 6rem"><div class="entities" style="line-height: 2.5; direction: ltr">{}</figure>'




if __name__ == "__main__":
    # print("hello world")
    test_mentions_file = sys.argv[1]
    model_path = sys.argv[2]
    instantiate_patterns(test_mentions_file)

    comparison_table = []
    comparison_table.append( ("Ref", "Old Model - Rulebased", "New Model - Machine Learning") )

    nlp = spacy.load(model_path)
    with open(test_mentions_file) as f:
        segments = json.load(f)

    for segment in tqdm(segments):
        text = segment["text"]
        ml_prediction = nlp(text)
        rule_based_string = basic_par_pattern[:]
        ml_string = basic_par_pattern[:]
        
        index_tuples = []
        for span in segment["spans"]:
            index_tuples.append((int(span["start"]), int(span["end"])))
        h = wrap_string_with_html_tag(text, index_tuples, entity_open, entity_close)
        rule_based_string = rule_based_string.format(h)

        index_tuples = []
        for ent in ml_prediction.ents:
            index_tuples.append((ent.start_char, ent.end_char))
        h = wrap_string_with_html_tag(text, index_tuples, entity_open, entity_close)
        ml_string = ml_string.format(h)

        comparison_table.append((segment["meta"]["ref"], rule_based_string, ml_string))
        
        
        
        
        



    # Open a file in write mode and write the HTML string to the file
    with open("my_file.html", "w") as f:
        f.write(create_html_table(comparison_table))
