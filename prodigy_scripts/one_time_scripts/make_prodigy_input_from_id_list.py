from db_manager import MongoProdigyDBManager
import csv
from bson import ObjectId

def get_id_list():
    with open("/Users/nss/Downloads/docs to correct - Sheet1.csv") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            yield row['doc id']


def convert_en_labels_to_he(doc):
    for span in doc['spans']:
        if span['label'] == 'Citation':
            span['label'] = 'מקור'
        elif span['label'] == 'Person':
            span['label'] = 'בן-אדם'
        else:
            raise Exception("Unknown label: {}".format(span['label']))
    return doc

if __name__ == '__main__':
    from_collection = "ner_he_gpt_copper_diff"
    to_collection = "ner_he_gpt_correction_input"
    id_list = list(get_id_list())
    input_db = MongoProdigyDBManager(from_collection)
    output_db = MongoProdigyDBManager(to_collection)
    output_db.output_collection.delete_many({})
    for doc in input_db.output_collection.find({}):
        doc = convert_en_labels_to_he(doc)
        output_db.output_collection.insert_one(doc)
    # for doc_id in id_list:
    #     doc = input_db.output_collection.find_one({"_id": ObjectId(doc_id)})
    #     doc = convert_en_labels_to_he(doc)
    #     output_db.output_collection.insert_one(doc)

"""
1 iteration of training:
1) Delete existing docs to correct and download new one. Leave it in Downloads folder
2) Run make_prodigy_input_from_id_list.py. No need to touch Mongo or parameters
3) Delete ner_he_gpt_correction_input and ner_he_gpt_correction_output on dev cluster. Upload collection from local.
4) restart prodigy server
5) Tag data according to docs to correct
6) export ner_he_gpt_correction_output to rishonim_output_gold on dev cluster
7) Delete rishonim_output_gold on local and download from dev cluster
8) Run project.yml to start fine tuning
9) copy ID of new model and paste it into LLM.run_on_validation_set.py
10) up skip by desired amount and run
11) export ner_he_gpt_copper using evaluation.py
12) review export and mark IDs in new docs to correct
"""
