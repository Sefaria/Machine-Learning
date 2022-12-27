"""
Functions for running prodigy server
Consider refactoring name to be better
"""

from typing import Callable, Iterator, List
import spacy
from sklearn.model_selection import train_test_split
from spacy.training import Example
from spacy.language import Language
from db_manager import MongoProdigyDBManager


def get_mongo_docs(min_training_text_len, unique_by_metadata=True, *db_manager_args) -> List[dict]:
    my_db = MongoProdigyDBManager(*db_manager_args)
    data = [d for d in my_db.output_collection.find({}) if len(d['text']) > min_training_text_len]
    # make data unique
    if unique_by_metadata:
        data = list({(tuple(sorted(d['meta'].items(), key=lambda x: x[0])), d['text']): d for d in data}.values())
    return data


def get_train_test_data(random_state: int, mongo_docs: List[dict], training_percentage: float):
    train_data, test_data = train_test_split(mongo_docs, random_state=random_state, train_size=training_percentage)
    return train_data, test_data


def get_corpus_data(db_host: str, db_port: int, input_collection: str, random_state: int, train_perc: float, corpus_type: str, min_len: int, unique_by_metadata=True):
    data = get_mongo_docs(min_len, unique_by_metadata, input_collection, db_host, db_port)
    print("Num examples", len(data))
    if random_state == -1:
        train_data, test_data = (data, []) if corpus_type == "train" else ([], data)
    else:
        train_data, test_data = get_train_test_data(random_state, data, train_perc)
    corpus_data = train_data if corpus_type == "train" else test_data
    return corpus_data

@spacy.registry.readers("mongo_reader")
def stream_data(*args, **kwargs) -> Callable[[Language], Iterator[Example]]:
    corpus_data = get_corpus_data(*args, **kwargs)

    def generate_stream(nlp):
        for raw_example in corpus_data:
            if raw_example['answer'] == 'reject': continue
            doc = nlp.make_doc(raw_example['text'])
            doc.user_data = raw_example['meta']
            doc.user_data.update({'answer': raw_example['answer'], '_id': str(raw_example['_id'])})
            entities = [(span['start'], span['end'], span['label']) for span in raw_example['spans']]
            example = Example.from_dict(doc, {"entities": entities})
            yield example

    return generate_stream
