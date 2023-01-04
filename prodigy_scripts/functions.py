"""
Functions for running prodigy server
Consider refactoring name to be better
"""

from typing import Callable, Iterator, List
import spacy
from spacy.training import Example
from spacy.language import Language
from util.training_utils import get_mongo_docs, get_train_test_data, get_corpus_data


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
