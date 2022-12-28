from spacy.tokens import DocBin
import typer
import json
from typing import List
from library_exporter import create_nlp
from prodigy.functions import get_mongo_docs, get_train_test_data


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
        doc.ents = ents
        doc_bin.add(doc)
    doc_bin.to_disk(output_file)


def main(lang: str, input: str, output_file_prefix: str, min_training_text_len: int, training_percentage: float, random_state: int, db_host: str = "localhost", db_port: int = 27017, input_type: str = "mongo"):
    if input_type == "mongo":
        data = get_mongo_docs(min_training_text_len, True, input, db_host, db_port)
    elif input_type == "json":
        with open(input, "r") as fin:
            data = json.load(fin)
    train_data, test_data = get_train_test_data(random_state, data, training_percentage)
    output_mongo_docs(train_data, lang, f"{output_file_prefix}_train.spacy")
    output_mongo_docs(test_data, lang, f"{output_file_prefix}_test.spacy")


if __name__ == '__main__':
    typer.run(main)
