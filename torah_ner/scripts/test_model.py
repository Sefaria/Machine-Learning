import django, json, srsly, csv

django.setup()
from sefaria.model import *
from tqdm import tqdm
import re
import sys
import random
import spacy
from util.library_exporter import create_normalizer

#
#
# {
#     "text": "אמר רב הונא שכיב מרע שהקדיש כל נכסיו ואמר מנה לפלוני בידי נאמן חזקה אין אדם עושה קנוניא על הקדש",
#     "spans": [
#       {
#         "start": 4,
#         "end": 11,
#         "token_start": 1,
#         "token_end": 2,
#         "label": "Person"
#       }
#     ],
#     "meta": {
#       "ref": "Bava Batra 174b:19",
#       "version_title": "William Davidson Edition - Aramaic",
#       "language": "he"
#     }
#   }
def include_in_trimmed_bavli(mention):
    page_number = re.search(r"\d+", mention['meta']['ref'])
    if int(page_number.group(0)) < 10:
        return True
    else:
        return False
def include_in_trimmed_yerushalmi(mention):
    page_number = re.search(r"\d+", mention['meta']['ref'])
    if int(page_number.group(0)) < 10:
        return True
    else:
        return False
def include_in_trimmed_mishna(mention):
    perek_number = re.search(r"\d+", mention['meta']['ref'])
    if int(perek_number.group(0)) <= 1:
        return True
    else:
        return False

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



if __name__ == "__main__":
    print("hello world")
    # stats

    predicted_spans = []
    truth_spans = []
    eval = []
    num_of_test_mentions = 0

    test_mentions_file = sys.argv[1]
    nlp = spacy.load('../models/people_en/model-best')
    with open(test_mentions_file) as f:
        test_segments = json.load(f)

    for segment in tqdm(test_segments):
        text = segment["text"]
        # print(text)
        prediction = nlp(text)
        # print(prediction)
        a = prediction.spans
        predicted = []
        test_spans_for_segment = set()
        predicted_spans_for_segment = set()
        for span in segment["spans"]:
            # keys_to_extract = ['start', 'end']
            test_spans_for_segment.add((span["token_start"], span["token_end"]))
            num_of_test_mentions += 1
        for ent in prediction.ents:
            # spans = {'start': ent.start, 'end' : ent.end}
            predicted_spans_for_segment.add((ent.start, ent.end-1))

        eval.append(len(test_spans_for_segment.intersection(predicted_spans_for_segment)))


    print("Accuracy: ", sum(eval)/num_of_test_mentions)