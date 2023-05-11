import django, json, srsly, csv

django.setup()
from sefaria.model import *
from tqdm import tqdm
from spacy.lang.he import Hebrew
from sefaria.spacy_function_registry import inner_punct_tokenizer_factory
from sefaria.model.linker.ref_part import span_inds
from util.helper import create_normalizer
import spacy
from spacy import displacy


# "
# {
#     "text": <text of segment>,
#     "spans": [<see definition of span below>],
#     "meta": {
#         "Ref": <ref>,
#         "Version Title": <version title>,
#         "Language": <language>
#     }
# }"
#
# "
# {
#     "start": <start character of mention>,
#     "end": <end character of mention>,
#     "token_start": <start token of mention>,
#     "token_end": <end token of mention>,
#     "label": "Person"
# }"




if __name__ == "__main__":
    print("hello world")
    nlp = spacy.load('../models/people_he/model-best')
    {
        "text": "אמר רב הונא שכיב מרע שהקדיש כל נכסיו ואמר מנה לפלוני בידי נאמן חזקה אין אדם עושה קנוניא על הקדש",
        "spans": [
            {
                "start": 4,
                "end": 11,
                "token_start": 1,
                "token_end": 2,
                "label": "Person"
            }
        ],
        "meta": {
            "ref": "Bava Batra 174b:19",
            "version_title": "William Davidson Edition - Aramaic",
            "language": "he"
        }
    },
    with open('test.json') as f:
        segments = json.load(f)
    docs = []
    i = 0
    for segment in segments:
        text = segment["text"]
        # print(text)
        docs.append(nlp(text))
        i = i+1
        if i > 1000:
            break
    
    displacy.serve(docs, style="ent")

        # for ent in doc.ents:
        #     # print(ent.text, ent.label_)
        #     displacy.serve(doc, style="ent")
        #     # options = {"colors": {"ENT": "red"}}
        #     # displacy.render(doc, style="ent", options=options)

            # print(doc)
    # Process the text


    # # Print the entities
    # for ent in doc.ents:
    #     print(ent.text, ent.label_)



