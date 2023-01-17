import django, json, srsly, csv

django.setup()
from sefaria.model import *
from tqdm import tqdm
import re
import sys

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



if __name__ == "__main__":
    print("hello world")
    # stats
    files = sys.argv[1:]
    for file in files:
        with open(file) as f:
            mentions = json.load(f)

        trimmed_training = []
        test = []


        for mention in tqdm(mentions, desc="trimming mentions of " + file ):
            page_number = re.search(r"\d+", mention['meta']['ref'])
            if int(page_number.group(0)) < 10:
                trimmed_training.append(mention)
            else:
                test.append(mention)

        #aggregated_list = list(aggregated_dict.values())

        with open("trimmed_" + file, "w") as f:
            # Write the list of dictionaries to the file as JSON
            json.dump(trimmed_training, f, ensure_ascii=False, indent=2)
        with open("test_" + file, "w") as f:
            # Write the list of dictionaries to the file as JSON
            json.dump(test, f, ensure_ascii=False, indent=2)