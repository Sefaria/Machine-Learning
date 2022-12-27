from spacy.tokens import DocBin
import typer
from library_exporter import create_nlp
from db_manager import MongoProdigyDBManager


def main(lang: str, input_collection: str, output_file: str):
    input_db = MongoProdigyDBManager(input_collection)
    nlp = create_nlp(lang)
    cursor = input_db.output_collection.find({}, {"_id": False, "tokens": False})

    # mostly copied from here https://spacy.io/usage/training#training-data
    doc_bin = DocBin()
    for mongo_doc in cursor:
        doc = nlp(mongo_doc['text'])
        ents = []
        for raw_span in mongo_doc['spans']:
            span = doc.char_span(raw_span['start'], raw_span['end'], label=raw_span['label'])
            ents.append(span)
        doc.ents = ents
        doc_bin.add(doc)
    doc_bin.to_disk(output_file)

if __name__ == '__main__':
    typer.run(main)
