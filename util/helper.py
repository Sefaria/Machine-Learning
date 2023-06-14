from typing import List
import json
from util.spacy_registry import inner_punct_tokenizer_factory
from spacy.lang.en import English
from spacy.lang.he import Hebrew


def get_mongo_docs(min_training_text_len, unique_by_metadata=True, *db_manager_args) -> List[dict]:
    from db_manager import MongoProdigyDBManager
    print(db_manager_args)
    my_db = MongoProdigyDBManager(*db_manager_args)
    data = [d for d in my_db.output_collection.find({}) if len(d['text']) > min_training_text_len]
    # make data unique
    if unique_by_metadata:
        data = list({(tuple(sorted(d['meta'].items(), key=lambda x: x[0])), d['text']): d for d in data}.values())
    return data


def get_mongo_docs_or_load_json(input, input_type: str, min_training_text_len, unique_by_metadata=True, *db_manager_args):
    if input_type == "mongo":
        return get_mongo_docs(min_training_text_len, unique_by_metadata, input, *db_manager_args)
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
