import django, json, srsly, csv

django.setup()
from sefaria.model import *
from tqdm import tqdm
import re
import sys
import random
import spacy
from util.helper import create_normalizer

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
    i = 0

    problematic = []
    eval = []
    num_of_test_mentions = 0

    model_file = sys.argv[1]
    test_mentions_file = sys.argv[2]
    nlp = spacy.load(model_file)
    with open(test_mentions_file) as f:
        test_segments = json.load(f)

    for segment in tqdm(test_segments):
        # i += 1
        # if i >= 1000:
        #     break
        text = segment["text"]
        prediction = nlp(text)
        test_spans_for_segment = set()
        predicted_spans_for_segment = set()

        pred_ents = set()
        test_ents = set()
        for span in segment["spans"]:
            # keys_to_extract = ['start', 'end']
            test_spans_for_segment.add((span["token_start"], span["token_end"]))
            test_ents.add(segment['text'][span['start']:span['end']])
            num_of_test_mentions += 1
        for ent in prediction.ents:
            # spans = {'start': ent.start, 'end' : ent.end}
            predicted_spans_for_segment.add((ent.start, ent.end-1))
            pred_ents.add(ent.text)

            prediction

        eval.append(len(test_spans_for_segment.intersection(predicted_spans_for_segment)))

        if test_spans_for_segment != predicted_spans_for_segment:
            # 
            # #highlight model:
            # for token in segment["text"]:
            #     if start <= token.i <= end:
            #         highlighted_text_predicted += "**" + str(token) + "** "
            #     else:
            #         highlighted_text_predicted += str(token) + " "

            problematic.append({'text': segment['text'], "predicted spans": list(predicted_spans_for_segment.difference(test_spans_for_segment)),
                                'test spans': list(test_spans_for_segment.difference(predicted_spans_for_segment)),
                               'predicted ents': list(pred_ents.difference(test_ents)),
                                'test ents': list(test_ents.difference(pred_ents))})

    with open("model_errors.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(problematic, f, ensure_ascii=False, indent=2)

    print("Accuracy: ", sum(eval)/num_of_test_mentions)