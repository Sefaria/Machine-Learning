"""
Functions for running prodigy server
Consider refactoring name to be better
"""

from typing import Callable, Iterator, List
import spacy
from spacy.training import Example
from spacy.language import Language
from util.training_utils import get_corpus_data


@spacy.registry.readers("mongo_reader")
def stream_data(*args, include_reject=False, **kwargs) -> Callable[[Language], Iterator[Example]]:
    corpus_data = get_corpus_data(*args, **kwargs)

    def generate_stream(nlp):
        for raw_example in corpus_data:
            answer = raw_example.get('answer', 'accept')
            if answer == 'reject' and not include_reject: continue
            doc = nlp.make_doc(raw_example['text'])
            doc.user_data = raw_example['meta']
            doc.user_data.update({'answer': answer, '_id': str(raw_example['_id'])})
            entities = [(span['start'], span['end'], span['label']) for span in raw_example['spans']]
            example = Example.from_dict(doc, {"entities": entities})
            yield example

    return generate_stream
