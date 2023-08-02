import django, json, srsly, csv

django.setup()
from sefaria.model import *
from tqdm import tqdm
import re
import sys
import random

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
    file = sys.argv[1]
    output_filename = sys.argv[2]
    num_of_mentions_for_each_genre = int(sys.argv[3])

    with open(file) as f:
        mentions = json.load(f)

    prodigy_dataset = []
    random.shuffle(mentions)

    mentions_bavli = num_of_mentions_for_each_genre
    mentions_yerushalmi = num_of_mentions_for_each_genre
    mentions_mishnah = num_of_mentions_for_each_genre

    for mention in tqdm(mentions, desc="trimming mentions of " + file ):

        if(mentions_bavli == 0 and mentions_mishnah == 0 and mentions_yerushalmi == 0):
            break
        if is_bavli(mention) and mentions_bavli > 0:
            prodigy_dataset.append(mention)
            mentions_bavli -= 1
        elif is_yerushalmi(mention) and mentions_yerushalmi > 0:
            prodigy_dataset.append(mention)
            mentions_yerushalmi -= 1
        elif is_mishna(mention) and mentions_mishnah > 0:
            prodigy_dataset.append(mention)
            mentions_mishnah -= 1


    #aggregated_list = list(aggregated_dict.values())

    with open(output_filename, "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(prodigy_dataset, f, ensure_ascii=False, indent=2)
