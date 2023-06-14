from spacy.tokens import DocBin
import argparse
import json
from typing import List
from helper import create_nlp, get_mongo_docs_or_load_json
from training_utils import get_train_test_data
import os


def output_mongo_docs(mongo_docs: List[dict], lang: str, output_file: str) -> None:
    nlp = create_nlp(lang)
    # mostly copied from here https://spacy.io/usage/training#training-data
    doc_bin = DocBin()
    for mongo_doc in mongo_docs:
        doc = nlp(mongo_doc['text'])
        ents = []
        for raw_span in mongo_doc['spans']:
            span = doc.char_span(raw_span['start'], raw_span['end'], label=raw_span['label'])
            ents.append(span)
        print("debug print: ents = ")
        print(ents)
        doc.ents = ents
        doc_bin.add(doc)
    doc_bin.to_disk(output_file)

def main(lang: str, input: str, output_file_prefix: str, min_training_text_len: int, training_percentage: float, random_state: int, input_type: str = "mongo",
         db_host: str = "localhost", db_port: int = 27017, user: str = "", password: str = "", replicaset: str = ""):
    data = get_mongo_docs_or_load_json(input, input_type, min_training_text_len, True, db_host, db_port, password, replicaset)
    train_data, test_data = get_train_test_data(random_state, data, training_percentage)
    output_mongo_docs(train_data, lang, f"{output_file_prefix}_train.spacy")
    output_mongo_docs(test_data, lang, f"{output_file_prefix}_test.spacy")

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('lang')
    parser.add_argument('input')
    parser.add_argument('output_file_prefix')
    parser.add_argument('min_training_text_len', type=int)
    parser.add_argument('training_percentage', type=float)
    parser.add_argument('random_state', type=int)
    parser.add_argument('-i', '--input-type', dest='input_type')
    parser.add_argument('-m', '--db-host', dest='db_host')
    parser.add_argument('-p', '--db-port', dest='db_port', type=int)
    parser.add_argument("-u", "--user", dest="user", const="", nargs="?")
    parser.add_argument("-r", "--replicaset", dest="replicaset", const="", nargs="?")
    return parser

if __name__ == '__main__':
    parser = init_argparse()
    args = parser.parse_args()
    password = os.getenv('MONGO_PASSWORD')
    main(args.lang, args.input, args.output_file_prefix, args.min_training_text_len, args.training_percentage, args.random_state, args.input_type,
         args.db_host, args.db_port, args.user, password, args.replicaset)