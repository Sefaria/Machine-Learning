from typing import List
import json
from util.spacy_registry import inner_punct_tokenizer_factory
from spacy.training import Example
from spacy.lang.en import English
from spacy.lang.he import Hebrew


def load_mongo_docs(min_training_text_len, unique_by_metadata=True, *db_manager_args) -> List[dict]:
    from db_manager import MongoProdigyDBManager
    print(db_manager_args)
    my_db = MongoProdigyDBManager(*db_manager_args)
    data = [d for d in my_db.output_collection.find({}) if len(d['text']) > min_training_text_len]
    # make data unique
    if unique_by_metadata:
        data = list({(tuple(sorted(d['meta'].items(), key=lambda x: x[0])), d['text']): d for d in data}.values())
    return data


def filter_rejected_docs(docs):
    return [doc for doc in docs if doc['answer'] == 'accept']


def generate_example_stream(nlp, docs):
    for raw_example in docs:
        answer = raw_example.get('answer', 'accept')
        doc = nlp.make_doc(raw_example['text'])
        doc.user_data = raw_example['meta']
        doc.user_data.update({'answer': answer, '_id': str(raw_example['_id'])})
        entities = [(span['start'], span['end'], span['label']) for span in raw_example['spans']]
        example = Example.from_dict(doc, {"entities": entities})
        yield example


def load_mongo_docs_or_json(input, input_type: str, min_training_text_len, unique_by_metadata=True, *db_manager_args):
    if input_type == "mongo":
        return load_mongo_docs(min_training_text_len, unique_by_metadata, input, *db_manager_args)
    elif input_type == "json":
        with open(input, "r") as fin:
            return json.load(fin)


def create_normalizer():
    from sefaria.helper.normalization import NormalizerByLang, NormalizerComposer
    base_normalizer_steps = ['unidecode', 'html', 'double-space']
    return NormalizerByLang({
        'en': NormalizerComposer(base_normalizer_steps),
        'he': NormalizerComposer(base_normalizer_steps + ['maqaf', 'cantillation']),
    })


def create_nlp(lang):
    """
    Create nlp object for tokenization
    :return:
    """
    nlp = Hebrew() if lang == 'he' else English()
    nlp.tokenizer = inner_punct_tokenizer_factory()(nlp)
    return nlp


def get_window_around_match(start, end, text, window=10):
    before_text = text[:start]
    before_window_words = list(filter(lambda x: len(x) > 0, before_text.split()))[-window:]
    before_window = " ".join(before_window_words)

    after_text = text[end:]
    after_window_words = list(filter(lambda x: len(x) > 0, after_text.split()))[:window]
    after_window = " ".join(after_window_words)

    return before_window, after_window
